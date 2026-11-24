from app.seed import load_games


def test_fixture_has_25_labelled_games():
    games = load_games()
    assert len(games) == 25
    assert len({game["app_id"] for game in games}) == 25
    assert any(game["features"]["online_coop"] for game in games)
    assert any(not game["features"]["online_coop"] for game in games)
    off_topic = 0
    saw_conflict = False
    for game in games:
        assert game["verification"] == "inferred"
        assert game["language"] == "en"
        assert game["source_url"].endswith(str(game["app_id"]))
        assert "author" not in game
        ids = set()
        for review in game["reviews"]:
            assert review["body"].startswith("SYNTHETIC FIXTURE —")
            assert review["source_label"] == "synthetic_fixture"
            assert "author" not in review
            ids.add(review["id"])
            off_topic += int(review["off_topic"])
        supports = {}
        for theme in game["themes"]:
            assert set(theme["evidence_ids"]) <= ids
            supports.setdefault(theme["name"], set()).add(theme["support"])
        if any(states == {"supports", "contradicts"} for states in supports.values()):
            saw_conflict = True
    assert off_topic >= 1
    assert saw_conflict
