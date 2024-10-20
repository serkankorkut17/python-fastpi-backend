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

    all_posts = graphene.List(PostModel)  # List of all postss
    post_by_id = graphene.Field(
        PostModel, post_id=graphene.Int(required=True)
    )  # Post by ID

    all_parent_comments_by_post_id = graphene.List(
        CommentModel, post_id=graphene.Int(required=True)
    )  # List of all parent comments by Post ID

    all_comments_by_post_id = graphene.List(
        CommentModel, post_id=graphene.Int(required=True)
    )  # List of all comments by Post ID
    comment_by_id = graphene.Field(
        CommentModel, comment_id=graphene.Int(required=True)
    )  # Comment by ID

    all_media_by_post_id = graphene.List(
        MediaModel, post_id=graphene.Int(required=True)
    )  # List of all media by Post ID
    media_by_id = graphene.Field(
        MediaModel, media_id=graphene.Int(required=True)
    )  # Media by ID

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

    # All posts
    def resolve_all_posts(self, info):
        db: Session = info.context["db"]
        return crud.find_all_posts(db)

    # Post by ID
    def resolve_post_by_id(self, info, post_id):
        db: Session = info.context["db"]
        post = crud.find_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post

    # All parent comments by Post ID
    def resolve_all_parent_comments_by_post_id(self, info, post_id):
        db: Session = info.context["db"]
        return crud.find_all_parent_comments_by_post_id(db, post_id)

    # All comments by Post ID
    def resolve_all_comments_by_post_id(self, info, post_id):
        db: Session = info.context["db"]
        return crud.find_all_comments_by_post_id(db, post_id)

    # Comment by ID
    def resolve_comment_by_id(self, info, comment_id):
        db: Session = info.context["db"]
        comment = crud.find_comment_by_id(db, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment

    # All media by Post ID
    def resolve_all_media_by_post_id(self, info, post_id):
        db: Session = info.context["db"]
        return crud.find_all_media_by_post_id(db, post_id)

    # Media by ID
    def resolve_media_by_id(self, info, media_id):
        db: Session = info.context["db"]
        media = crud.find_media_by_id(db, media_id)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        return media
