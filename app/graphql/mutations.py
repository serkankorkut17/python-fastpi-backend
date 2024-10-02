import graphene
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from app.utils import (
    hash_password,
    authenticate_user,
    create_access_token,
    decode_access_token,
)
import app.models as models


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
        access_token_expires = timedelta(minutes=60)
        data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.name,  # Include the user's role
            "iat": datetime.now(),  # Time the token was issued
        }
        access_token = create_access_token(
            data=data, expires_delta=access_token_expires
        )

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
        role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")

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
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            ok = True
            return CreateUser(ok=ok, user_id=db_user.id)  # Return created user's ID
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
            db.add(db_role)
            db.commit()
            db.refresh(db_role)
            return CreateRole(ok=True, role_id=db_role.id)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Error creating role: " + str(e.orig)
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
        authorization = info.context["request"].headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        token = authorization.split(" ")[1]
        token_data = decode_access_token(token)

        # Check if the token is valid
        if token_data["user"] is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Fetch the user based on token
        user = (
            db.query(models.User)
            .filter(models.User.username == token_data["user"])
            .first()
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Create new post
        db_post = models.Post(title=title, content=content, user_id=user.id)

        try:
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            return CreatePost(ok=True, post_id=db_post.id)
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
