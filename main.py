from fastapi import FastAPI
from psycopg2 import connect
from psycopg2.extras import RealDictCursor

# --------------------------
# FastAPI App Instance
# --------------------------
app = FastAPI(
    title="Accounts API",
    description="API to fetch account details with Exact / Fuzzy / Website search",
    version="1.0.0"
)

# --------------------------
# Database Configuration
# --------------------------
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "UmR9sGpLkSuK0PzM",
    "host": "db.zpqzrnnjmzmmgpiuouob.supabase.co",
    "port": "5432"
}

# --------------------------
# Root Endpoint
# --------------------------
@app.get("/")
def home():
    return {"message": "FastAPI is running successfully! Visit /accounts to use the API."}

# --------------------------
# Accounts API with Exact / Fuzzy / Website Search
# --------------------------
@app.get("/accounts")
def get_accounts(company: str = None, website: str = None, search_type: str = "exact"):
    try:
        # Connect to Database
        conn = connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Base Query
        query = "SELECT * FROM accounts WHERE TRUE"
        params = []

        # Company Search (Exact / Fuzzy)
        if company:
            if search_type.lower() == "fuzzy":
                query += " AND account_global_legal_name ILIKE %s"
                params.append(f"%{company}%")
            else:
                query += " AND LOWER(account_global_legal_name) = LOWER(%s)"
                params.append(company)

        # Website Search
        if website:
            query += " AND website ILIKE %s"
            params.append(f"%{website}%")

        # Execute Query
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        # Close DB Connection
        cursor.close()
        conn.close()

        # Handle No Results
        if not results:
            return {"message": "No matching records found.", "count": 0, "data": []}

        # Return Success Response
        return {"count": len(results), "data": results}

    except Exception as e:
        return {"error": str(e)}
