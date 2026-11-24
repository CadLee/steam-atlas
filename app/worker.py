import logging
import threading
import time

from app.config import MAX_JOB_ATTEMPTS
from app.catalog import load_game_for_index
from app.db import transaction
from app.embeddings import embed_documents
from app.qdrant_store import delete_point, scroll_ids, upsert_point

logger = logging.getLogger(__name__)


def next_job_state(attempts: int, ok: bool, max_attempts: int = MAX_JOB_ATTEMPTS) -> tuple[str, int]:
    if ok:
        return "done", attempts
    updated = attempts + 1
    if updated >= max_attempts:
        return "failed", updated
    return "pending", updated


def reset_running_jobs() -> None:
    with transaction() as conn:
        conn.execute("UPDATE index_jobs SET status = 'pending' WHERE status = 'running'")


def pending_count() -> int:
    with transaction() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM index_jobs WHERE status IN ('pending', 'running')"
        ).fetchone()
    return row["n"]


def _claim():
    with transaction() as conn:
        row = conn.execute(
            """
            WITH claimed AS (
                SELECT id FROM index_jobs
                WHERE status = 'pending'
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE index_jobs AS job
            SET status = 'running'
            FROM claimed
            WHERE job.id = claimed.id
            RETURNING job.id, job.app_id, job.op, job.profile_version, job.attempts
            """
        ).fetchone()
    return row


def _finish(job_id: int, status: str, attempts: int, error: str | None) -> None:
    with transaction() as conn:
        conn.execute(
            """
            UPDATE index_jobs
            SET status = %s, attempts = %s, last_error = %s,
                acked_at = CASE WHEN %s = 'done' THEN now() ELSE acked_at END
            WHERE id = %s
            """,
            (status, attempts, error, status, job_id),
        )


def process_one() -> str:
    job = _claim()
    if job is None:
        return "idle"
    try:
        if job["op"] == "delete":
            delete_point(job["app_id"])
        else:
            game = load_game_for_index(job["app_id"])
            if game is None:
                delete_point(job["app_id"])
            elif game["profile_version"] != job["profile_version"]:
                pass
            else:
                vector = embed_documents([game["profile_text"]])[0]
                upsert_point(
                    game["app_id"],
                    vector,
                    {
                        "app_id": game["app_id"],
                        "title": game["title"],
                        "profile_text": game["profile_text"],
                        "profile_version": game["profile_version"],
                        "online_coop": bool(game["features"].get("online_coop")),
                        "tags": game["tags"],
                        "publisher_ids": game["publisher_ids"],
                    },
                )
        status, attempts = next_job_state(job["attempts"], True)
        _finish(job["id"], status, attempts, None)
        return "worked"
    except Exception as exc:
        logger.exception("index job %s failed", job["id"])
        status, attempts = next_job_state(job["attempts"], False)
        _finish(job["id"], status, attempts, str(exc)[:500])
        return "error"


def drain(timeout: float = 180.0) -> None:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        outcome = process_one()
        if outcome == "idle":
            if pending_count() == 0:
                return
        elif outcome == "error":
            time.sleep(0.2)
        failed = _failed_count()
        if failed:
            raise RuntimeError(f"{failed} index jobs failed")
    raise TimeoutError("index worker did not catch up")


def _failed_count() -> int:
    with transaction() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM index_jobs WHERE status = 'failed'").fetchone()["n"]


def reconcile() -> dict:
    from app.db import transaction as tx

    with tx() as conn:
        rows = conn.execute("SELECT app_id FROM games").fetchall()
    expected = {row["app_id"] for row in rows}
    extras = sorted(scroll_ids() - expected)
    for app_id in extras:
        delete_point(app_id)
    return {"removed": extras}


def run_loop(stop: threading.Event) -> None:
    reset_running_jobs()
    while not stop.is_set():
        outcome = process_one()
        if outcome == "idle":
            stop.wait(0.3)
        elif outcome == "error":
            stop.wait(1.0)
