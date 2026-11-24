from app.config import (
    APPROVAL_PRIOR,
    WEIGHT_APPROVAL,
    WEIGHT_FEATURES,
    WEIGHT_HYBRID,
    WEIGHT_THEMES,
)

PREF_TAGS = {
    "relaxing": {"relaxing", "cozy"},
    "farming": {"farming sim", "farming"},
    "horror": {"horror"},
    "exploration": {"exploration"},
    "story_rich": {"story rich", "narrative"},
    "atmospheric": {"atmospheric"},
    "punishing": {"difficult", "souls-like"},
}


def passes_hard_filters(features: dict, hard_filters: dict) -> bool:
    for key, required in hard_filters.items():
        if bool(features.get(key)) != bool(required):
            return False
    return True


def approval_counts(evidence: list[dict]) -> tuple[int, int]:
    counted = [item for item in evidence if not item.get("off_topic")]
    positives = sum(1 for item in counted if item.get("verdict") == "positive")
    return positives, len(counted)


def adjusted_approval(positives: int, sample_size: int, catalog_average: float, prior: int = APPROVAL_PRIOR) -> float:
    if sample_size < 0 or positives < 0 or positives > sample_size:
        raise ValueError("approval counts are inconsistent")
    return (positives + prior * catalog_average) / (sample_size + prior)


def theme_states(theme_rows: list[dict]) -> dict[str, str]:
    grouped: dict[str, set[str]] = {}
    for row in theme_rows:
        grouped.setdefault(row["name"], set()).add(row["support"])
    states = {}
    for name, supports in grouped.items():
        if supports == {"supports", "contradicts"}:
            states[name] = "mixed"
        elif "supports" in supports:
            states[name] = "supports"
        elif "contradicts" in supports:
            states[name] = "contradicts"
    return states


def theme_fit(preferences: list[str], states: dict[str, str]) -> float:
    if not preferences:
        return 0.5
    total = 0.0
    for name in preferences:
        state = states.get(name)
        if state == "supports":
            total += 1.0
        elif state == "contradicts":
            total -= 1.0
        elif state == "mixed":
            total += 0.25
    return (total / len(preferences) + 1.0) / 2.0


def feature_fit(preferences: list[str], tags: list[str], publishers: list[str], requested_publishers: list[str]) -> float:
    scores = []
    tagset = {tag.lower() for tag in tags}
    for preference in preferences:
        expected = PREF_TAGS.get(preference)
        if not expected:
            continue
        scores.append(1.0 if tagset & expected else 0.0)
    if requested_publishers:
        owned = {name.lower() for name in publishers}
        wanted = {name.lower() for name in requested_publishers}
        scores.append(1.0 if owned & wanted else 0.0)
    if not scores:
        return 0.5
    return sum(scores) / len(scores)


def normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high == low:
        return [1.0 for _ in values]
    span = high - low
    return [(value - low) / span for value in values]


def rank_candidates(candidates: list[dict]) -> list[dict]:
    """Rank eligible games. Each candidate needs hybrid, feature_fit, theme_fit, and adjusted_approval."""
    hybrid_norm = normalize_scores([item["hybrid"] for item in candidates])
    ranked = []
    for item, hybrid in zip(candidates, hybrid_norm):
        score = (
            WEIGHT_HYBRID * hybrid
            + WEIGHT_FEATURES * item["feature_fit"]
            + WEIGHT_THEMES * item["theme_fit"]
            + WEIGHT_APPROVAL * item["adjusted_approval"]
        )
        ranked.append({
            **item,
            "hybrid_normalized": hybrid,
            "score": score,
        })
    ranked.sort(key=lambda item: (-item["score"], item["title"].lower(), item["app_id"]))
    return ranked
