import os
import uuid
import json
from typing import Optional
from psycopg2.sql import DEFAULT
from fastapi import FastAPI, HTTPException, Depends, Cookie, Response, status
from pydantic import BaseModel, EmailStr, Field
import psycopg2
import bcrypt
import redis 

app = FastAPI()


# =========================
# PostgreSQL connection
# =========================

DATABASE_URL = os.getenv("PG_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# =========================
# PostgreSQL connection
# =========================

REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True  # Automatically decodes Redis bytes to string
)

DEFAULT_EXPIRE_SECONDS = 3600

# =========================
# Request models
# =========================

class RegisterRequest(BaseModel):
    name: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# =========================
# Authentication Dependency
# =========================

def get_current_user(session_id: Optional[str] = Cookie(None, alias="session_id")):
    """
    FastAPI dependency to protect routes requiring authentication.
    Reads 'session_id' from HTTP cookies and verifies it in Redis.
    """
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session cookie"
        )

    # Retrieve session payload from Redis
    session_data = redis_client.get(f"session:{session_id}")
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    # Parse JSON string back into dictionary
    return json.loads(session_data)

# =========================
# Register
# =========================

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: RegisterRequest):

    # Hash password
    password_hash = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s);
            """,
            (user.name, user.email, password_hash)
        )


        conn.commit()

        return {
            "message": "User registered successfully",
        }

    except psycopg2.errors.UniqueViolation:
        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    finally:
        cursor.close()
        conn.close()


# =========================
# Login
# =========================

@app.post("/login")
def login(user: LoginRequest, response: Response):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, email, password_hash
            FROM users
            WHERE email = %s;
            """,
            (user.email,)
        )

        db_user = cursor.fetchone()

        if not db_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        user_id, email, password_hash = db_user

        # Check password
        password_correct = bcrypt.checkpw(
            user.password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

        if not password_correct:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

            # 1. Create unique session identifier
        session_id = str(uuid.uuid4())

        # 2. Store session state in Redis with automatic expiration (TTL)
        session_payload = {
            "user_id": user_id,
            "email": email
        }
        redis_client.setex(
            name=f"session:{session_id}",
            time=DEFAULT_EXPIRE_SECONDS,
            value=json.dumps(session_payload)
        )

        # 3. Set HttpOnly cookie on client response
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,       # Prevents JavaScript client-side access (XSS protection)
            max_age=DEFAULT_EXPIRE_SECONDS,
            samesite="lax",      # Protects against CSRF
            secure=False        # Set to True in production (requires HTTPS)
        )

        return {
            "message": "Login successful",
            "user_id": user_id
        }

    finally:
        cursor.close()
        conn.close()

@app.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Protected endpoint testing active session validation.
    """
    return {
        "message": "Authenticated successfully",
        "user": current_user
    }


@app.post("/logout")
def logout(
    response: Response,
    session_id: Optional[str] = Cookie(None, alias="session_id")
):
    """
    Invalidates current session in Redis and clears browser cookie.
    """
    if session_id:
        # Delete key from Redis store
        redis_client.delete(f"session:{session_id}")

    # Remove browser cookie
    response.delete_cookie(key="session_id")
    return {"message": "Logged out successfully"}



