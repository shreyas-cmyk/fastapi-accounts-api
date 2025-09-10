import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Accounts & Services API",
    description="Fetch account details and department-wise services from Supabase Postgres DB",
    version="3.0"
)

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "UmR9sGpLkSuK0PzM",
    "host": "db.zpqzrnnjmzmmgpiuouob.supabase.co",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/account/details")
def get_account_and_services(
    name: str = Query(None, description="Enter company name to fetch details"),
    website: str = Query(None, description="Enter company website to fetch details"),
    fuzzy: bool = Query(False, description="Enable fuzzy search for company name")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if website:
            cursor.execute(
                "SELECT * FROM accounts1 WHERE LOWER(website) = LOWER(%s) LIMIT 1;",
                (website,))
        elif name:
            if fuzzy:
                cursor.execute(
                    "SELECT * FROM accounts1 WHERE LOWER(account_global_legal_name) LIKE LOWER(%s) LIMIT 1;",
                    (f"%{name}%",))
            else:
                cursor.execute(
                    "SELECT * FROM accounts1 WHERE LOWER(account_global_legal_name) = LOWER(%s) LIMIT 1;",
                    (name,))
        else:
            raise HTTPException(status_code=400, detail="Please provide either 'name' or 'website'")

        account_row = cursor.fetchone()
        if not account_row:
            raise HTTPException(status_code=404, detail="No matching account found")

        account_columns = [desc[0] for desc in cursor.description]
        account_data = dict(zip(account_columns, account_row))

        name_filter = account_data["account_global_legal_name"]

        cursor.execute("""
            SELECT 
                MAX(account_global_legal_name) AS account_global_legal_name,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(it, '')), NULL) AS it_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(erd, '')), NULL) AS erd_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(fna, '')), NULL) AS fna_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(hr, '')), NULL) AS hr_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(procurement_and_supply_chain, '')), NULL) AS procurement_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(sales_and_marketing, '')), NULL) AS sales_marketing_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(customer_support_services, '')), NULL) AS customer_support_services,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(others_service, '')), NULL) AS other_services
            FROM services1
            WHERE LOWER(account_global_legal_name) = LOWER(%s)
            GROUP BY account_global_legal_name;
        """, (name_filter,))

        services_row = cursor.fetchone()
        services_data = {}

        if services_row:
            services_columns = [desc[0] for desc in cursor.description]
            services_dict = dict(zip(services_columns, services_row))

            for dept, services in services_dict.items():
                if dept == "account_global_legal_name":
                    continue
                if services and len(services) > 0:
                    services_data[dept.replace("_services", "").replace("_", " ").title()] = services

        response = {
            "account_details": account_data,
            "services": services_data
        }
        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
