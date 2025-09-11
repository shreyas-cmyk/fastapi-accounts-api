import jwt
import datetime
from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

# FastAPI app
app = FastAPI(
    title="Accounts API",
    description="Search accounts by company name or website (with token authentication).",
    version="2.0.0"
)

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key for JWT
SECRET_KEY = "supersecretkey"  # replace with secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Neon DB configuration (your provided credentials)
DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_8ykcVJYtDw9R",
    "host": "ep-royal-pond-a1oahaiz-pooler.ap-southeast-1.aws.neon.tech",
    "port": "5432"
}

# DB connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# Utility: create JWT token
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Auth dependency: validate token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# Endpoint to generate token
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # For demo → any email/password is accepted
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


# Search endpoint (protected)
@app.get("/search")
def search_accounts(
    company: Optional[str] = Query(None, description="Company name to search"),
    website: Optional[str] = Query(None, description="Website to search"),
    fuzzy: bool = Query(False, description="Enable fuzzy search"),
    current_user: str = Depends(get_current_user)
):
    try:
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
            raise HTTPException(status_code=400, detail="Provide at least one parameter: company or website")

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"count": len(results), "results": results, "requested_by": current_user}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Log Render URL when app starts
@app.on_event("startup")
async def startup_event():
    render_url = "https://fastapi-accounts-api.onrender.com"
    print(f"✅ Service running at: {render_url}")
    print("📌 Use /docs for Swagger UI or /redoc for ReDoc")

@app.get("/")
def root():
    return {"message": "API is running. Use /docs for Swagger UI or /accounts for data."}

