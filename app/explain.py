THEME_LABELS = {
    "relaxing": "relaxing",
    "farming": "farming",
    "low_grind": "low grind",
    "punishing": "punishing difficulty",
    "horror": "horror",
    "exploration": "exploration",
    "story_rich": "a strong story",
    "atmospheric": "atmosphere",
}


def theme_label(name: str) -> str:
    return THEME_LABELS.get(name, name.replace("_", " "))


def citations_for(evidence: list[dict], theme_rows: list[dict], preferences: list[str]) -> list[dict]:
    by_id = {item["id"]: item for item in evidence}
    relevant = []
    for row in theme_rows:
        if preferences and row["name"] not in preferences:
            continue
        for evidence_id in row["evidence_ids"]:
            record = by_id.get(evidence_id)
            if record is None or record.get("off_topic"):
                continue
            relevant.append((evidence_id, row["name"], row["support"], record))

    grouped: dict[str, dict] = {}
    for evidence_id, theme_name, support, record in relevant:
        entry = grouped.setdefault(
            evidence_id,
            {
                "evidence_id": evidence_id,
                "verdict": record["verdict"],
                "excerpt": record["body"],
                "helpful": record["helpful"],
                "recent": record["recent"],
                "source_label": record["source_label"],
                "source_url": record.get("source_url"),
                "themes": [],
            },
        )
        entry["themes"].append({"name": theme_name, "support": support})
    ordered = list(grouped.values())
    ordered.sort(key=lambda item: item["evidence_id"])
    return ordered[:4]


def explain(game: dict, preferences: list[str], hard_filters: dict, states: dict[str, str]) -> str:
    title = game["title"]
    sentences = [f"{title} is included from the local fixture catalog."]
    if hard_filters:
        rendered = []
        for key, required in hard_filters.items():
            label = key.replace("_", " ")
            rendered.append(f"{label} {'required' if required else 'excluded'}")
        sentences.append("It still matches the current filters after a catalog recheck: " + ", ".join(rendered) + ".")
    supported = [theme_label(name) for name in preferences if states.get(name) == "supports"]
    mixed = [theme_label(name) for name in preferences if states.get(name) == "mixed"]
    contradicted = [theme_label(name) for name in preferences if states.get(name) == "contradicts"]
    sample_size = game["approval"]["sample_size"]
    if supported:
        sentences.append(
            f"The synthetic review sample ({sample_size} on-topic reviews) supports {', '.join(supported)}."
        )
    if mixed:
        sentences.append(f"The same sample is mixed on {', '.join(mixed)}.")
    if contradicted:
        sentences.append(f"The sample conflicts with {', '.join(contradicted)}.")
    if not supported and not mixed and not contradicted:
        sentences.append("None of the requested themes were observed in this game's sample.")
    raw = game["approval"]["raw"]
    sentences.append(
        f"Raw approval in the fixture is {raw:.0%}, before small samples are pulled toward the catalog average."
    )
    sentences.append("Review text is a synthetic fixture, not a Steam user review.")
    return " ".join(sentences)
