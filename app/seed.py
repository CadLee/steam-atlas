"""Hand-authored 25-game access-test fixture.

Facts are inferred from public knowledge of these Steam app IDs. They are not a
live catalog pull. Every review is synthetic and is labelled in the text.
"""

from datetime import datetime, timezone

FETCHED_AT = datetime(2026, 11, 24, tzinfo=timezone.utc)
PROVENANCE = (
    "Hand-authored access-test fixture. Facts are inferred, not fetched from Steam. "
    "Review text is synthetic and is not a Steam user review."
)


def _review(number, verdict, body, helpful=True, recent=True, off_topic=False):
    return {
        "n": number,
        "verdict": verdict,
        "body": body,
        "helpful": helpful,
        "recent": recent,
        "off_topic": off_topic,
    }


def _game(
    app_id,
    title,
    publisher,
    summary,
    tags,
    online_coop,
    single_player,
    themes,
    reviews,
):
    return {
        "app_id": app_id,
        "title": title,
        "publisher": publisher,
        "summary": summary,
        "tags": tags,
        "features": {"online_coop": online_coop, "single_player": single_player},
        "themes": [{"name": name, "support": support, "review_numbers": numbers} for name, support, numbers in themes],
        "reviews": reviews,
    }


GAMES = [
    _game(
        413150, "Stardew Valley", "ConcernedApe",
        "A gentle farming life sim about restoring an overgrown homestead through crops, friendships, and small optional goals. Friends can join the same farm online.",
        ["Farming Sim", "Life Sim", "Relaxing", "Pixel Graphics", "Multiplayer"],
        True, True,
        [
            ("relaxing", "supports", [1, 4]),
            ("farming", "supports", [1]),
            ("low_grind", "supports", [2]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "Quiet days of farming and a shared farm online felt peaceful rather than hectic."),
            _review(2, "positive", "Most goals can wait, so the pace stays light if you ignore the bulletin board."),
            _review(3, "negative", "The community center and the mines turned into a checklist I kept grinding through."),
            _review(4, "positive", "It is still the cozy game I leave running on a rainy evening."),
        ],
    ),
    _game(
        433340, "Slime Rancher", "Monomi Park",
        "A bright single-player ranch about corralling slimes on a far planet and selling what they produce. The loop is playful and low pressure.",
        ["Relaxing", "Creature Collector", "Exploration", "Casual"],
        False, True,
        [
            ("relaxing", "supports", [1]),
            ("low_grind", "supports", [2]),
            ("exploration", "supports", [4]),
        ],
        [
            _review(1, "positive", "Vacuuming slimes and wandering the range is calm and colorful."),
            _review(2, "positive", "Progress comes in short bursts without a long obligation list."),
            _review(3, "negative", "A few slime types feel samey after the first range."),
            _review(4, "positive", "I kept finding new corners of the island to poke around."),
        ],
    ),
    _game(
        1868140, "DAVE THE DIVER", "MINTROCKET",
        "A single-player dive-and-restaurant story about catching fish by day and serving them at night. The tone is light, with a long story to nibble through.",
        ["Relaxing", "Adventure", "Casual", "Story Rich"],
        False, True,
        [
            ("relaxing", "supports", [1]),
            ("story_rich", "supports", [2]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "The dives are breezy and the sushi bar is a pleasant wind-down."),
            _review(2, "positive", "The characters and side plots kept me curious."),
            _review(3, "negative", "Upgrading gear meant repeating the same dive spots more than I wanted."),
            _review(4, "positive", "Short sessions still moved the restaurant forward."),
        ],
    ),
    _game(
        972660, "Spiritfarer: Farewell Edition", "Thunder Lotus",
        "A single-player journey about ferrying spirits and caring for them on a boat. It is tender, slow, and focused on relationships rather than combat.",
        ["Relaxing", "Story Rich", "Atmospheric", "Management"],
        False, True,
        [
            ("relaxing", "supports", [1]),
            ("story_rich", "supports", [2]),
            ("atmospheric", "supports", [4]),
            ("low_grind", "supports", [1]),
        ],
        [
            _review(1, "positive", "Boat chores stay gentle and the farewells are the point."),
            _review(2, "positive", "Each spirit's story is specific and worth seeing through."),
            _review(3, "negative", "Resource runs between islands slowed the middle of the game."),
            _review(4, "positive", "The music and the water make the whole trip feel hushed."),
        ],
    ),
    _game(
        1055540, "A Short Hike", "adamgryu",
        "A small single-player hike up a provincial park, with climbing, chatting, and no combat. It is short, kind, and easy to finish in an afternoon.",
        ["Relaxing", "Exploration", "Casual", "Short"],
        False, True,
        [
            ("relaxing", "supports", [1]),
            ("exploration", "supports", [2]),
            ("low_grind", "supports", [4]),
        ],
        [
            _review(1, "positive", "Wandering the island with no pressure was the whole pleasure."),
            _review(2, "positive", "Every side path had a small conversation or view."),
            _review(3, "negative", "It ends quickly if you only want the summit."),
            _review(4, "positive", "There is no gear treadmill, just golden feathers and a nice climb."),
        ],
    ),
    _game(
        892970, "Valheim", "Iron Gate AB",
        "A hard survival game of building, sailing, and boss fights in a Norse wilderness. Friends share a world online, and preparation is a long climb.",
        ["Survival", "Open World", "Multiplayer", "Crafting"],
        True, True,
        [
            ("exploration", "supports", [2]),
            ("relaxing", "contradicts", [1]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Nights and corpse runs kept the world tense, not restful."),
            _review(2, "positive", "Sailing to an unmarked shore is still a great moment."),
            _review(3, "negative", "Ore, food, and boss prep became a long material grind."),
            _review(4, "positive", "Building a hall with friends made the deaths easier to laugh off."),
        ],
    ),
    _game(
        548430, "Deep Rock Galactic", "Ghost Ship Games",
        "A cooperative shooter about dwarves mining alien caves and extracting under pressure. Missions are loud, social, and built for a team.",
        ["Co-op", "FPS", "Multiplayer", "Mining"],
        True, True,
        [
            ("relaxing", "contradicts", [1]),
            ("low_grind", "contradicts", [3]),
            ("exploration", "supports", [2]),
        ],
        [
            _review(1, "negative", "Swarms and extract timers are exciting, not calming."),
            _review(2, "positive", "Each cave generation still surprises the team."),
            _review(3, "negative", "Promotions ask you to repeat mission types for a long while."),
            _review(4, "positive", "Rock and stone with three friends is the reason to launch it."),
        ],
    ),
    _game(
        1966720, "Lethal Company", "Zeekerss",
        "A cooperative horror job about scavenging moons and meeting a quota. It is funny in a group and hostile when you are alone in the dark.",
        ["Horror", "Co-op", "Online Co-Op", "Comedy"],
        True, True,
        [
            ("horror", "supports", [1]),
            ("relaxing", "contradicts", [1]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "The facilities are scary on purpose and I never felt safe."),
            _review(2, "positive", "Voice chat with friends turns the panic into a story."),
            _review(3, "negative", "Hitting the quota means running the same moons again and again."),
            _review(4, "positive", "A single good scrap haul still feels like a heist."),
        ],
    ),
    _game(
        1426210, "It Takes Two", "Electronic Arts",
        "A story co-op adventure about a couple collaborating through fantastical levels. It is built to be played online with one other person.",
        ["Co-op", "Adventure", "Story Rich", "Platformer"],
        True, False,
        [
            ("story_rich", "supports", [1]),
            ("low_grind", "supports", [2]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "The relationship story gives every level a reason to exist."),
            _review(2, "positive", "Mechanics change often, so it never settles into a grind."),
            _review(3, "negative", "Some set pieces are stressful when your partner is stuck."),
            _review(4, "positive", "Playing the whole thing online with one friend worked cleanly."),
        ],
    ),
    _game(
        620, "Portal 2", "Valve",
        "A first-person puzzle game with a sharp single-player campaign and a separate co-op course. Test chambers stay clever rather than padded.",
        ["Puzzle", "Co-op", "Comedy", "First-Person"],
        True, True,
        [
            ("low_grind", "supports", [2]),
            ("story_rich", "supports", [1]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "The campaign's jokes and betrayal are still worth replaying."),
            _review(2, "positive", "Chambers are self-contained, with no upgrade treadmill."),
            _review(3, "negative", "A few co-op puzzles left us arguing instead of unwinding."),
            _review(4, "positive", "Online co-op with one friend is still the best way to see the extra course."),
        ],
    ),
    _game(
        1145360, "Hades", "Supergiant Games",
        "A single-player action roguelike about escaping the underworld, dying, and talking to the household afterward. Fights are fast and demanding.",
        ["Action", "Roguelike", "Story Rich", "Difficult"],
        False, True,
        [
            ("punishing", "supports", [1]),
            ("story_rich", "supports", [2]),
            ("relaxing", "contradicts", [1]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Early escapes are brutal until a build finally clicks."),
            _review(2, "positive", "Dialogue between runs gives the deaths a story."),
            _review(3, "negative", "I repeated the same regions many times to see one conversation."),
            _review(4, "positive", "Combat stays readable even when the room is full."),
        ],
    ),
    _game(
        367520, "Hollow Knight", "Team Cherry",
        "A single-player subterranean action adventure with precise combat and a quiet, ruined kingdom. Progress is exploratory and often unforgiving.",
        ["Metroidvania", "Difficult", "Atmospheric", "Exploration"],
        False, True,
        [
            ("punishing", "supports", [1]),
            ("atmospheric", "supports", [2]),
            ("exploration", "supports", [4]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Bosses took many attempts and the benches are far apart."),
            _review(2, "positive", "The caverns feel mournful and beautifully drawn."),
            _review(3, "negative", "Getting lost while low on health was stressful, not soothing."),
            _review(4, "positive", "Finding a new tram or area still felt like real exploration."),
        ],
    ),
    _game(
        504230, "Celeste", "Extremely OK Games",
        "A single-player platformer about climbing a mountain one screen at a time. The challenge is steep, with assist options if you want them.",
        ["Platformer", "Difficult", "Story Rich", "Pixel Graphics"],
        False, True,
        [
            ("punishing", "supports", [1]),
            ("story_rich", "supports", [2]),
            ("relaxing", "contradicts", [1]),
            ("low_grind", "supports", [3]),
        ],
        [
            _review(1, "negative", "Summit screens demanded precision I did not have at first."),
            _review(2, "positive", "The story about anxiety lands because the climb is hard."),
            _review(3, "positive", "Deaths are instant restarts, so it never becomes a gear grind."),
            _review(4, "positive", "Assist mode let a friend see the ending without the same wall."),
        ],
    ),
    _game(
        646570, "Slay the Spire", "Mega Crit",
        "A single-player deck-building climb through a spire of encounters. Runs are tactical, replayable, and indifferent to how much time you have already spent.",
        ["Roguelike", "Card Game", "Strategy", "Difficult"],
        False, True,
        [
            ("punishing", "supports", [1]),
            ("low_grind", "supports", [2]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Act 3 still ends runs that felt strong an hour earlier."),
            _review(2, "positive", "Each run stands alone, so there is no account-wide grind."),
            _review(3, "negative", "I stay tense choosing cards, which is not a wind-down game."),
            _review(4, "positive", "The defect and watcher keep the card puzzles fresh."),
        ],
    ),
    _game(
        2379780, "Balatro", "Playstack",
        "A single-player poker-themed roguelike about building absurd hands against escalating blinds. Rounds are short and easy to restart.",
        ["Roguelike", "Card Game", "Casual", "Strategy"],
        False, True,
        [
            ("low_grind", "supports", [2]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "One more blind is a dangerous sentence in the best way."),
            _review(2, "positive", "A run is over in a sitting, with no meta upgrade wall."),
            _review(3, "negative", "Chasing a high score kept me wired instead of relaxed."),
            _review(4, "positive", "This comment is about a different card game and does not belong here.", off_topic=True),
        ],
    ),
    _game(
        1794680, "Vampire Survivors", "poncle",
        "A single-player survivor game of automatic attacks, crowds, and short timed stages. The fun is escalation, and unlocking the full cast takes repetition.",
        ["Action", "Roguelite", "Pixel Graphics", "Casual"],
        False, True,
        [
            ("low_grind", "contradicts", [3]),
            ("relaxing", "contradicts", [1]),
        ],
        [
            _review(1, "negative", "The screen fills until the run is chaos, not a rest."),
            _review(2, "positive", "Thirty minutes is a complete session."),
            _review(3, "negative", "Collection unlocks asked me to replay stages with odd constraints."),
            _review(4, "positive", "A lucky build still feels ridiculous and joyful."),
        ],
    ),
    _game(
        632470, "Disco Elysium - The Final Cut", "ZA/UM",
        "A single-player role-playing investigation in a decaying district. Skills argue in your head, and there is almost no traditional combat.",
        ["RPG", "Story Rich", "Narrative", "Atmospheric"],
        False, True,
        [
            ("story_rich", "supports", [1]),
            ("atmospheric", "supports", [2]),
            ("low_grind", "supports", [4]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "The writing is the game, and the case kept me reading."),
            _review(2, "positive", "Martinaise feels damp, political, and specific."),
            _review(3, "negative", "Some skill checks and hangovers made me more anxious than soothed."),
            _review(4, "positive", "There is no combat treadmill or gear score to chase."),
        ],
    ),
    _game(
        753640, "Outer Wilds", "Mobius Digital",
        "A single-player mystery about a tiny solar system stuck in a time loop. You explore by flying a model ship and reading what other travelers left behind.",
        ["Exploration", "Mystery", "Atmospheric", "Story Rich"],
        False, True,
        [
            ("exploration", "supports", [1]),
            ("atmospheric", "supports", [2]),
            ("story_rich", "supports", [4]),
            ("low_grind", "supports", [3]),
        ],
        [
            _review(1, "positive", "Every planet hides knowledge rather than a collectible count."),
            _review(2, "positive", "The campfire music and the scale of the orbits stay with you."),
            _review(3, "positive", "You do not level up; you only understand more."),
            _review(4, "positive", "The ending depends on what you have read, not on a damage number."),
        ],
    ),
    _game(
        264710, "Subnautica", "Unknown Worlds Entertainment",
        "A single-player underwater survival story about a crashed ship and a deepening ocean. It is beautiful, tense, and full of material gathering.",
        ["Survival", "Exploration", "Atmospheric", "Open World"],
        False, True,
        [
            ("exploration", "supports", [1]),
            ("atmospheric", "supports", [2]),
            ("relaxing", "contradicts", [3]),
            ("low_grind", "contradicts", [4]),
        ],
        [
            _review(1, "positive", "Going deeper is the reward, biome by biome."),
            _review(2, "positive", "The water and the wrecks are haunting in a good way."),
            _review(3, "negative", "Leviathans and low oxygen kept me scared, not cozy."),
            _review(4, "negative", "Base building meant many trips for titanium and quartz."),
        ],
    ),
    _game(
        427520, "Factorio", "Wube Software",
        "A factory builder about automating a hostile planet, playable alone or in online co-op. The pleasure is optimization, and the to-do list never really ends.",
        ["Automation", "Strategy", "Multiplayer", "Base Building"],
        True, True,
        [
            ("low_grind", "contradicts", [1]),
            ("relaxing", "contradicts", [3]),
            ("exploration", "supports", [2]),
        ],
        [
            _review(1, "negative", "Scaling the factory is an endless production grind by design."),
            _review(2, "positive", "Clearing a new ore patch still feels like a small expedition."),
            _review(3, "negative", "Biters and brownouts made my sessions stressful."),
            _review(4, "positive", "Online co-op lets one person fix trains while another builds smelters."),
        ],
    ),
    _game(
        292030, "The Witcher 3: Wild Hunt — Remastered", "CD PROJEKT RED",
        "A single-player fantasy role-playing game about a monster hunter crossing a war-torn continent. Contracts, side stories, and a long main plot fill the map.",
        ["RPG", "Story Rich", "Open World", "Atmospheric"],
        False, True,
        [
            ("story_rich", "supports", [1]),
            ("atmospheric", "supports", [2]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "positive", "Side contracts often have a better story than the marker suggests."),
            _review(2, "positive", "The isles and villages feel lived in, even the ruined ones."),
            _review(3, "negative", "Question marks on the map became a completion grind."),
            _review(4, "positive", "Geralt's investigations still work as evening-long chapters."),
        ],
    ),
    _game(
        1245620, "ELDEN RING", "Bandai Namco Entertainment",
        "A single-player open-world action game of difficult fights, cryptic clues, and optional cooperation with strangers. Progress is demanding and rarely casual.",
        ["Action", "Difficult", "Open World", "Souls-like"],
        False, True,
        [
            ("punishing", "supports", [1]),
            ("exploration", "supports", [2]),
            ("relaxing", "contradicts", [1]),
            ("low_grind", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Bosses are punishing and I put the game down after several of them."),
            _review(2, "positive", "Riding into an unmapped region is the best kind of exploration."),
            _review(3, "negative", "Rune farming before a wall felt like the wrong kind of work."),
            _review(4, "positive", "Build variety kept a second character interesting."),
        ],
    ),
    _game(
        105600, "Terraria", "Re-Logic",
        "A sandbox of digging, building, and boss fights that supports online co-op. Worlds get large, and gear tiers ask for a lot of materials.",
        ["Sandbox", "Adventure", "Multiplayer", "Crafting"],
        True, True,
        [
            ("exploration", "supports", [2]),
            ("low_grind", "contradicts", [1]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Hardmode ores and boss summons turned into a material grind."),
            _review(2, "positive", "Digging a new cave system with friends is still exciting."),
            _review(3, "negative", "Boss nights are chaotic, not a calm building session."),
            _review(4, "positive", "Online co-op makes base building much faster."),
        ],
    ),
    _game(
        294100, "RimWorld", "Ludeon Studios",
        "A single-player colony story generator about settlers, disasters, and difficult choices. There is no built-in online co-op, and the colony's needs never stay solved.",
        ["Colony Sim", "Strategy", "Story Rich", "Management"],
        False, True,
        [
            ("story_rich", "supports", [1]),
            ("low_grind", "contradicts", [3]),
            ("relaxing", "contradicts", [2]),
        ],
        [
            _review(1, "positive", "The best stories come from a raid going wrong."),
            _review(2, "negative", "A blight or psychic wave can ruin a calm evening."),
            _review(3, "negative", "Keeping everyone fed and armed is a standing grind."),
            _review(4, "positive", "I still tell people about individual colonists years later."),
        ],
    ),
    _game(
        526870, "Satisfactory", "Coffee Stain Studios",
        "A first-person factory game on an alien planet, with online co-op for building enormous production lines. The landscape is pretty and the logistics are absorbing work.",
        ["Automation", "Base Building", "Multiplayer", "Open World"],
        True, True,
        [
            ("exploration", "supports", [2]),
            ("low_grind", "contradicts", [1]),
            ("relaxing", "contradicts", [3]),
        ],
        [
            _review(1, "negative", "Phase goals ask for huge part counts and a lot of rebuilding."),
            _review(2, "positive", "Hiking to a new resource node is genuinely scenic."),
            _review(3, "negative", "Power trips and spaghetti belts stressed me more than they soothed."),
            _review(4, "positive", "Online co-op lets friends own different parts of the factory."),
        ],
    ),
]


def evidence_id(app_id: int, number: int) -> str:
    return f"syn-{app_id}-{number}"


def iter_records():
    """Yield games with evidence ids resolved and profile text attached."""
    for game in GAMES:
        reviews = []
        for review in game["reviews"]:
            reviews.append({
                "id": evidence_id(game["app_id"], review["n"]),
                "verdict": review["verdict"],
                "body": f"SYNTHETIC FIXTURE — {review['body']}",
                "helpful": review["helpful"],
                "recent": review["recent"],
                "off_topic": review["off_topic"],
                "source_label": "synthetic_fixture",
            })
        known_ids = {item["id"] for item in reviews}
        themes = []
        for theme in game["themes"]:
            evidence_ids = [evidence_id(game["app_id"], number) for number in theme["review_numbers"]]
            missing = [item for item in evidence_ids if item not in known_ids]
            if missing:
                raise ValueError(f"{game['app_id']} theme cites missing evidence {missing}")
            themes.append({
                "name": theme["name"],
                "support": theme["support"],
                "evidence_ids": evidence_ids,
            })
        record = {
            "app_id": game["app_id"],
            "title": game["title"],
            "publisher": game["publisher"],
            "summary": game["summary"],
            "tags": list(game["tags"]),
            "features": dict(game["features"]),
            "themes": themes,
            "reviews": reviews,
            "language": "en",
            "source_url": f"https://store.steampowered.com/app/{game['app_id']}",
            "fetched_at": FETCHED_AT,
            "verification": "inferred",
            "provenance": PROVENANCE,
        }
        record["profile_text"] = build_profile(record)
        yield record


def build_profile(game: dict) -> str:
    supported = [theme["name"].replace("_", " ") for theme in game["themes"] if theme["support"] == "supports"]
    contradicted = [theme["name"].replace("_", " ") for theme in game["themes"] if theme["support"] == "contradicts"]
    lines = [
        game["title"],
        game["summary"],
        "Tags: " + ", ".join(game["tags"]),
        "Publisher: " + game["publisher"],
        "Review themes: " + ", ".join(supported) if supported else "Review themes: none recorded",
    ]
    if contradicted:
        lines.append("Conflicting themes: " + ", ".join(contradicted))
    if game["features"].get("online_coop"):
        lines.append("Supports online co-op.")
    else:
        lines.append("Does not support online co-op.")
    return "\n".join(lines)


def load_games() -> list[dict]:
    return list(iter_records())
