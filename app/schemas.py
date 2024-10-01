from graphene_sqlalchemy import SQLAlchemyObjectType
from pydantic import BaseModel
from typing import Optional

from models import User, Role


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


# GraphQL Schemas using Graphene
class UserModel(SQLAlchemyObjectType):
    class Meta:
        model = User
        # You can define additional configurations like excluding fields if necessary
        exclude_fields = ('hashed_password',)  # Exclude sensitive fields


class RoleModel(SQLAlchemyObjectType):
    class Meta:
        model = Role
