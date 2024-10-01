# GraphQL Queries
import graphene
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.graphql.schemas import UserModel, RoleModel
import app.models as models

class Query(graphene.ObjectType):
    all_users = graphene.List(UserModel)
    user_by_id = graphene.Field(UserModel, user_id=graphene.Int(required=True))

    all_roles = graphene.List(RoleModel)
    role_by_id = graphene.Field(RoleModel, role_id=graphene.Int(required=True))

    def resolve_all_users(self, info):
        db: Session = info.context["db"]
        return db.query(models.User).all()

    def resolve_user_by_id(self, info, user_id):
        db: Session = info.context["db"]
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def resolve_all_roles(self, info):
        db: Session = info.context["db"]
        return db.query(models.Role).all()

    def resolve_role_by_id(self, info, role_id):
        db: Session = info.context["db"]
        role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role