import shutil
from pathlib import Path

import numpy as np

from app.config import (
    DOCUMENT_PREFIX,
    EMBEDDING_DIM,
    MAX_TOKENS,
    MODEL_FILE,
    MODEL_REPO,
    MODEL_REVISION,
    QUERY_PREFIX,
    ROOT,
    TOKENIZER_FILE,
    model_dir,
)

_session = None
_tokenizer = None


def _ensure_artifacts() -> Path:
    directory = model_dir()
    onnx_path = directory / MODEL_FILE
    tokenizer_path = directory / TOKENIZER_FILE
    if not onnx_path.exists() or not tokenizer_path.exists():
        from huggingface_hub import hf_hub_download

        directory.mkdir(parents=True, exist_ok=True)
        for filename in (MODEL_FILE, TOKENIZER_FILE):
            hf_hub_download(
                repo_id=MODEL_REPO,
                filename=filename,
                revision=MODEL_REVISION,
                local_dir=directory,
            )
    notice_dir = ROOT / "third_party" / "nomic-embed-text-v1.5"
    for name in ("NOTICE", "LICENSE"):
        source = notice_dir / name
        target = directory / name
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)
    return directory


def _load():
    global _session, _tokenizer
    if _session is not None:
        return _session, _tokenizer
    import onnxruntime as ort
    from tokenizers import Tokenizer

    directory = _ensure_artifacts()
    tokenizer = Tokenizer.from_file(str(directory / TOKENIZER_FILE))
    tokenizer.enable_truncation(max_length=MAX_TOKENS)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(directory / MODEL_FILE),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    _session = session
    _tokenizer = tokenizer
    return session, tokenizer


def embed_texts(texts: list[str], prefix: str) -> list[list[float]]:
    if not texts:
        return []
    if prefix not in (DOCUMENT_PREFIX, QUERY_PREFIX):
        raise ValueError("prefix must be the pinned Nomic search prefix")
    session, tokenizer = _load()
    encoded = tokenizer.encode_batch([prefix + text for text in texts])
    width = max(len(item.ids) for item in encoded)
    input_ids = np.zeros((len(encoded), width), dtype=np.int64)
    attention_mask = np.zeros((len(encoded), width), dtype=np.int64)
    for row, item in enumerate(encoded):
        length = len(item.ids)
        input_ids[row, :length] = item.ids
        attention_mask[row, :length] = item.attention_mask
    token_type_ids = np.zeros_like(input_ids)
    hidden = session.run(
        None,
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        },
    )[0]
    mask = attention_mask.astype(np.float32)[:, :, None]
    pooled = (hidden * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
    pooled = pooled[:, :EMBEDDING_DIM]
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    pooled = pooled / np.clip(norms, 1e-9, None)
    return pooled.astype(np.float32).tolist()


def embed_documents(texts: list[str]) -> list[list[float]]:
    return embed_texts(texts, DOCUMENT_PREFIX)


def embed_query(text: str) -> list[float]:
    return embed_texts([text], QUERY_PREFIX)[0]
