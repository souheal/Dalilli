from fastapi import APIRouter, HTTPException
from typing import List

from app.models import CollectionCreate, CollectionResponse
from app.services.vector_store import vector_store

router = APIRouter()


@router.get("/", response_model=List[CollectionResponse])
async def list_collections():
    """List all collections"""
    return vector_store.list_collections()


@router.post("/", response_model=CollectionResponse)
async def create_collection(collection: CollectionCreate):
    """Create a new collection"""
    try:
        return vector_store.create_collection(collection.name, collection.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{name}", response_model=CollectionResponse)
async def get_collection(name: str):
    """Get collection details"""
    collection = vector_store.get_collection(name)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/{name}")
async def delete_collection(name: str):
    """Delete a collection"""
    if name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default collection")

    success = vector_store.delete_collection(name)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")

    return {"message": f"Collection '{name}' deleted successfully"}
