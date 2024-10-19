import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.models as models


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


# Authenticate user
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    # Check if user exists and password is correct
    if user and check_password(password, user.hashed_password):
        return user
    raise HTTPException(status_code=401, detail="Incorrect username or password")
