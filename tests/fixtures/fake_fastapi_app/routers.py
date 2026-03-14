"""Fake FastAPI router for testing APIRouter extraction."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/items")
async def list_items(
    category: str = Query(None, description="Filter by category"),
):
    """List items, optionally filtered by category."""
    return []


@router.post("/items")
async def create_item(name: str, price: float):
    """Create a new item."""
    return {"name": name, "price": price}
