# app/graphql/__init__.py

from app.graphql.queries import Query
from app.graphql.mutations import Mutation
from app.graphql.schemas import UserModel, RoleModel
import graphene

# Define the main GraphQL schema
schema = graphene.Schema(query=Query, mutation=Mutation)

__all__ = ["schema", "UserModel", "RoleModel"]
