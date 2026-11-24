import os
import shutil
from pathlib import Path

from app.config import EMBEDDING_DIM, MODEL_FILE, MODEL_REPO, MODEL_REVISION


def host_snapshot() -> dict:
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, raw = line.split(":", 1)
        memory[key] = int(raw.strip().split()[0])
    disk = shutil.disk_usage("/")
    load = os.getloadavg()
    return {
        "mem_total_mb": round(memory.get("MemTotal", 0) / 1024),
        "mem_available_mb": round(memory.get("MemAvailable", 0) / 1024),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "loadavg": [round(value, 2) for value in load],
    }


def model_descriptor() -> dict:
    return {
        "repo": MODEL_REPO,
        "revision": MODEL_REVISION,
        "file": MODEL_FILE,
        "dimensions": EMBEDDING_DIM,
        "prefixes": {"document": "search_document: ", "query": "search_query: "},
    }
