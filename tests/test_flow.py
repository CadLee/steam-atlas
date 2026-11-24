import os

import httpx
import psycopg
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql:///steam_atlas_test")
os.environ.setdefault("QDRANT_COLLECTION", "games_test")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from app.catalog import coverage, delete_game, enqueue_rebuild, load_game_for_index, refresh_catalog, update_game_facts
from app.db import init_db
from app.qdrant_store import count_points, ensure_collection, get_point, ready, recreate_collection
from app.search_service import search
from app.worker import drain, reconcile


def _services_available() -> bool:
    if not ready():
        return False
    try:
        with psycopg.connect("postgresql:///postgres", connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _services_available(), reason="postgres or qdrant is not running")


@pytest.fixture(scope="module", autouse=True)
def fixture_catalog():
    admin = psycopg.connect("postgresql:///postgres", autocommit=True)
    admin.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'steam_atlas_test' AND pid <> pg_backend_pid()"
    )
    admin.execute("DROP DATABASE IF EXISTS steam_atlas_test")
    admin.execute("CREATE DATABASE steam_atlas_test")
    admin.close()
    init_db()
    recreate_collection()
    ensure_collection()
    refresh_catalog()
    drain()
    yield


def test_coverage_is_complete_and_search_stays_offline():
    report = coverage()
    assert report["games"] == 25
    assert report["missing"] == {"tags": [], "publishers": [], "evidence": [], "themes": [], "identity": []}
    assert count_points() == 25
    payload = search({"query": "a relaxing farming game with online co-op and very little grind"})
    assert payload["results"][0]["app_id"] == 413150
    assert payload["results"][0]["title"] == "Stardew Valley"
    assert all(item["features"]["online_coop"] for item in payload["results"])
    assert all(433340 != item["app_id"] for item in payload["results"])
    assert payload["excluded"]["failed_sql_recheck"] == 0
    stardew = payload["results"][0]
    assert any(theme["name"] == "low_grind" and theme["support"] == "contradicts" for theme in stardew["themes"])
    assert stardew["citations"]
    assert all(item["source_label"] == "synthetic_fixture" for item in stardew["citations"])
    assert "synthetic" in stardew["explanation"].lower()


def test_tag_change_delete_and_rebuild_round_trip():
    update_game_facts(413150, tags=["Farming Sim", "Relaxing", "Experimental"])
    drain()
    stored = load_game_for_index(413150)
    assert "Experimental" in stored["tags"]
    point = get_point(413150)
    assert point is not None
    assert "Experimental" in point["payload"]["tags"]

    delete_game(433340)
    drain()
    reconcile()
    assert load_game_for_index(433340) is None
    assert count_points() == 24

    refresh_catalog()
    enqueue_rebuild()
    drain()
    removed = reconcile()
    assert removed["removed"] == []
    assert count_points() == 25
    assert load_game_for_index(433340)["title"] == "Slime Rancher"


def test_warm_template_searches_meet_the_latency_target():
    queries = [
        "a relaxing farming game with online co-op and very little grind",
        "punishing action with no co-op",
        "atmospheric exploration",
        "online co-op factory",
    ]
    search(search_body(queries[0]))
    totals = []
    for index in range(40):
        payload = search({"query": queries[index % len(queries)]})
        assert payload["results"]
        assert payload["excluded"]["failed_sql_recheck"] == 0
        totals.append(payload["timings_ms"]["total"])
    totals.sort()
    p95 = totals[int(len(totals) * 0.95) - 1]
    assert p95 < 2000, totals


def search_body(query):
    return {"query": query}
