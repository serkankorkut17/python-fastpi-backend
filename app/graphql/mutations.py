import graphene
from fastapi import HTTPException, UploadFile, Depends
from graphene_file_upload.scalars import Upload
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import jwt
import os
import shutil
import json
from pathlib import Path

# Import custom modules
from app.db_configuration import get_db
from app.utils import (
    hash_password,
    authenticate_user,
    generate_access_token,
    check_auth,
    handle_file_upload,
)
import app.models as models
from app.models import PostVisibility, PostType, MediaType
import app.crud as crud
from app.utils import logger


# GraphQL Mutations
# Login mutation
class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)  # Required username
        password = graphene.String(required=True)  # Required password

    ok = graphene.Boolean()  # Return True if login is successful
    access_token = graphene.String()  # Return the generated access token

    @staticmethod
    async def mutate(root, info, username, password):
        db: Session = info.context["db"]
        # Authenticate the user
        user = authenticate_user(db, username, password)
        # Generate access token
        access_token = generate_access_token(user)
        # update last_login field
        # user.last_login = datetime.utcnow()
        user.last_login = datetime.now(timezone.utc)
        crud.save_to_db(db, user)
        # Log the successful login
        logger.info(f"[{Login.__name__}] User {username} logged in successfully")
        # Return the access token
        return Login(ok=True, access_token=access_token)


# Create user mutation
class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)  # Required username
        email = graphene.String(required=True)  # Required email
        role_id = graphene.Int(required=True)  # Required role ID
        password = graphene.String(required=True)  # Required password

    ok = graphene.Boolean()  # Return True if user creation is successful
    user_id = graphene.Int()  # Return the created user's ID

    @staticmethod
    def mutate(root, info, username, email, role_id, password):
        db: Session = info.context["db"]
        # Check if the role exists
        role = crud.find_role_by_id(db, role_id)
        if not role:
            # create a new role
            role = models.Role(name="user", description="Default user role")
            role_id = crud.save_to_db(db, role)
            role = crud.find_role_by_id(db, role_id)
            if not role:
                logger.error(f"[{CreateUser.__name__}] Role with ID {role_id} not found")
                raise HTTPException(status_code=404, detail="Role not found")
        # Hash the password
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
        # Handle any IntegrityError exceptions
        except IntegrityError as e:
            db.rollback()  # Roll back the session on error
            # Log the error
            logger.error(f"[{CreateUser.__name__}] Error creating user: {str(e.orig)}")
            raise HTTPException(
                status_code=400, detail=str(e.orig)
            )  # Provide a clear error message


# Create role mutation
class CreateRole(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)  # Required role name
        description = graphene.String()  # Optional role description

    ok = graphene.Boolean()  # Return True if role creation is successful
    role_id = graphene.Int()  # Return the created role's ID

    @staticmethod
    def mutate(root, info, name, description=None):
        db: Session = info.context["db"]
        # Create new role instance
        db_role = models.Role(name=name, description=description)
        # Add role to the session and commit
        try:
            role_id = crud.save_to_db(db, db_role)
            # Log the successful role creation
            logger.info(f"[{CreateRole.__name__}] Role {name} created successfully")
            return CreateRole(ok=True, role_id=role_id)  # Return created role's ID
        # Handle any IntegrityError exceptions
        except IntegrityError as e:
            db.rollback()
            logger.error(f"[{CreateRole.__name__}] Error creating role: {str(e.orig)}")
            raise HTTPException(
                status_code=400, detail="Error creating role: " + str(e.orig)
            )


# Update user profile mutation
class UpdateUserProfile(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=False)  # Optional first name
        last_name = graphene.String(required=False)  # Optional last name
        bio = graphene.String(required=False)  # Optional bio
        profile_photo = Upload(required=False)  # Optional profile photo

    ok = graphene.Boolean()  # Return True if profile update is successful
    user_id = graphene.Int()  # Return the user's ID
    profile_photo_url = graphene.String()  # Return the profile photo URL

    @staticmethod
    def mutate(
        root, info, first_name=None, last_name=None, bio=None, profile_photo=None
    ):
        db: Session = info.context["db"]
        # db: Session = next(get_db())
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")
        # Check if the user is authenticated
        token_data = check_auth(authorization)
        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])
        # If user is not found, return an error
        if not user:
            logger.error(
                f"[{UpdateUserProfile.__name__}] User not found or invalid token"
            )
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )
        # Fetch the user profile
        db_profile = user.profile
        # If user profile is not found, return an error
        if not db_profile:
            logger.error(
                f"[{UpdateUserProfile.__name__}] User profile not found for user {user.username}"
            )
            raise HTTPException(status_code=404, detail="User profile not found")
        # Update profile picture if provided
        profile_picture_path, content_type = (
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
        # Update profile attributes
        for attr, value in updated_attributes.items():
            if value is not None:  # Only update if value is provided
                setattr(db_profile, attr, value)
        # Save the updated profile to the database
        try:
            user_id = crud.save_to_db(db, db_profile)
            # Log the successful profile update
            logger.info(
                f"[{UpdateUserProfile.__name__}] User profile updated successfully for user {user.username}"
            )
            return UpdateUserProfile(
                ok=True, user_id=user_id, profile_photo_url=profile_picture_path
            )
        # Handle any exceptions
        except Exception as e:
            db.rollback()
            logger.error(
                f"[{UpdateUserProfile.__name__}] Error updating user profile: {str(e)}"
            )
            raise HTTPException(
                status_code=400, detail="Error updating user profile: " + str(e)
            )


# Create post mutation
class CreatePost(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)  # Required content
        visibility = graphene.String(required=False)  # Optional visibility
        post_type = graphene.String(required=False)  # Optional post type
        media_files = graphene.List(Upload, required=False)  # Optional media files

    ok = graphene.Boolean()  # Return True if post creation is successful
    post_id = graphene.Int()  # Return the created post's ID

    @staticmethod
    def mutate(root, info, content, visibility=None, post_type=None, media_files=None):
        db: Session = info.context["db"]
        # db: Session = next(get_db())
        # Log the post creation details
        logger.info(
            f"CreatePost: Content: {content}, Visibility: {visibility}, Post Type: {post_type}"
        )
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")
        # Check if the user is authenticated
        token_data = check_auth(authorization)
        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])
        # If user is not found, return an error
        if not user:
            logger.error("User not found or invalid token")
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )
        # if visibility is not provided, set it to public by default
        # if visibility is "public" or "private" or "followers", set it to the provided value
        # if visibility is not one of the above, set it to public by default
        if visibility:
            visibility = visibility.upper()
            if visibility not in ["PUBLIC", "PRIVATE", "FOLLOWERS"]:
                visibility = PostVisibility.PUBLIC
            else:
                visibility = PostVisibility[visibility.upper()]
        # if post_type is not provided, set it to post by default
        # if post_type is "post" or "share", set it to the provided value
        # if post_type is not one of the above, set it to post by default
        if post_type:
            post_type = post_type.upper()
            if post_type not in ["POST", "SHARE", "PROMOTION"]:
                post_type = PostType.POST
            else:
                post_type = PostType[post_type.upper()]
        # Create new post
        db_post = models.Post(
            content=content,
            visibility=visibility,
            post_type=post_type,
            user_id=user.id,
        )
        # Add post to the session and commit
        try:
            post_id = crud.save_to_db(db, db_post)
            # Log the successful post creation
            logger.info(
                f"CreatePost: New post created by user {user.username} with post_id {post_id}"
            )
            # Handle media if any URLs are provided
            if media_files:
                for url in media_files:
                    # Save the media file to the uploads/posts directory
                    media_path, media_type = handle_file_upload(url, "posts")
                    logger.info(
                        f"Media saved: Media path: {media_path}, Media type: {media_type}"
                    )
                    # Set the media type based on the content type
                    if media_type.startswith("image"):
                        media_type = MediaType.IMAGE
                    elif media_type.startswith("video"):
                        media_type = MediaType.VIDEO
                    elif media_type.startswith("audio"):
                        media_type = MediaType.AUDIO
                    elif media_type.startswith("document"):
                        media_type = MediaType.DOCUMENT
                    db_media = models.Media(
                        file_url=media_path, media_type=media_type, post_id=post_id
                    )
                    crud.save_to_db(db, db_media)
            # Log the successful post creation
            logger.info(
                f"CreatePost: New post created by user {user.username} with post_id {post_id}"
            )
            return CreatePost(ok=True, post_id=post_id)
        # Handle any exceptions
        except Exception as e:
            db.rollback()
            logger.error(f"CreatePost: Error creating post - {str(e)}")
            raise HTTPException(
                status_code=400, detail="Error creating post: " + str(e)
            )


# Create comment mutation
class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)  # Required post ID
        content = graphene.String(required=True)  # Required content

    ok = graphene.Boolean()  # Return True if comment creation is successful
    comment_id = graphene.Int()  # Return the created comment's ID

    @staticmethod
    def mutate(root, info, post_id, content):
        db: Session = info.context["db"]
        # db: Session = next(get_db())
        # Log the comment creation details
        logger.info(f"CreateComment: Post ID: {post_id}, Content: {content}")
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")
        # Check if the user is authenticated
        token_data = check_auth(authorization)
        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])
        # If user is not found, return an error
        if not user:
            logger.error("User not found or invalid token")
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )
        # If post is not found, return an error
        post = crud.find_post_by_id(db, post_id)
        if not post:
            logger.error("Post not found")
            raise HTTPException(status_code=404, detail="Post not found")
        # Create new comment
        db_comment = models.Comment(content=content, post_id=post_id, user_id=user.id)
        # Add comment to the session and commit
        try:
            comment_id = crud.save_to_db(db, db_comment)
            # Log the successful comment creation
            logger.info(
                f"CreateComment: New comment created by user {user.username} with comment_id {comment_id}"
            )
            return CreateComment(ok=True, comment_id=comment_id)
        # Handle any exceptions
        except Exception as e:
            db.rollback()
            logger.error(f"CreateComment: Error creating comment - {str(e)}")
            raise HTTPException(
                status_code=400, detail="Error creating comment: " + str(e)
            )


# Create reply mutation
class CreateReply(graphene.Mutation):
    class Arguments:
        comment_id = graphene.Int(required=True)  # Required comment ID
        content = graphene.String(required=True)  # Required content

    ok = graphene.Boolean()  # Return True if comment creation is successful
    comment_id = graphene.Int()  # Return the created comment's ID

    @staticmethod
    def mutate(root, info, comment_id, content):
        db: Session = info.context["db"]
        # db: Session = next(get_db())
        # Log the comment creation details
        logger.info(f"CreateComment: Comment ID: {comment_id}, Content: {content}")
        # Get the Authorization header from the request
        request = info.context["request"]
        authorization = request.headers.get("Authorization")
        # Check if the user is authenticated
        token_data = check_auth(authorization)
        # Fetch the user based on token
        user = crud.find_user_by_username(db, token_data["username"])
        # If user is not found, return an error
        if not user:
            logger.error("User not found or invalid token")
            raise HTTPException(
                status_code=401, detail="User not found or invalid token"
            )
        # Find parent comment
        parent_comment = crud.find_comment_by_id(db, comment_id)
        if not parent_comment:
            logger.error("Parent comment not found")
            raise HTTPException(status_code=404, detail="Parent comment not found")
        # Create new comment
        db_comment = models.Comment(
            content=content,
            post_id=parent_comment.post_id,
            parent_comment_id=comment_id,
            user_id=user.id,
        )
        # Add comment to the session and commit
        try:
            comment_id = crud.save_to_db(db, db_comment)
            # Log the successful comment creation
            logger.info(
                f"CreateComment: New comment created by user {user.username} with comment_id {comment_id}"
            )
            return CreateComment(ok=True, comment_id=comment_id)
        # Handle any exceptions
        except Exception as e:
            db.rollback()
            logger.error(f"CreateComment: Error creating comment - {str(e)}")
            raise HTTPException(
                status_code=400, detail="Error creating comment: " + str(e)
            )


# File upload mutation
class FileUpload(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    ok = graphene.Boolean()
    filename = graphene.String()  # Return the file name
    filepath = graphene.String()  # Return the file path

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
            # Log the successful file upload
            logger.info(
                f"[{FileUpload.__name__}] File uploaded successfully: {filename}"
            )
            return FileUpload(ok=True, filename=filename, filepath=file_location)
        # Handle any exceptions
        except Exception as e:
            logger.error(f"[{FileUpload.__name__}] Error uploading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# Mutation class to add all mutations
class Mutation(graphene.ObjectType):
    create_role = CreateRole.Field()  # Create role mutation
    create_user = CreateUser.Field()  # Create user mutation
    login = Login.Field()  # Login mutation
    update_user_profile = UpdateUserProfile.Field()  # Update user profile mutation
    create_post = CreatePost.Field()  # Create post mutation
    create_comment = CreateComment.Field()  # Create comment mutation
    create_reply = CreateReply.Field()  # Create reply mutation
    file_upload = FileUpload.Field()  # File upload mutation
