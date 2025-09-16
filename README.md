# FastAPI Accounts API 🚀

This is a FastAPI API hosted on Render to fetch account details and department-wise services from a Supabase PostgreSQL database.

## How to Deploy on Render

### 1. Fork or Push Repo to GitHub
- Create a new repository on GitHub
- Upload these files

### 2. Connect Render
- Go to [https://dashboard.render.com/](https://dashboard.render.com/)
- Click **New Web Service**
- Connect your GitHub
- Select your repo

### 3. Configure Deployment
- **Build Command:** Leave blank
- **Start Command:**
  uvicorn main:app --host 0.0.0.0 --port $PORT

### 4. Set Environment Variables(Modify DB credentials accordingly)
- DB_NAME=postgres
- DB_USER=postgres
- DB_PASSWORD=UmR9sGpLkSuK0PzM
- DB_HOST=db.zpqzrnnjmzmmgpiuouob.supabase.co
- DB_PORT=5432

### 5. Access Swagger Docs
https://<your-app>.onrender.com/docs
