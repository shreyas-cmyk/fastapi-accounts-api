from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

# ---------------------------------------------
# FastAPI App Configuration
# ---------------------------------------------
app = FastAPI(
    title="Accounts API",
    description="API to fetch accounts with Exact/Fuzzy Search and Website Search",
    version="1.0.0"
)

# Enable CORS (required if front-end will call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain for security in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------
# Database Configuration
# ---------------------------------------------
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "UmR9sGpLkSuK0PzM",
    "host": "db.zpqzrnnjmzmmgpiuouob.supabase.co",
    "port": "5432"
}

# DB connection function
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ---------------------------------------------
# Root Endpoint - API Status
# ---------------------------------------------
@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Accounts API is running successfully 🎉",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health",
        "search_example": "/search?company=Google&fuzzy=true"
    }

# ---------------------------------------------
# Health Check Endpoint
# ---------------------------------------------
@app.get("/health")
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "message": "Database connection successful ✅"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ---------------------------------------------
# Search Accounts Endpoint
# ---------------------------------------------
@app.get("/search")
def search_accounts(
    company: Optional[str] = Query(None, description="Company name to search"),
    website: Optional[str] = Query(None, description="Website to search"),
    fuzzy: bool = Query(False, description="Enable fuzzy search for company names")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build dynamic query based on params
        query = "SELECT * FROM accounts WHERE 1=1"
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

        # Ensure at least one parameter is provided
        if not company and not website:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least one search parameter: company or website"
            )

        # Execute query
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail="No matching records found.")

        return {"count": len(results), "results": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
