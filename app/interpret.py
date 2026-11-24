import re
from dataclasses import dataclass, field


NEG_PHRASES = (
    "without online co-op",
    "without online coop",
    "no online co-op",
    "no online coop",
    "without co-op",
    "without coop",
    "no co-op",
    "no coop",
    "not co-op",
    "not coop",
    "single-player only",
    "single player only",
)
OPTIONAL_PHRASES = (
    "optional online co-op",
    "optional online coop",
    "optional co-op",
    "optional coop",
)
POS_PHRASES = (
    "online co-op",
    "online coop",
    "cooperative",
    "co-op",
    "coop",
)
PREF_PATTERNS = (
    ("relaxing", (r"\brelaxing\b", r"\bcozy\b", r"\bchill\b")),
    ("farming", (r"\bfarming\b", r"\bfarm sim\b")),
    ("low_grind", (r"\bvery little grind\b", r"\blittle grind\b", r"\blow grind\b", r"\bno grind\b", r"\bnot grindy\b")),
    ("punishing", (r"\bpunishing\b", r"\bvery hard\b", r"\bsouls-?like\b")),
    ("horror", (r"\bhorror\b", r"\bscary\b")),
    ("exploration", (r"\bexploration\b", r"\bexplore\b")),
    ("story_rich", (r"\bstory[- ]rich\b", r"\bstory driven\b", r"\bnarrative\b")),
    ("atmospheric", (r"\batmospheric\b",)),
)


@dataclass
class Interpretation:
    query: str
    mood_text: str
    hard_filters: dict = field(default_factory=dict)
    preferences: list = field(default_factory=list)
    publishers: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "query": self.query,
            "mood_text": self.mood_text,
            "hard_filters": self.hard_filters,
            "preferences": self.preferences,
            "publishers": self.publishers,
        }


def _phrase_match(text: str, phrase: str):
    return re.search(r"\b" + re.escape(phrase) + r"\b", text)


def _first_phrase(text: str, phrases: tuple[str, ...]):
    found = None
    for phrase in phrases:
        match = _phrase_match(text, phrase)
        if match is None:
            continue
        if found is None or match.start() < found[0].start() or (
            match.start() == found[0].start() and len(phrase) > len(found[1])
        ):
            found = (match, phrase)
    return found


def _strip_span(original: str, start: int, end: int) -> str:
    window = original[max(0, start - 6) : start].lower()
    if window.endswith(" with "):
        start -= 6
    return original[:start] + " " + original[end:]


def interpret(query: str, publishers: list[str] | None = None) -> Interpretation:
    original = " ".join(query.strip().split())
    lowered = original.lower()
    hard: dict[str, bool] = {}
    span = None

    negative = _first_phrase(lowered, NEG_PHRASES)
    optional = _first_phrase(lowered, OPTIONAL_PHRASES)
    positive = _first_phrase(lowered, POS_PHRASES)
    if negative is not None:
        hard["online_coop"] = False
        span = negative[0].span()
    elif optional is not None:
        span = optional[0].span()
    elif positive is not None:
        hard["online_coop"] = True
        span = positive[0].span()

    mood_source = _strip_span(original, span[0], span[1]) if span else original
    mood_text = " ".join(mood_source.split())

    preference_hits = []
    for name, patterns in PREF_PATTERNS:
        earliest = None
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match is not None and (earliest is None or match.start() < earliest):
                earliest = match.start()
        if earliest is not None:
            preference_hits.append((earliest, name))
    preference_hits.sort()
    preferences = [name for _, name in preference_hits]

    requested = []
    for name in publishers or []:
        if _phrase_match(lowered, name.lower()):
            requested.append(name)
    requested.sort(key=str.lower)

    return Interpretation(
        query=original,
        mood_text=mood_text or original,
        hard_filters=hard,
        preferences=preferences,
        publishers=requested,
    )
