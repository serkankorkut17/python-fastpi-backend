# GraphQL Queries
import graphene
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.graphql.schemas import UserModel, RoleModel
import app.models as models
import app.crud as crud

class Query(graphene.ObjectType):
    all_users = graphene.List(UserModel)
    user_by_id = graphene.Field(UserModel, user_id=graphene.Int(required=True))

    all_roles = graphene.List(RoleModel)
    role_by_id = graphene.Field(RoleModel, role_id=graphene.Int(required=True))

    def resolve_all_users(self, info):
        db: Session = info.context["db"]
        return crud.find_all_users(db)

    def resolve_user_by_id(self, info, user_id):
        db: Session = info.context["db"]
        user = crud.find_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def resolve_all_roles(self, info):
        db: Session = info.context["db"]
        return crud.find_all_roles(db)

    def resolve_role_by_id(self, info, role_id):
        db: Session = info.context["db"]
        role = crud.find_role_by_id(db, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role