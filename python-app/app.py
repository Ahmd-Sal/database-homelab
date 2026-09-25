import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
import psycopg2
import bcrypt

app = FastAPI()


# =========================
# PostgreSQL connection
# =========================

DATABASE_URL = os.getenv("PG_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


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
# Register
# =========================

@app.post("/register")
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
def login(user: LoginRequest):

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

        return {
            "message": "Login successful",
            "user_id": user_id
        }

    finally:
        cursor.close()
        conn.close()
