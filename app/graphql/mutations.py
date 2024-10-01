import graphene
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.utils import hash_password
import app.models as models

# GraphQL Mutations
class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)  # Use Pydantic's EmailStr for validation
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
        role = models.Role(name=name, description=description)

        try:
            db.add(role)
            db.commit()
            db.refresh(role)
            return CreateRole(ok=True, role_id=role.id)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Error creating role: " + str(e.orig)
            )


# Mutation class to add all mutations
class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_role = CreateRole.Field()