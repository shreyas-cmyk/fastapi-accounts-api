from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# ===============================
# Config
# ===============================
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_8ykcVJYtDw9R",
    "host": "ep-royal-pond-a1oahaiz-pooler.ap-southeast-1.aws.neon.tech",
    "port": "5432"
}

app = FastAPI(title="Accounts API", version="2.1.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ===============================
# Database Connection
# ===============================
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ===============================
# Auth Helpers
# ===============================
def authenticate_user(email: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return False
    if not bcrypt.checkpw(password.encode("utf-8"), user["hashed_password"].encode("utf-8")):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ===============================
# Pydantic Models
# ===============================
class RegisterUser(BaseModel):
    email: str
    password: str

# ===============================
# Routes
# ===============================
@app.post("/register")
async def register(user: RegisterUser):
    conn = get_db_connection()
    cursor = conn.cursor()

    # check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")

    # hash password
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # insert new user
    cursor.execute(
        "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id",
        (user.email, hashed_pw)
    )
    user_id = cursor.fetchone()[0]
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "User registered successfully", "user_id": user_id}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm uses "username" field, but we treat it as the email
    email = form_data.username
    password = form_data.password

    user = authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/accounts")
async def search_accounts(
    company: Optional[str] = Query(None, description="Company name"),
    website: Optional[str] = Query(None, description="Website"),
    fuzzy: bool = Query(False, description="Enable fuzzy search"),
    current_user: str = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = "SELECT * FROM accounts1 WHERE 1=1"
    params = []

    if company:
        if fuzzy:
            query += " AND account_global_legal_name ILIKE %s"
            params.append(f"%{company}%")
        else:
            query += " AND account_global_legal_name = %s"
            params.append(company)

    if website:
        query += " AND hq_website = %s"
        params.append(website)

    if not company and not website:
        raise HTTPException(status_code=400, detail="Provide at least one search parameter")

    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        raise HTTPException(status_code=404, detail="No matching records found")

    return {"count": len(results), "results": results}
@app.get("/")
def read_root():
    return JSONResponse(content={"message": "FastAPI Accounts API is running!"})
