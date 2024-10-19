from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums for post visibility, post type, and media type
class PostVisibilityEnum(str, Enum):
    public = "public"
    private = "private"
    followers = "followers"


class PostTypeEnum(str, Enum):
    post = "post"
    share = "share"
    promotion = "promotion"


class MediaTypeEnum(str, Enum):
    image = "image"
    video = "video"
    audio = "audio"
    document = "document"


# Pydantic schemas


# User schema
class UserSchema(BaseModel):
    username: str
    email: str
    role_id: int

    class Config:
        from_attributes = True  # Allows ORM conversion


# Role schema
class RoleSchema(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# UserProfile schema
class UserProfileSchema(BaseModel):
    first_name: str
    last_name: str
    bio: Optional[str] = None
    profile_photo: Optional[str] = None  # URL or file path to the profile photo

    class Config:
        from_attributes = True


# Media schema
class MediaSchema(BaseModel):
    file_url: HttpUrl  # Ensures the file URL is a valid URL format
    media_type: MediaTypeEnum

    class Config:
        from_attributes = True


# Comment schema
class CommentSchema(BaseModel):
    content: str
    user_id: int
    post_id: int
    likes: int = 0
    parent_comment_id: Optional[int] = None  # For replies to other comments
    created_at: datetime

    class Config:
        from_attributes = True


# Post schema
class PostSchema(BaseModel):
    title: str
    content: str
    user_id: int
    likes: int = 0
    visibility: PostVisibilityEnum = PostVisibilityEnum.public
    post_type: PostTypeEnum = PostTypeEnum.post
    parent_post_id: Optional[int] = None  # For shared posts
    created_at: datetime

    # Include media and comments as optional lists
    media: Optional[List[MediaSchema]] = []
    comments: Optional[List[CommentSchema]] = []

    class Config:
        from_attributes = True
