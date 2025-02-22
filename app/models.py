from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    Table,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLAlchemyEnum
import enum

from app.db_configuration import Base


# Enum for post visibility
class PostVisibility(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FOLLOWERS = "followers"


# Enum for post type
class PostType(enum.Enum):
    POST = "post"
    SHARE = "share"
    PROMOTION = "promotion"


# Enum for media types
class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


# ROLE MODEL
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)  # Role ID
    name = Column(String(50), unique=True, nullable=False)  # Role name (unique)
    description = Column(String(250), nullable=True)  # Role description (optional)
    users = relationship(
        "User", back_populates="role", cascade="all, delete-orphan"
    )  # Relationship with users

    # __repr__ method to return a string representation of the object
    def __repr__(self):
        return f"<Role(name={self.name})>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # User ID
    username = Column(String(50), unique=True, index=True, nullable=False)  # Username
    email = Column(
        String(100), unique=True, index=True, nullable=False
    )  # Email address
    hashed_password = Column(String(255), nullable=False)  # Hashed password
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )  # Foreign key linking to roles table
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # Created timestamp
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )  # Updated timestamp
    last_login = Column(DateTime, nullable=True)  # Last login timestamp

    role = relationship("Role", back_populates="users")  # Relationship with roles
    profile = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )  # Relationship with user profile
    posts = relationship(
        "Post", back_populates="user", cascade="all, delete-orphan"
    )  # Relationship with posts
    comments = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )  # Relationship with comments
    # Unique constraint for username and email
    __table_args__ = (UniqueConstraint("username", "email", name="uq_username_email"),)

    # __repr__ method to return a string representation of the object
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, role={self.role.name})>"


# USER PROFILE MODEL
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)  # Profile ID
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # Foreign key linking to users table
    first_name = Column(String(50), nullable=False)  # First name
    last_name = Column(String(50), nullable=False)  # Last name
    bio = Column(String(250), nullable=True)  # Bio
    profile_photo = Column(String(255), nullable=True)  # Profile photo URL
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # Created timestamp
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )  # Updated timestamp

    user = relationship("User", back_populates="profile")  # Relationship with users

    # __repr__ method to return a string representation of the object
    def __repr__(self):
        return (
            f"<UserProfile(first_name={self.first_name}, last_name={self.last_name})>"
        )


# POST MODEL
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)  # Post ID
    content = Column(String, nullable=False)  # Post content
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # Created timestamp
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )  # Updated timestamp
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # Foreign key linking to users table

    likes = Column(Integer, default=0)  # Like count for posts
    visibility = Column(
        SQLAlchemyEnum(PostVisibility)
    )  # Post visibility (public, private, followers)
    post_type = Column(SQLAlchemyEnum(PostType))  # Post type (post, share, promotion)
    parent_post_id = Column(
        Integer, ForeignKey("posts.id"), nullable=True
    )  # For shared posts

    user = relationship("User", back_populates="posts")  # Relationship with users
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )  # Relationship with comments
    media = relationship(
        "Media", back_populates="post", cascade="all, delete-orphan"
    )  # Relationship with media

    # __repr__ method to return a string representation of the object
    def __repr__(self):
        return f"<Post(content={self.content}, user_id={self.user_id}, visibility={self.visibility})>"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)  # Comment ID
    content = Column(String, nullable=False)  # Comment content
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # Created timestamp
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )  # Updated timestamp
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # Foreign key linking to users table
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )  # Foreign key linking to posts table
    likes = Column(Integer, default=0)  # Like count for comments
    parent_comment_id = Column(
        Integer, ForeignKey("comments.id"), nullable=True
    )  # For threaded comments (replies)

    user = relationship("User", back_populates="comments")  # Relationship with users
    post = relationship("Post", back_populates="comments")  # Relationship with posts
    replies = relationship(
        "Comment", back_populates="parent_comment", cascade="all, delete-orphan"
    )  # Self-referencing for threaded comments
    parent_comment = relationship(
        "Comment", remote_side=[id]
    )  # Self-referencing for threaded comments

    # __repr__ method to return a string representation of the object
    def __repr__(self):
        return f"<Comment(content={self.content}, user_id={self.user_id})>"


# MEDIA MODEL
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)  # Media ID
    file_url = Column(String, nullable=False)  # URL or path to the media file
    media_type = Column(
        SQLAlchemyEnum(MediaType)
    )  # Media type (image, video, audio, document)
    post_id = Column(
        Integer, ForeignKey("posts.id"), nullable=False
    )  # Foreign key linking to posts table

    post = relationship("Post", back_populates="media")  # Relationship with posts

    # __repr__ method to return a string representation of the object
    def __repr__(self):
        return f"<Media(file_url={self.file_url}, media_type={self.media_type})>"


# Voice room participants association table
voice_room_participants = Table(
    "voice_room_participants",
    Base.metadata,
    Column("room_id", Integer, ForeignKey("voice_rooms.id", ondelete="CASCADE")),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("is_muted", Boolean, default=False),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
)

class VoiceRoom(Base):
    __tablename__ = "voice_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_private = Column(Boolean, default=False)
    max_participants = Column(Integer, default=10)

    # Relationships
    owner = relationship("User", foreign_keys=[created_by])
    participants = relationship(
        "User", secondary=voice_room_participants, backref="voice_rooms"
    )


class VoiceMessage(Base):
    __tablename__ = "voice_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("voice_rooms.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    file_url = Column(String, nullable=False)
    duration = Column(Integer)  # Duration in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    room = relationship("VoiceRoom", backref="messages")
    user = relationship("User", backref="voice_messages")
