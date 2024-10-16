# app/graphql/schema.py
from graphene_sqlalchemy import SQLAlchemyObjectType
from app.models import User, Role, Post, Comment, Media, UserProfile  # Include new models

# GraphQL Schemas using Graphene

class UserModel(SQLAlchemyObjectType):
    class Meta:
        model = User
        exclude_fields = ('hashed_password',)  # Exclude sensitive fields

class RoleModel(SQLAlchemyObjectType):
    class Meta:
        model = Role

class UserProfileModel(SQLAlchemyObjectType):
    class Meta:
        model = UserProfile

class PostModel(SQLAlchemyObjectType):
    class Meta:
        model = Post
        exclude_fields = ('user_id',)  # Exclude sensitive fields

class CommentModel(SQLAlchemyObjectType):
    class Meta:
        model = Comment

class MediaModel(SQLAlchemyObjectType):
    class Meta:
        model = Media
