from app.interpret import interpret


def test_example_prompt_splits_required_coop_from_preferences():
    parsed = interpret(
        "a relaxing farming game with online co-op and very little grind",
        publishers=["ConcernedApe", "Valve"],
    )
    assert parsed.hard_filters == {"online_coop": True}
    assert parsed.preferences == ["relaxing", "farming", "low_grind"]
    assert "co-op" not in parsed.mood_text.lower()
    assert "farming" in parsed.mood_text.lower()
    assert "grind" in parsed.mood_text.lower()


def test_without_coop_is_a_hard_exclusion():
    parsed = interpret("a farming game without co-op")
    assert parsed.hard_filters == {"online_coop": False}
    assert parsed.preferences == ["farming"]


def test_optional_coop_is_not_a_hard_filter():
    parsed = interpret("a relaxing game with optional co-op")
    assert parsed.hard_filters == {}
    assert parsed.preferences == ["relaxing"]


def test_publisher_names_are_detected():
    parsed = interpret("something from Supergiant Games", publishers=["Supergiant Games", "Valve"])
    assert parsed.publishers == ["Supergiant Games"]
