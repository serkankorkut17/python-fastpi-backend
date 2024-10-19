from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLAlchemyEnum
import enum
import graphene

# from datetime import datetime

from app.db_configuration import Base


# Enum for post visibility
# Define the Python Enum (shared between SQLAlchemy and GraphQL)
class PostVisibility(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FOLLOWERS = "followers"

# PostVisibility = graphene.Enum.from_enum(PostVisibilityEnum)

class PostType(enum.Enum):
    POST = "post"
    SHARE = "share"
    PROMOTION = "promotion"

# PostType = graphene.Enum.from_enum(PostTypeEnum)

class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"

# MediaType = graphene.Enum.from_enum(MediaTypeEnum)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(50), unique=True, nullable=False
    )  # Role name (e.g., 'admin', 'user')
    description = Column(String(250), nullable=True)  # Optional description of the role

    users = relationship("User", back_populates="role", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )  # Foreign key linking to roles table
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")
    profile = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("username", "email", name="uq_username_email"),)

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, role={self.role.name})>"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    bio = Column(String(250), nullable=True)
    profile_photo = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    # title = Column(String(100), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    likes = Column(Integer, default=0)  # Like count
    visibility = Column(SQLAlchemyEnum(PostVisibility), values_callable=lambda x: [e.value for e in x])
    post_type = Column(SQLAlchemyEnum(PostType), values_callable=lambda x: [e.value for e in x])
    parent_post_id = Column(
        Integer, ForeignKey("posts.id"), nullable=True
    )  # For shared posts

    user = relationship("User", back_populates="posts")
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    media = relationship(
        "Media", back_populates="post", cascade="all, delete-orphan"
    )  # Relationship with media

    def __repr__(self):
        return f"<Post(content={self.content}, user_id={self.user_id}, visibility={self.visibility})>"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )

    # New fields
    likes = Column(Integer, default=0)  # Like count for comments
    parent_comment_id = Column(
        Integer, ForeignKey("comments.id"), nullable=True
    )  # For threaded comments (replies)

    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    replies = relationship(
        "Comment", back_populates="parent_comment", cascade="all, delete-orphan"
    )  # Self-referencing for threaded comments
    parent_comment = relationship("Comment", remote_side=[id])

    def __repr__(self):
        return f"<Comment(content={self.content}, user_id={self.user_id})>"


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    file_url = Column(String, nullable=False)  # URL or path to the media file
    media_type = Column(
        SQLAlchemyEnum(MediaType), values_callable=lambda x: [e.value for e in x]
    )  # Type of media (image, video, etc.)
    post_id = Column(
        Integer, ForeignKey("posts.id"), nullable=False
    )  # Link to the post

    post = relationship("Post", back_populates="media")

    def __repr__(self):
        return f"<Media(file_url={self.file_url}, media_type={self.media_type})>"