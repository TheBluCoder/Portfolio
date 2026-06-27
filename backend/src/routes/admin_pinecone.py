from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from src.config.log_config import setup_logging
from src.config.settings import ADMIN_API_KEY, PORTFOLIO_CONTEXT_INDEX
from src.dependencies import get_pinecone_service
from src.services.pinecone_service import PineconeService

router = APIRouter()
logger = setup_logging(filename=__file__)

MANAGED_INDEXES = [PORTFOLIO_CONTEXT_INDEX]


class RecordUpsert(BaseModel):
    index_name: str
    namespace: str = ""
    text: str
    record_id: str | None = None


class RecordDelete(BaseModel):
    index_name: str
    namespace: str = ""
    ids: list[str]


class RecordSearch(BaseModel):
    index_name: str
    namespace: str = ""
    query: str
    top_k: int = 10


@router.get("/admin/pinecone/indexes")
async def list_indexes(
    x_admin_key: str = Header(default=""),
    pinecone_service: PineconeService = Depends(get_pinecone_service),
) -> dict:
    _require_admin(x_admin_key)
    result: dict[str, Any] = {}
    for index_name in MANAGED_INDEXES:
        try:
            namespaces = await pinecone_service.list_namespaces(index_name)
            result[index_name] = {"namespaces": namespaces}
        except Exception as e:
            logger.warning("Could not describe index '%s': %s", index_name, e)
            result[index_name] = {"namespaces": [], "error": str(e)}
    return result


@router.post("/admin/pinecone/search")
async def search_records(
    body: RecordSearch,
    x_admin_key: str = Header(default=""),
    pinecone_service: PineconeService = Depends(get_pinecone_service),
) -> dict:
    _require_admin(x_admin_key)
    if body.index_name not in MANAGED_INDEXES:
        raise HTTPException(status_code=400, detail=f"Index must be one of {MANAGED_INDEXES}")
    try:
        raw = await pinecone_service.query_similar(
            body.index_name,
            body.query,
            namespace=body.namespace,
            top_k=body.top_k,
            top_n=body.top_k,
        )
        return {"hits": _normalize_hits(raw)}
    except Exception as e:
        logger.error("Pinecone search error: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/admin/pinecone/records")
async def upsert_record(
    body: RecordUpsert,
    x_admin_key: str = Header(default=""),
    pinecone_service: PineconeService = Depends(get_pinecone_service),
) -> dict:
    _require_admin(x_admin_key)
    if body.index_name not in MANAGED_INDEXES:
        raise HTTPException(status_code=400, detail=f"Index must be one of {MANAGED_INDEXES}")
    try:
        rid = await pinecone_service.upsert_single_record(
            body.index_name, body.namespace, body.text, body.record_id
        )
        return {"id": rid, "status": "upserted"}
    except Exception as e:
        logger.error("Pinecone upsert error: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/admin/pinecone/records")
async def delete_records(
    body: RecordDelete,
    x_admin_key: str = Header(default=""),
    pinecone_service: PineconeService = Depends(get_pinecone_service),
) -> dict:
    _require_admin(x_admin_key)
    if body.index_name not in MANAGED_INDEXES:
        raise HTTPException(status_code=400, detail=f"Index must be one of {MANAGED_INDEXES}")
    try:
        await pinecone_service.delete_records_by_ids(
            body.index_name, body.namespace, body.ids
        )
        return {"deleted": len(body.ids)}
    except Exception as e:
        logger.error("Pinecone delete error: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


# ── helpers ────────────────────────────────────────────────────────────────

def _normalize_hits(results: Any) -> list[dict]:
    """Flatten Pinecone search results to [{id, text, score}]."""
    candidates: list[Any] = []
    if isinstance(results, dict):
        result_obj = results.get("result")
        hits = (result_obj.get("hits") if isinstance(result_obj, dict) else None)
        candidates = hits or results.get("matches") or results.get("hits") or []
    elif hasattr(results, "result"):
        candidates = getattr(results.result, "hits", []) or []
    elif hasattr(results, "matches"):
        candidates = results.matches or []

    out = []
    for hit in candidates:
        if isinstance(hit, dict):
            rid = hit.get("id", "")
            fields = hit.get("fields", {}) or {}
            text = fields.get("text", "") if isinstance(fields, dict) else ""
            score = hit.get("score", 0)
        else:
            rid = getattr(hit, "id", "")
            fields = getattr(hit, "fields", None) or {}
            text = fields.get("text", "") if isinstance(fields, dict) else getattr(fields, "text", "")
            score = getattr(hit, "score", 0)
        out.append({"id": rid, "text": str(text), "score": float(score)})
    return out


def _require_admin(admin_key: str) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="Admin API key not configured")
    if admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
