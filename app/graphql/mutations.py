import graphene
from fastapi import HTTPException
from graphene_file_upload.scalars import Upload
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import jwt

from app.utils import (
    hash_password,
    authenticate_user,
    generate_access_token,
    check_auth,
)
import app.models as models
import app.crud as crud


# GraphQL Mutations
class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    access_token = graphene.String()

    @staticmethod
    def mutate(root, info, username, password):
        db: Session = info.context["db"]

        # Authenticate the user
        user = authenticate_user(db, username, password)

        # Generate access token
        access_token = generate_access_token(user)
        # !!!!!!! add last_login to user

        return Login(ok=True, access_token=access_token)


class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        role_id = graphene.Int(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user_id = graphene.Int()  # Return the created user's ID

    @staticmethod
    def mutate(root, info, username, email, role_id, password):
        db: Session = info.context["db"]

        # Validate role_id here, e.g., check if role exists (optional)
        role = crud.find_role_by_id(db, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        

        hashed_password = hash_password(password)

        # Create a new User instance
        db_user = models.User(
            username=username,
            email=email,
            role_id=role_id,
            hashed_password=hashed_password,
        )

        # Add user to the session and commit
        try:
            user_id = crud.save_to_db(db, db_user)
            ok = True
            return CreateUser(ok=ok, user_id=user_id)  # Return created user's ID
        except IntegrityError as e:
            db.rollback()  # Roll back the session on error
            raise HTTPException(
                status_code=400, detail=str(e.orig)
            )  # Provide a clear error message


class CreateRole(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()

    ok = graphene.Boolean()
    role_id = graphene.Int()

    @staticmethod
    def mutate(root, info, name, description=None):
        db: Session = info.context["db"]

        # Create new role instance
        db_role = models.Role(name=name, description=description)

        try:
            role_id = crud.save_to_db(db, db_role)
            return CreateRole(ok=True, role_id=role_id)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Error creating role: " + str(e.orig)
            )
        
class UpdateUserProfile(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        bio = graphene.String(required=False)
        profile_picture = Upload(required=False)  # Optional image upload

    ok = graphene.Boolean()
    user_id = graphene.Int()

    @staticmethod
    def mutate(root, info, first_name=None, last_name=None, bio=None, profile_photo=None):
        db: Session = info.context["db"]

        # Decode JWT from header
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")

        # Check if the user is authenticated
        token_data = check_auth(authorization)

        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])

        if not user:
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )

        # Update user profile
        db_profile = models.UserProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            bio=bio,
            profile_photo=profile_photo,
        )

        try:
            user_id = crud.save_to_db(db, db_profile)
            return UpdateUserProfile(ok=True, user_id=user_id)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Error updating user profile: " + str(e)
            )


class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)

    ok = graphene.Boolean()
    post_id = graphene.Int()

    @staticmethod
    def mutate(root, info, title, content):
        db: Session = info.context["db"]

        # Decode JWT from header
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")

        # Check if the user is authenticated
        token_data = check_auth(authorization)

        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])

        if not user:
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )

        # Create new post
        db_post = models.Post(title=title, content=content, user_id=user.id)

        try:
            post_id = crud.save_to_db(db, db_post)
            return CreatePost(ok=True, post_id=post_id)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Error creating post: " + str(e)
            )


# Mutation class to add all mutations
class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_role = CreateRole.Field()
    login = Login.Field()
    create_post = CreatePost.Field()
