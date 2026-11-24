import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
MODEL_REPO = "nomic-ai/nomic-embed-text-v1.5"
MODEL_REVISION = "e9b6763023c676ca8431644204f50c2b100d9aab"
MODEL_FILE = "onnx/model_int8.onnx"
TOKENIZER_FILE = "tokenizer.json"
EMBEDDING_DIM = 768
MAX_TOKENS = 512
DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "

CANDIDATE_LIMIT = 50
EXPANDED_CANDIDATE_LIMIT = 150
MIN_ELIGIBLE = 8
RESULT_LIMIT = 10
APPROVAL_PRIOR = 8
MAX_JOB_ATTEMPTS = 5

WEIGHT_HYBRID = 0.55
WEIGHT_FEATURES = 0.20
WEIGHT_THEMES = 0.15
WEIGHT_APPROVAL = 0.10


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "postgresql:///steam_atlas")


def qdrant_url() -> str:
    return os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")


def collection_name() -> str:
    return os.environ.get("QDRANT_COLLECTION", "games")


def model_dir() -> Path:
    override = os.environ.get("MODEL_DIR")
    if override:
        return Path(override)
    return ROOT / ".cache" / "models" / "nomic-embed-text-v1.5"
