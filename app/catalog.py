from app.db import jsonb, transaction
from app.seed import build_profile, load_games


def _publisher_id(conn, name: str) -> int:
    row = conn.execute(
        """
        INSERT INTO publishers (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    ).fetchone()
    return row["id"]


def _tag_id(conn, name: str) -> int:
    row = conn.execute(
        """
        INSERT INTO tags (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    ).fetchone()
    return row["id"]


def _theme_id(conn, name: str) -> int:
    row = conn.execute(
        """
        INSERT INTO themes (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    ).fetchone()
    return row["id"]


def _enqueue(conn, app_id: int, op: str, profile_version: int) -> None:
    conn.execute(
        """
        INSERT INTO index_jobs (app_id, op, profile_version, status)
        VALUES (%s, %s, %s, 'pending')
        """,
        (app_id, op, profile_version),
    )


def upsert_game(conn, game: dict) -> int:
    current = conn.execute(
        "SELECT profile_version FROM games WHERE app_id = %s",
        (game["app_id"],),
    ).fetchone()
    version = 1 if current is None else current["profile_version"] + 1
    profile = game.get("profile_text") or build_profile(game)
    conn.execute(
        """
        INSERT INTO games (
            app_id, title, summary, profile_text, profile_version, features,
            language, source_url, fetched_at, verification, provenance
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (app_id) DO UPDATE SET
            title = EXCLUDED.title,
            summary = EXCLUDED.summary,
            profile_text = EXCLUDED.profile_text,
            profile_version = EXCLUDED.profile_version,
            features = EXCLUDED.features,
            language = EXCLUDED.language,
            source_url = EXCLUDED.source_url,
            fetched_at = EXCLUDED.fetched_at,
            verification = EXCLUDED.verification,
            provenance = EXCLUDED.provenance
        """,
        (
            game["app_id"],
            game["title"],
            game["summary"],
            profile,
            version,
            jsonb(game["features"]),
            game["language"],
            game["source_url"],
            game["fetched_at"],
            game["verification"],
            game["provenance"],
        ),
    )
    conn.execute("DELETE FROM game_publishers WHERE app_id = %s", (game["app_id"],))
    conn.execute("DELETE FROM game_tags WHERE app_id = %s", (game["app_id"],))
    conn.execute("DELETE FROM game_themes WHERE app_id = %s", (game["app_id"],))
    conn.execute("DELETE FROM evidence WHERE app_id = %s", (game["app_id"],))
    publisher_id = _publisher_id(conn, game["publisher"])
    conn.execute(
        """
        INSERT INTO game_publishers (app_id, publisher_id, source_url, fetched_at, verification)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (game["app_id"], publisher_id, game["source_url"], game["fetched_at"], game["verification"]),
    )
    for tag in game["tags"]:
        conn.execute(
            """
            INSERT INTO game_tags (app_id, tag_id, source_url, fetched_at, verification)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (game["app_id"], _tag_id(conn, tag), game["source_url"], game["fetched_at"], game["verification"]),
        )
    sample_size = sum(1 for review in game["reviews"] if not review["off_topic"])
    for review in game["reviews"]:
        conn.execute(
            """
            INSERT INTO evidence (
                id, app_id, verdict, body, helpful, recent, off_topic,
                language, source_label, source_url, fetched_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                review["id"],
                game["app_id"],
                review["verdict"],
                review["body"],
                review["helpful"],
                review["recent"],
                review["off_topic"],
                game["language"],
                review["source_label"],
                None,
                game["fetched_at"],
            ),
        )
    for theme in game["themes"]:
        conn.execute(
            """
            INSERT INTO game_themes (
                app_id, theme_id, support, evidence_ids, sample_size,
                language, fetched_at, verification
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                game["app_id"],
                _theme_id(conn, theme["name"]),
                theme["support"],
                theme["evidence_ids"],
                sample_size,
                game["language"],
                game["fetched_at"],
                game["verification"],
            ),
        )
    _enqueue(conn, game["app_id"], "upsert", version)
    return version


def refresh_catalog() -> int:
    games = load_games()
    for game in games:
        with transaction() as conn:
            upsert_game(conn, game)
    return len(games)


def update_game_facts(app_id: int, tags: list[str] | None = None, features: dict | None = None) -> dict:
    with transaction() as conn:
        game = _load_games(conn, [app_id]).get(app_id)
        if game is None:
            raise KeyError(app_id)
        if tags is not None:
            game["tags"] = tags
        if features is not None:
            merged = dict(game["features"])
            merged.update(features)
            game["features"] = merged
        game["profile_text"] = build_profile(game)
        version = upsert_game(conn, game)
        game["profile_version"] = version
        return game


def delete_game(app_id: int) -> None:
    with transaction() as conn:
        deleted = conn.execute("DELETE FROM games WHERE app_id = %s RETURNING app_id", (app_id,)).fetchone()
        if deleted is None:
            raise KeyError(app_id)
        _enqueue(conn, app_id, "delete", 0)


def enqueue_rebuild() -> int:
    with transaction() as conn:
        rows = conn.execute("SELECT app_id, profile_version FROM games ORDER BY app_id").fetchall()
        for row in rows:
            _enqueue(conn, row["app_id"], "upsert", row["profile_version"])
        return len(rows)


def game_count() -> int:
    with transaction() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"]


def publisher_names() -> list[str]:
    with transaction() as conn:
        rows = conn.execute("SELECT name FROM publishers ORDER BY name").fetchall()
    return [row["name"] for row in rows]


def _load_games(conn, app_ids: list[int]) -> dict[int, dict]:
    if not app_ids:
        return {}
    rows = conn.execute(
        """
        SELECT
            g.app_id, g.title, g.summary, g.profile_text, g.profile_version,
            g.features, g.language, g.source_url, g.fetched_at, g.verification, g.provenance,
            COALESCE((
                SELECT json_agg(t.name ORDER BY t.name)
                FROM game_tags gt
                JOIN tags t ON t.id = gt.tag_id
                WHERE gt.app_id = g.app_id
            ), '[]'::json) AS tags,
            COALESCE((
                SELECT json_agg(p.name ORDER BY p.name)
                FROM game_publishers gp
                JOIN publishers p ON p.id = gp.publisher_id
                WHERE gp.app_id = g.app_id
            ), '[]'::json) AS publishers,
            COALESCE((
                SELECT json_agg(p.id ORDER BY p.id)
                FROM game_publishers gp
                JOIN publishers p ON p.id = gp.publisher_id
                WHERE gp.app_id = g.app_id
            ), '[]'::json) AS publisher_ids,
            COALESCE((
                SELECT json_agg(
                    json_build_object(
                        'name', th.name,
                        'support', gt.support,
                        'evidence_ids', gt.evidence_ids
                    )
                    ORDER BY th.name, gt.support
                )
                FROM game_themes gt
                JOIN themes th ON th.id = gt.theme_id
                WHERE gt.app_id = g.app_id
            ), '[]'::json) AS themes,
            COALESCE((
                SELECT json_agg(
                    json_build_object(
                        'id', e.id,
                        'verdict', e.verdict,
                        'body', e.body,
                        'helpful', e.helpful,
                        'recent', e.recent,
                        'off_topic', e.off_topic,
                        'source_label', e.source_label,
                        'source_url', e.source_url
                    )
                    ORDER BY e.id
                )
                FROM evidence e
                WHERE e.app_id = g.app_id
            ), '[]'::json) AS evidence
        FROM games g
        WHERE g.app_id = ANY(%s)
        """,
        (app_ids,),
    ).fetchall()
    loaded = {}
    for row in rows:
        game = dict(row)
        game["tags"] = list(game["tags"] or [])
        game["publishers"] = list(game["publishers"] or [])
        game["publisher_ids"] = [int(item) for item in (game["publisher_ids"] or [])]
        game["themes"] = list(game["themes"] or [])
        for theme in game["themes"]:
            theme["evidence_ids"] = list(theme["evidence_ids"])
        game["evidence"] = list(game["evidence"] or [])
        game["features"] = dict(game["features"] or {})
        game["publisher"] = game["publishers"][0] if game["publishers"] else ""
        game["reviews"] = game["evidence"]
        loaded[game["app_id"]] = game
    return loaded


def load_games_by_id(app_ids: list[int]) -> dict[int, dict]:
    with transaction() as conn:
        return _load_games(conn, app_ids)


def load_game_for_index(app_id: int) -> dict | None:
    games = load_games_by_id([app_id])
    return games.get(app_id)


def coverage() -> dict:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT
                g.app_id,
                g.title,
                (SELECT COUNT(*) FROM game_tags gt WHERE gt.app_id = g.app_id) AS tags,
                (SELECT COUNT(*) FROM game_publishers gp WHERE gp.app_id = g.app_id) AS publishers,
                (SELECT COUNT(*) FROM evidence e WHERE e.app_id = g.app_id AND NOT e.off_topic) AS evidence,
                (SELECT COUNT(*) FROM game_themes gt WHERE gt.app_id = g.app_id) AS themes,
                (g.source_url <> '' AND g.language <> '' AND g.verification IN ('verified', 'inferred')) AS identity
            FROM games g
            ORDER BY g.app_id
            """
        ).fetchall()
    missing = {"tags": [], "publishers": [], "evidence": [], "themes": [], "identity": []}
    for row in rows:
        for field in missing:
            if not row[field]:
                missing[field].append(row["app_id"])
    return {"games": len(rows), "missing": missing}


def catalog_average_approval() -> float:
    per_game = conn_average_by_game()
    if not per_game:
        return 0.5
    return sum(per_game) / len(per_game)


def conn_average_by_game() -> list[float]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT
                SUM(CASE WHEN verdict = 'positive' AND NOT off_topic THEN 1 ELSE 0 END)::float
                    / NULLIF(SUM(CASE WHEN NOT off_topic THEN 1 ELSE 0 END), 0) AS ratio
            FROM evidence
            GROUP BY app_id
            """
        ).fetchall()
    return [row["ratio"] for row in rows if row["ratio"] is not None]
