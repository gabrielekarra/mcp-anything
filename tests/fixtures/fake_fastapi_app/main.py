"""Fake FastAPI app for testing route extraction."""

from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel

app = FastAPI(title="User API")


class UserCreate(BaseModel):
    name: str
    email: str
    age: int = 25


class UserUpdate(BaseModel):
    name: str = None
    email: str = None


@app.get("/users")
async def list_users(
    skip: int = Query(0, description="Number of users to skip"),
    limit: int = Query(10, description="Max users to return"),
):
    """List all users with pagination."""
    return []


@app.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(..., description="The user ID"),
):
    """Get a specific user by ID."""
    return {"id": user_id}


@app.post("/users")
async def create_user(user: UserCreate):
    """Create a new user."""
    return {"id": 1, **user.dict()}


@app.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(..., description="The user ID"),
    user: UserUpdate = Body(...),
):
    """Update an existing user."""
    return {"id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user."""
    return {"deleted": True}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
