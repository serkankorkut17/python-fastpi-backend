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

        # logger.info(f"Request headers: {info.context['request'].headers}")
        # logger.info(f"Request method: {info.context['request'].method}")

        # request = info.context["request"]
        # logger.info(f"Request: {dir(request)}")

        # # Read and log request body as JSON
        # req_body = await request.body()
        
        # # Convert the request body to a string for printing
        # body_str = req_body.decode("utf-8") if isinstance(req_body, bytes) else str(req_body)
        
        # # Log the request body
        # logger.info(f"Request body: {body_str}")
        # # Log request details
        # logger.info(f"Request headers: {request.headers}")
        # logger.info(f"Request method: {request.method}")
        # logger.info(f"Request URL: {request.url}")
        # logger.info(f"Request query parameters: {request.query_params}")
        # logger.info(f"Request path parameters: {request.path_params}")
        # logger.info(f"Request client: {request.client}")
        # logger.info(f"Request cookies: {request.cookies}")


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
            db_user.profile = models.UserProfile(
                first_name=username, last_name=username
            )
            crud.save_to_db(db, db_user.profile)
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
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        bio = graphene.String(required=False)
        profile_picture = Upload(required=False)  # Optional image upload

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
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )

        db_profile = user.profile
        if not db_profile:
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


class MyUpload(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    ok = graphene.Boolean()

    @staticmethod
    async def mutate(root, info, file):

        logger.info(f"Request headers: {info.context['request'].headers}")
        logger.info(f"Request method: {info.context['request'].method}")

        request = info.context["request"]
        logger.info(f"Request: {dir(request)}")

        # Read and log request body as JSON
        req_body = await request.body()
        
        # Convert the request body to a string for printing
        body_str = req_body.decode("utf-8") if isinstance(req_body, bytes) else str(req_body)
        
        # Log the request body
        logger.info(f"Request body: {body_str}")
        # Log request details
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request query parameters: {request.query_params}")
        logger.info(f"Request path parameters: {request.path_params}")
        logger.info(f"Request client: {request.client}")
        logger.info(f"Request cookies: {request.cookies}")

        # Define the upload directory
        upload_folder = "uploads"
        upload_directory = os.path.join(
            os.getcwd(), upload_folder
        )  # Ensures correct path
        os.makedirs(
            upload_directory, exist_ok=True
        )  # Create directory if it doesn't exist

        # Create a unique filename using the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = file.filename
        base_filename, extension = os.path.splitext(original_filename)

        # Save the file with the new unique name
        output_file_path = os.path.join(
            upload_directory, f"{timestamp}_{base_filename}{extension}"
        )

        with open(output_file_path, "wb") as destination:
            shutil.copyfileobj(file.file, destination)

        # Check if the file was saved
        if os.path.exists(output_file_path):
            return MyUpload(ok=True)
        else:
            return MyUpload(ok=False)
        

# class FileUploadMutation(graphene.Mutation):
#     class Arguments:
#         file = Upload(required=True)

#     ok = graphene.Boolean()
#     filename = graphene.String()
#     filepath = graphene.String()

#     async def mutate(self, info, file):
#         upload_dir = Path("uploads")
#         upload_dir.mkdir(parents=True, exist_ok=True)
        
#         file_location = upload_dir / file.filename
#         with open(file_location, "wb") as f:
#             f.write(await file.read())
        
#         return FileUploadMutation(ok=True, filename=file.filename, filepath=str(file_location))
    
class FileUploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    ok = graphene.Boolean()
    filename = graphene.String()
    filepath = graphene.String()

    async def mutate(self, info, file: UploadFile):
        try:
            file_location = f"uploads/{file.filename}"  # Specify your upload directory
            with open(file_location, "wb") as f:
                f.write(await file.read())  # Save the uploaded file
            return FileUploadMutation(ok=True, filename=file.filename, filepath=file_location)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")




# Mutation class to add all mutations
class Mutation(graphene.ObjectType):
    create_role = CreateRole.Field()
    create_user = CreateUser.Field()
    login = Login.Field()
    update_user_profile = UpdateUserProfile.Field()
    my_upload = MyUpload.Field()
    file_upload = FileUploadMutation.Field()
    create_post = CreatePost.Field()
