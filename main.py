from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

# FastAPI App Config
app = FastAPI(
    title="Accounts API",
    description="Search accounts by company name and website with exact or fuzzy search.",
    version="1.0.0"
)

# NeonDB Database Configuration
DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_8ykcVJYtDw9R",
    "host": "ep-royal-pond-a1oahaiz-pooler.ap-southeast-1.aws.neon.tech",
    "port": "5432"
}

# Function to connect to NeonDB
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Root URL → Search Form
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Accounts Search</title>
        </head>
        <body style="font-family: Arial; padding: 30px; background-color: #f7f7f7;">
            <h1 style="color: #4CAF50;">🔍 Accounts Search</h1>
            <form action="/search" method="get" style="margin-bottom: 20px;">
                <label><b>Company Name:</b></label>
                <input type="text" name="company" placeholder="Enter company name" style="padding: 8px; width: 300px;"><br><br>
                
                <label><b>Website:</b></label>
                <input type="text" name="website" placeholder="Enter website" style="padding: 8px; width: 300px;"><br><br>
                
                <label><b>Fuzzy Search:</b></label>
                <input type="checkbox" name="fuzzy" value="true"><br><br>
                
                <button type="submit" style="padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    Search
                </button>
            </form>
        </body>
    </html>
    """

# Search Endpoint
@app.get("/search", response_class=HTMLResponse)
def search_accounts(
    company: Optional[str] = Query(None, description="Company name to search"),
    website: Optional[str] = Query(None, description="Website to search"),
    fuzzy: bool = Query(False, description="Enable fuzzy search for company names")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build SQL query dynamically
        query = "SELECT * FROM accounts1 WHERE 1=1"  # ✅ Use accounts1
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
            return "<h3 style='color:red;'>⚠ Please provide at least one search parameter: company or website.</h3>"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        # If no records found
        if not results:
            return "<h3 style='color:red;'>❌ No matching records found.</h3>"

        # Create HTML table for results
        table_html = """
        <html>
            <head>
                <title>Search Results</title>
            </head>
            <body style="font-family: Arial; padding: 20px;">
                <h2 style="color: #4CAF50;">✅ Search Results</h2>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #4CAF50; color: white;">
        """

        # Table Headers
        for col in results[0].keys():
            table_html += f"<th style='padding: 8px; text-align: left;'>{col}</th>"
        table_html += "</tr>"

        # Table Rows
        for row in results:
            table_html += "<tr>"
            for val in row.values():
                table_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{val}</td>"
            table_html += "</tr>"

        table_html += "</table></body></html>"

        return table_html

    except Exception as e:
        return f"<h3 style='color:red;'>🚨 Internal Server Error: {str(e)}</h3>"
