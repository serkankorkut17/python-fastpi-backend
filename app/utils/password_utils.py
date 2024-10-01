import bcrypt

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