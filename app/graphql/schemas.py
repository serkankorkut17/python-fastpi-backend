# app/graphql/schema.py
from graphene_sqlalchemy import SQLAlchemyObjectType
from app.models import User, Role, Post  # Use absolute imports

# GraphQL Schemas using Graphene
class UserModel(SQLAlchemyObjectType):
    class Meta:
        model = User
        # You can define additional configurations like excluding fields if necessary
        exclude_fields = ('hashed_password',)  # Exclude sensitive fields


class RoleModel(SQLAlchemyObjectType):
    class Meta:
        model = Role


class PostModel(SQLAlchemyObjectType):
    class Meta:
        model = Post
        exclude_fields = ('user_id',)  # Exclude sensitive fields
        