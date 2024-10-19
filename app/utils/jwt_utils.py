import os
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException

# load environment variables
load_dotenv(".env")

# Ensure the SECRET_KEY is set and handle the error if it's missing
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("SECRET_KEY not found in environment variables")

# JWT algorithm
algorithm = (
    "HS256"  # For stronger security, consider using RS256 with private/public key pairs
)
issuer = "serkankorkut.dev"  # Set your app name or domain
audience = "serkankorkut.dev/users"  # Define the expected audience, e.g., your users


# Create a JWT access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    # Copy the data to avoid modifying the original
    to_encode = data.copy()
    # !!! utcnow deprecated !!!
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=30)
    )  # Default to 30 minutes if no expiration provided
    # Add the expiration and audience claims
    to_encode.update({"exp": expire, "aud": audience, "iss": issuer})
    # Encode the JWT token
    access_token = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return access_token


# Decode and validate a JWT token
def decode_access_token(token: str):
    try:
        token_data = jwt.decode(
            token,  # The token to decode
            secret_key,  # Use the same secret key to decode the token
            algorithms=[algorithm],  # Specify the expected algorithm
            audience=audience,  # Validate the audience
            issuer=issuer,  # Validate the issuer
            leeway=10,  # Allows 10 seconds of clock skew tolerance
        )
        return token_data
    # Handle the common JWT errors
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Generate an access token
def generate_access_token(user):
    access_token_expires = timedelta(minutes=60)
    data = {
        "user_id": user.id,  # Include the user's ID
        "username": user.username,  # Include the user's username
        "role": user.role.name,  # Include the user's role
        "iat": datetime.utcnow(),  # Time the token was issued
    }
    # Create the access token
    access_token = create_access_token(data=data, expires_delta=access_token_expires)

    return access_token


# Check the authorization header
def check_auth(authorization: str):
    # Ensure the Authorization header is present
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Extract and decode the JWT token
    try:
        token = authorization.split(" ")[1]  # 'Bearer <token>'
        token_data = decode_access_token(token)
    # Handle common JWT errors
    except (IndexError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the token contains the expected data
    if token_data["username"] is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return token_data
