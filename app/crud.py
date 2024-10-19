from sqlalchemy.orm import Session

import app.models as models


def find_role_by_id(db: Session, role_id: int):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    return role


def find_all_roles(db: Session):
    return db.query(models.Role).all()


def find_user_by_id(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user


def find_user_by_username(db: Session, username: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    return user


def find_all_users(db: Session):
    return db.query(models.User).all()


def find_user_profile(db: Session, user_id: int):
    user_profile = (
        db.query(models.UserProfile)
        .filter(models.UserProfile.user_id == user_id)
        .first()
    )
    return user_profile


def find_post_by_id(db: Session, post_id: int):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    return post


def save_to_db(db: Session, model):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model.id
