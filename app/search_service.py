import time

from app.config import (
    CANDIDATE_LIMIT,
    EXPANDED_CANDIDATE_LIMIT,
    MIN_ELIGIBLE,
    RESULT_LIMIT,
)
from app.catalog import catalog_average_approval, load_games_by_id, publisher_names
from app.embeddings import embed_query
from app.explain import citations_for, explain
from app.interpret import Interpretation, interpret
from app.qdrant_store import query_hybrid
from app.rank import (
    adjusted_approval,
    approval_counts,
    feature_fit,
    passes_hard_filters,
    rank_candidates,
    theme_fit,
    theme_states,
)


def resolve_interpretation(payload: dict) -> Interpretation:
    query = str(payload.get("query") or "").strip()
    if not query:
        raise ValueError("Enter a description of the game you want.")
    if payload.get("apply_interpretation", True):
        return interpret(query, publisher_names())
    hard = payload.get("hard_filters") or {}
    if not isinstance(hard, dict):
        raise ValueError("hard_filters must be an object")
    clean_hard = {}
    for key, value in hard.items():
        if key != "online_coop":
            raise ValueError(f"Unsupported filter: {key}")
        if value is not None:
            clean_hard[key] = bool(value)
    preferences = [str(item) for item in (payload.get("preferences") or [])]
    publishers = [str(item) for item in (payload.get("publishers") or [])]
    mood = str(payload.get("mood_text") or "").strip() or query
    return Interpretation(query, mood, clean_hard, preferences, publishers)


def _eligible(points: list[dict], games: dict[int, dict], hard_filters: dict) -> tuple[list[dict], dict]:
    excluded = {"failed_sql_recheck": 0, "missing_in_catalog": 0}
    kept = []
    for point in points:
        game = games.get(point["app_id"])
        if game is None:
            excluded["missing_in_catalog"] += 1
            continue
        if not passes_hard_filters(game["features"], hard_filters):
            excluded["failed_sql_recheck"] += 1
            continue
        kept.append({**point, "game": game})
    return kept, excluded


def _prepare(kept: list[dict], interpretation: Interpretation, average: float) -> list[dict]:
    prepared = []
    for item in kept:
        game = item["game"]
        states = theme_states(game["themes"])
        positives, sample_size = approval_counts(game["evidence"])
        raw = (positives / sample_size) if sample_size else average
        shrunk = adjusted_approval(positives, sample_size, average)
        prepared.append({
            "app_id": game["app_id"],
            "title": game["title"],
            "hybrid": item["hybrid"],
            "feature_fit": feature_fit(
                interpretation.preferences,
                game["tags"],
                game["publishers"],
                interpretation.publishers,
            ),
            "theme_fit": theme_fit(interpretation.preferences, states),
            "adjusted_approval": shrunk,
            "raw_approval": raw,
            "sample_size": sample_size,
            "states": states,
            "game": game,
        })
    return prepared


def _present(ranked: list[dict], interpretation: Interpretation) -> list[dict]:
    results = []
    for index, item in enumerate(ranked[:RESULT_LIMIT], start=1):
        game = item["game"]
        game_view = {
            **game,
            "approval": {"raw": item["raw_approval"], "sample_size": item["sample_size"]},
        }
        relevant_themes = [
            row for row in game["themes"]
            if not interpretation.preferences or row["name"] in interpretation.preferences
        ]
        results.append({
            "rank": index,
            "app_id": game["app_id"],
            "title": game["title"],
            "score": round(item["score"], 4),
            "breakdown": {
                "hybrid": round(item["hybrid_normalized"], 4),
                "features": round(item["feature_fit"], 4),
                "themes": round(item["theme_fit"], 4),
                "approval": round(item["adjusted_approval"], 4),
            },
            "qdrant_score": round(item["hybrid"], 4),
            "explanation": explain(game_view, interpretation.preferences, interpretation.hard_filters, item["states"]),
            "tags": game["tags"],
            "publishers": game["publishers"],
            "features": game["features"],
            "approval": {
                "raw": round(item["raw_approval"], 4),
                "adjusted": round(item["adjusted_approval"], 4),
                "sample_size": item["sample_size"],
            },
            "themes": relevant_themes,
            "citations": citations_for(game["evidence"], game["themes"], interpretation.preferences),
            "source_url": game["source_url"],
            "verification": game["verification"],
            "provenance": game["provenance"],
        })
    return results


def search(payload: dict) -> dict:
    started = time.perf_counter()
    interpretation = resolve_interpretation(payload)
    embed_started = time.perf_counter()
    vector = embed_query(interpretation.mood_text)
    embed_ms = (time.perf_counter() - embed_started) * 1000

    limit = CANDIDATE_LIMIT
    expanded = False
    excluded = {"failed_sql_recheck": 0, "missing_in_catalog": 0}
    retrieve_ms = 0.0
    kept = []
    candidate_ids: list[int] = []
    for _ in range(2):
        retrieve_started = time.perf_counter()
        points = query_hybrid(vector, interpretation.query, interpretation.hard_filters, limit)
        retrieve_ms += (time.perf_counter() - retrieve_started) * 1000
        candidate_ids = [point["app_id"] for point in points]
        games = load_games_by_id(candidate_ids)
        kept, excluded = _eligible(points, games, interpretation.hard_filters)
        if len(kept) >= MIN_ELIGIBLE or expanded or limit >= EXPANDED_CANDIDATE_LIMIT:
            break
        expanded = True
        limit = EXPANDED_CANDIDATE_LIMIT

    average = catalog_average_approval()
    ranked = rank_candidates(_prepare(kept, interpretation, average))
    results = _present(ranked, interpretation)
    for result in results:
        for citation in result["citations"]:
            if citation["source_label"] != "synthetic_fixture":
                raise RuntimeError("fixture search cited a non-synthetic review")
            if not citation["excerpt"].startswith("SYNTHETIC FIXTURE —"):
                raise RuntimeError("citation text is missing its fixture label")
    total_ms = (time.perf_counter() - started) * 1000
    return {
        "interpretation": interpretation.as_dict(),
        "results": results,
        "candidate_ids": candidate_ids,
        "excluded": excluded,
        "expanded": expanded,
        "timings_ms": {
            "embed": round(embed_ms, 1),
            "retrieve": round(retrieve_ms, 1),
            "total": round(total_ms, 1),
        },
    }
