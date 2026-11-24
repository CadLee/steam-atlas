import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.catalog import (
    coverage,
    delete_game,
    enqueue_rebuild,
    game_count,
    refresh_catalog,
    update_game_facts,
)
from app.config import ROOT
from app.db import init_db
from app.interpret import interpret
from app.qdrant_store import count_points, ensure_collection, ready
from app.search_service import search
from app.status import host_snapshot, model_descriptor
from app.worker import pending_count, reconcile, reset_running_jobs, run_loop

logger = logging.getLogger(__name__)
_stop = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_collection()
    if game_count() == 0:
        refresh_catalog()
    reset_running_jobs()
    _stop.clear()
    thread = threading.Thread(target=run_loop, args=(_stop,), name="index-worker", daemon=True)
    thread.start()
    yield
    _stop.set()
    thread.join(timeout=5)


app = FastAPI(title="Steam Game Discovery Copilot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/api/health")
def health():
    try:
        games = game_count()
        pending = pending_count()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"postgres unavailable: {exc}") from exc
    return {
        "postgres": True,
        "qdrant": ready(),
        "games": games,
        "indexed": count_points() if ready() else 0,
        "pending_jobs": pending,
        "model": model_descriptor(),
        "host": host_snapshot(),
    }


@app.get("/api/coverage")
def coverage_report():
    report = coverage()
    report["complete"] = report["games"] > 0 and not any(report["missing"].values())
    return report


@app.post("/api/interpret")
def interpret_query(payload: dict):
    query = str(payload.get("query") or "")
    from app.catalog import publisher_names

    return interpret(query, publisher_names()).as_dict()


@app.post("/api/search")
def search_games(payload: dict):
    if pending_count() > 0:
        raise HTTPException(status_code=409, detail="The index is still catching up to the catalog.")
    try:
        return search(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/catalog/refresh")
def refresh():
    count = refresh_catalog()
    return {"games": count}


@app.post("/api/catalog/rebuild")
def rebuild():
    enqueued = enqueue_rebuild()
    return {"enqueued": enqueued}


@app.post("/api/catalog/reconcile")
def reconcile_index():
    if pending_count() > 0:
        raise HTTPException(status_code=409, detail="Wait for index jobs to finish before reconciling.")
    return reconcile()


@app.patch("/api/catalog/games/{app_id}")
def patch_game(app_id: int, payload: dict):
    tags = payload.get("tags")
    features = payload.get("features")
    if tags is not None and not isinstance(tags, list):
        raise HTTPException(status_code=400, detail="tags must be a list")
    if features is not None and not isinstance(features, dict):
        raise HTTPException(status_code=400, detail="features must be an object")
    try:
        game = update_game_facts(app_id, tags=tags, features=features)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None
    return {"app_id": game["app_id"], "profile_version": game["profile_version"], "tags": game["tags"]}


@app.delete("/api/catalog/games/{app_id}")
def remove_game(app_id: int):
    try:
        delete_game(app_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None
    return {"deleted": app_id}
