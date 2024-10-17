import graphene
from fastapi import HTTPException, UploadFile
from graphene_file_upload.scalars import Upload
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import jwt
import os
import shutil
import json
from pathlib import Path

from app.utils import (
    hash_password,
    authenticate_user,
    generate_access_token,
    check_auth,
    handle_file_upload,
)
import app.models as models
import app.crud as crud
from app.utils import logger


# GraphQL Mutations
class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    access_token = graphene.String()

    @staticmethod
    async def mutate(root, info, username, password):
        db: Session = info.context["db"]

        # Authenticate the user
        user = authenticate_user(db, username, password)

        # Generate access token
        access_token = generate_access_token(user)

        # update last_login field
        user.last_login = datetime.utcnow()
        crud.save_to_db(db, user)

        # Log the successful login
        logger.info(f"[{Login.__name__}] User {username} logged in successfully")

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
            logger.error(f"[{CreateUser.__name__}] Role with ID {role_id} not found")
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
            db_user.profile = models.UserProfile(
                first_name=username, last_name=username
            )
            crud.save_to_db(db, db_user.profile)
            ok = True
            # Log the successful user creation
            logger.info(f"[{CreateUser.__name__}] User {username} created successfully")
            return CreateUser(ok=ok, user_id=user_id)  # Return created user's ID
        except IntegrityError as e:
            db.rollback()  # Roll back the session on error
            # Log the error
            logger.error(f"[{CreateUser.__name__}] Error creating user: {str(e.orig)}")
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
            logger.info(f"[{CreateRole.__name__}] Role {name} created successfully")
            return CreateRole(ok=True, role_id=role_id)
        except IntegrityError as e:
            db.rollback()
            logger.error(f"[{CreateRole.__name__}] Error creating role: {str(e.orig)}")
            raise HTTPException(
                status_code=400, detail="Error creating role: " + str(e.orig)
            )


class UpdateUserProfile(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        bio = graphene.String(required=False)
        profile_photo = Upload(required=False)  # Optional image upload

    ok = graphene.Boolean()
    user_id = graphene.Int()

    @staticmethod
    def mutate(
        root, info, first_name=None, last_name=None, bio=None, profile_photo=None
    ):
        db: Session = info.context["db"]

        # Decode JWT from header
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")

        # save profile picture to current folder

        # Check if the user is authenticated
        token_data = check_auth(authorization)

        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])

        if not user:
            logger.error(
                f"[{UpdateUserProfile.__name__}] User not found or invalid token"
            )
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )

        db_profile = user.profile
        if not db_profile:
            logger.error(
                f"[{UpdateUserProfile.__name__}] User profile not found for user {user.username}"
            )
            raise HTTPException(status_code=404, detail="User profile not found")

        # Update profile picture if provided
        profile_picture_path = (
            handle_file_upload(profile_photo, "profile_pictures")
            if profile_photo
            else None
        )

        # Update profile attributes
        updated_attributes = {
            "first_name": first_name,
            "last_name": last_name,
            "bio": bio,
            "profile_photo": profile_picture_path,
        }

        for attr, value in updated_attributes.items():
            if value is not None:  # Only update if value is provided
                setattr(db_profile, attr, value)

        try:
            user_id = crud.save_to_db(db, db_profile)
            logger.info(
                f"[{UpdateUserProfile.__name__}] User profile updated successfully for user {user.username}"
            )
            return UpdateUserProfile(ok=True, user_id=user_id)
        except Exception as e:
            db.rollback()
            logger.error(
                f"[{UpdateUserProfile.__name__}] Error updating user profile: {str(e)}"
            )
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

        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")

        # Check if the user is authenticated
        token_data = check_auth(authorization)

        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])

        if not user:
            logger.error("User not found or invalid token")
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


class FileUpload(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    ok = graphene.Boolean()
    filename = graphene.String()
    filepath = graphene.String()

    async def mutate(self, info, file: UploadFile):
        # upload_dir = Path("uploads")
        # upload_dir.mkdir(parents=True, exist_ok=True)
        # file_location = upload_dir / file.filename
        # filename includes directory path remove it
        filename = file.filename.split("/")[-1]
        try:
            file_location = f"uploads/{filename}"  # Specify your upload directory
            with open(file_location, "wb") as f:
                f.write(await file.read())  # Save the uploaded file
            logger.info(f"[{FileUpload.__name__}] File uploaded successfully: {filename}")
            return FileUpload(ok=True, filename=filename, filepath=file_location)
        except Exception as e:
            logger.error(f"[{FileUpload.__name__}] Error uploading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# Mutation class to add all mutations
class Mutation(graphene.ObjectType):
    create_role = CreateRole.Field()
    create_user = CreateUser.Field()
    login = Login.Field()
    update_user_profile = UpdateUserProfile.Field()
    create_post = CreatePost.Field()
    file_upload = FileUpload.Field()
