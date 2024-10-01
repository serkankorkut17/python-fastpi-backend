# This file contains Pydantic schemas for FastAPI validation
from pydantic import BaseModel
from typing import Optional


# Pydantic schemas (for FastAPI validation)
class UserSchema(BaseModel):
    username: str
    email: str
    role_id: int

    class Config:
        from_attributes = True  # To allow ORM objects to be converted to Pydantic models


class RoleSchema(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
