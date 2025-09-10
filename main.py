from fastapi import FastAPI, Query, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
import os

app = FastAPI(
    title="Accounts API",
    description="API to fetch accounts with Exact/Fuzzy Search and Website Search",
    version="1.0.0"
)

# Database configuration
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "UmR9sGpLkSuK0PzM",
    "host": "db.zpqzrnnjmzmmgpiuouob.supabase.co",
    "port": "5432"
}

# Create DB connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/search")
def search_accounts(
    company: Optional[str] = Query(None, description="Company name to search"),
    website: Optional[str] = Query(None, description="Website to search"),
    fuzzy: bool = Query(False, description="Enable fuzzy search for company names")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build query dynamically based on provided params
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

        # If no params are provided
        if not company and not website:
            raise HTTPException(status_code=400, detail="Please provide at least one search parameter: company or website")

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail="No matching records found.")

        return {"count": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
