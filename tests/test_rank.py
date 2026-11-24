import pytest

from app.explain import citations_for, explain
from app.rank import (
    adjusted_approval,
    feature_fit,
    passes_hard_filters,
    rank_candidates,
    theme_fit,
    theme_states,
)
from app.worker import next_job_state


def test_hard_filter_requires_exact_feature():
    assert passes_hard_filters({"online_coop": True}, {"online_coop": True})
    assert not passes_hard_filters({"online_coop": False}, {"online_coop": True})
    assert passes_hard_filters({"online_coop": False}, {})


def test_small_sample_is_pulled_toward_the_catalog_average():
    shrunk = adjusted_approval(positives=1, sample_size=1, catalog_average=0.5, prior=8)
    assert shrunk == pytest.approx((1 + 4) / 9)


def test_mixed_theme_scores_between_support_and_conflict():
    states = theme_states([
        {"name": "low_grind", "support": "supports"},
        {"name": "low_grind", "support": "contradicts"},
        {"name": "farming", "support": "supports"},
    ])
    assert states["low_grind"] == "mixed"
    mixed = theme_fit(["farming", "low_grind"], states)
    pure = theme_fit(["farming", "low_grind"], {"farming": "supports", "low_grind": "supports"})
    assert mixed < pure


def test_feature_fit_uses_tags_and_publishers():
    score = feature_fit(
        ["farming", "relaxing", "low_grind"],
        ["Farming Sim", "Relaxing"],
        ["ConcernedApe"],
        [],
    )
    assert score == 1.0
    missed = feature_fit(["farming"], ["Action"], ["Valve"], ["ConcernedApe"])
    assert missed < 1.0


def test_theme_and_feature_signals_outrank_a_grindy_coop_game():
    ranked = rank_candidates([
        {
            "app_id": 892970,
            "title": "Valheim",
            "hybrid": 0.8,
            "feature_fit": 0.0,
            "theme_fit": 0.0,
            "adjusted_approval": 0.5,
        },
        {
            "app_id": 413150,
            "title": "Stardew Valley",
            "hybrid": 0.8,
            "feature_fit": 1.0,
            "theme_fit": 0.9,
            "adjusted_approval": 0.8,
        },
    ])
    assert [item["app_id"] for item in ranked] == [413150, 892970]


def test_citations_drop_unknown_ids_and_off_topic_rows():
    evidence = [
        {"id": "syn-1", "verdict": "positive", "body": "SYNTHETIC FIXTURE — ok", "helpful": True, "recent": True, "source_label": "synthetic_fixture", "off_topic": False},
        {"id": "syn-2", "verdict": "negative", "body": "SYNTHETIC FIXTURE — off", "helpful": False, "recent": False, "source_label": "synthetic_fixture", "off_topic": True},
    ]
    themes = [
        {"name": "farming", "support": "supports", "evidence_ids": ["syn-1", "missing"]},
        {"name": "low_grind", "support": "contradicts", "evidence_ids": ["syn-2"]},
    ]
    citations = citations_for(evidence, themes, ["farming", "low_grind"])
    assert [item["evidence_id"] for item in citations] == ["syn-1"]


def test_explanation_names_conflict_and_the_fixture():
    text = explain(
        {
            "title": "Stardew Valley",
            "approval": {"raw": 0.75, "sample_size": 4},
        },
        ["low_grind"],
        {"online_coop": True},
        {"low_grind": "mixed"},
    )
    assert "synthetic" in text.lower()
    assert "mixed" in text.lower()
    assert "online coop required" in text.lower()


def test_failed_jobs_retry_then_stop():
    assert next_job_state(0, True) == ("done", 0)
    assert next_job_state(2, False) == ("pending", 3)
    assert next_job_state(4, False) == ("failed", 5)
