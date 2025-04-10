from fastapi import APIRouter, HTTPException, Body
from datetime import datetime, timezone as tz
from src.models.schemas import DeleteIndexResponse, Content
from typing import List, Dict
from src.services.pinecone_service import PineconeService
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/indexes")
async def list_indexes():
    try:
        pc = PineconeService()
        indexes = await pc.list_all_indexes()
        return {
            "indexes": indexes,
            "count": len(indexes),
            "timestamp": datetime.now(tz=tz.utc)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/indexes/{index_name}")
async def delete_index(index_name: str):
    try:
        pc = PineconeService()
        if await pc.delete_index(index_name):
            return DeleteIndexResponse(
                message="Index deleted successfully",
                deleted_index=index_name,
                timestamp=datetime.now(tz=tz.utc)
            )
        raise HTTPException(
            status_code=404,
            detail=f"Index '{index_name}' not found"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indexes/create",status_code=200)
async def create_index(
    index_name: str = Body(..., description="The name of the index to create")
):
    try:
        pc = PineconeService()
        await pc.get_or_create_index(index_name)
        return {"message": f"Index '{index_name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/indexes/{index_name}/upsert",status_code=200)
async def upsert_index(index_name: str, documents: List[Content]):
    try:
        pc = PineconeService()
        await pc.upsert_documents(index_name, documents)
        return {"message": f"Successfully upserted {len(documents)} documents to index '{index_name}'"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/indexes/{index_name}/query",status_code=200)
async def query_index(index_name: str, query: str):
    try:
        pc = PineconeService()
        await pc.query_similar(index_name, query)
        return {"message": f"Index '{index_name}' queried successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

