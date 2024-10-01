import uvicorn
import graphene
import bcrypt
from fastapi import FastAPI, Depends, HTTPException
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr

import models
from db_configuration import get_db
from schemas import UserModel, RoleModel, UserSchema

# FastAPI app initialization
app = FastAPI()


# Function to hash a password
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# Function to verify the password
def check_password(entered_password: str, stored_hashed_password: str) -> bool:
    return bcrypt.checkpw(
        entered_password.encode("utf-8"), stored_hashed_password.encode("utf-8")
    )


# GraphQL Queries
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

        # Create UserSchema instance
        user_data = UserSchema(username=username, email=email, role_id=role_id)
        hashed_password = hash_password(password)

        # Create a new User instance
        db_user = models.User(
            username=user_data.username,
            email=user_data.email,
            role_id=user_data.role_id,
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
class UserMutations(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_role = CreateRole.Field()


# Add the GraphQL route to FastAPI with dependency injection for database session
app.mount(
    "/graphql",
    GraphQLApp(
        schema=graphene.Schema(query=Query, mutation=UserMutations),
        context_value=lambda request: {"db": next(get_db())},
        on_get=make_graphiql_handler(),
    ),
)


# Example root route
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI with GraphQL for Users and Roles"}


# Entry point for running the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
