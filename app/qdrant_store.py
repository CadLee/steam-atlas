import httpx

from app.config import EMBEDDING_DIM, collection_name, qdrant_url


class QdrantError(RuntimeError):
    pass


def _request(method: str, path: str, body: dict | None = None, timeout: float = 30.0) -> dict:
    url = qdrant_url() + path
    try:
        response = httpx.request(method, url, json=body, timeout=timeout)
    except httpx.HTTPError as exc:
        raise QdrantError(str(exc)) from exc
    if response.status_code >= 400:
        raise QdrantError(f"{response.status_code} {response.text[:500]}")
    if not response.content:
        return {}
    return response.json()


def ready() -> bool:
    try:
        response = httpx.get(qdrant_url() + "/readyz", timeout=2.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def ensure_collection() -> None:
    name = collection_name()
    existing = _request("GET", "/collections")
    names = {item["name"] for item in existing.get("result", {}).get("collections", [])}
    if name not in names:
        _request(
            "PUT",
            f"/collections/{name}",
            {
                "vectors": {
                    "dense": {"size": EMBEDDING_DIM, "distance": "Cosine"},
                }
            },
        )
    _request(
        "PUT",
        f"/collections/{name}/index?wait=true",
        {
            "field_name": "profile_text",
            "field_schema": {
                "type": "text",
                "tokenizer": "word",
                "lowercase": True,
                "scoring": True,
            },
        },
    )
    for field_name, schema in (
        ("online_coop", "bool"),
        ("tags", "keyword"),
        ("publisher_ids", "integer"),
        ("app_id", "integer"),
    ):
        _request(
            "PUT",
            f"/collections/{name}/index?wait=true",
            {"field_name": field_name, "field_schema": schema},
        )


def recreate_collection() -> None:
    name = collection_name()
    try:
        _request("DELETE", f"/collections/{name}")
    except QdrantError as exc:
        if "404" not in str(exc):
            raise
    ensure_collection()


def upsert_point(app_id: int, vector: list[float], payload: dict) -> None:
    _request(
        "PUT",
        f"/collections/{collection_name()}/points?wait=true",
        {"points": [{"id": app_id, "vector": {"dense": vector}, "payload": payload}]},
    )


def get_point(app_id: int) -> dict | None:
    result = _request(
        "POST",
        f"/collections/{collection_name()}/points",
        {"ids": [app_id], "with_payload": True, "with_vector": False},
    )
    points = result.get("result", [])
    if not points:
        return None
    return points[0]


def delete_point(app_id: int) -> None:
    _request(
        "POST",
        f"/collections/{collection_name()}/points/delete?wait=true",
        {"points": [app_id]},
    )


def query_hybrid(vector: list[float], text: str, hard_filters: dict, limit: int) -> list[dict]:
    query_filter = _filter(hard_filters)
    body = {
        "prefetch": [
            {
                "query": vector,
                "using": "dense",
                "limit": limit,
                "params": {"exact": True},
                "filter": query_filter,
            },
            {
                "query": {"text": text},
                "using": "profile_text",
                "limit": limit,
                "filter": query_filter,
            },
        ],
        "query": {"fusion": "rrf"},
        "limit": limit,
        "with_payload": True,
    }
    if query_filter is None:
        for prefetch in body["prefetch"]:
            prefetch.pop("filter")
    result = _request("POST", f"/collections/{collection_name()}/points/query", body)
    points = []
    for point in result.get("result", {}).get("points", []):
        points.append({
            "app_id": int(point["id"]),
            "hybrid": float(point.get("score") or 0.0),
            "payload": point.get("payload") or {},
        })
    return points


def _filter(hard_filters: dict) -> dict | None:
    must = []
    for key, required in hard_filters.items():
        must.append({"key": key, "match": {"value": bool(required)}})
    if not must:
        return None
    return {"must": must}


def count_points() -> int:
    try:
        result = _request("POST", f"/collections/{collection_name()}/points/count", {"exact": True})
    except QdrantError:
        return 0
    return int(result.get("result", {}).get("count") or 0)


def scroll_ids() -> set[int]:
    name = collection_name()
    found = set()
    offset = None
    while True:
        body = {"limit": 128, "with_payload": False, "with_vector": False}
        if offset is not None:
            body["offset"] = offset
        result = _request("POST", f"/collections/{name}/points/scroll", body)
        page = result.get("result", {})
        for point in page.get("points", []):
            found.add(int(point["id"]))
        offset = page.get("next_page_offset")
        if offset is None:
            return found
