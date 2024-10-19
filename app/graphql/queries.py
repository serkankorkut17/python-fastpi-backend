# GraphQL Queries
import graphene
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.graphql.schemas import (
    UserModel,
    RoleModel,
    UserProfileModel,
    PostModel,
    CommentModel,
    MediaModel,
)
import app.models as models
import app.crud as crud


# Query class
class Query(graphene.ObjectType):
    all_users = graphene.List(UserModel)  # List of all users
    user_by_id = graphene.Field(
        UserModel, user_id=graphene.Int(required=True)
    )  # User by ID
    user_by_username = graphene.Field(
        UserModel, username=graphene.String(required=True)
    )  # User by username

    all_roles = graphene.List(RoleModel)  # List of all roles
    role_by_id = graphene.Field(
        RoleModel, role_id=graphene.Int(required=True)
    )  # Role by ID

    user_profile = graphene.Field(
        UserProfileModel, user_id=graphene.Int(required=True)
    )  # User profile by User ID

    post = graphene.Field(PostModel, post_id=graphene.Int(required=True))  # Post by ID

    # Resolver functions
    # All users
    def resolve_all_users(self, info):
        db: Session = info.context["db"]
        return crud.find_all_users(db)

    # User by ID
    def resolve_user_by_id(self, info, user_id):
        db: Session = info.context["db"]
        user = crud.find_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    # User by username
    def resolve_user_by_username(self, info, username):
        db: Session = info.context["db"]
        user = crud.find_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    # All roles
    def resolve_all_roles(self, info):
        db: Session = info.context["db"]
        return crud.find_all_roles(db)

    # Role by ID
    def resolve_role_by_id(self, info, role_id):
        db: Session = info.context["db"]
        role = crud.find_role_by_id(db, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    # User profile by User ID
    def resolve_user_profile(self, info, user_id):
        db: Session = info.context["db"]
        user_profile = crud.find_user_profile(db, user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User not found")
        return user_profile

    # Post by ID
    def resolve_post(self, info, post_id):
        db: Session = info.context["db"]
        post = crud.find_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
