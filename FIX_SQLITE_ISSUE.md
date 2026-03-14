# Fix SQLite DLL Issue - Step by Step Guide

## Problem
You're getting this error:
```
ImportError: DLL load failed while importing _sqlite3: The specified module could not be found.
```

This happens because Anaconda's Python is missing the SQLite DLL file.

---

## Solution 1: Copy SQLite DLL (Quickest Fix)

### Step 1: Check if sqlite3.dll exists in Anaconda
Open File Explorer and navigate to:
```
C:\Users\Lenovo\Anaconda3\DLLs\
```

Look for `sqlite3.dll` file.

### Step 2A: If sqlite3.dll EXISTS
Run this command in your terminal:
```bash
copy "C:\Users\Lenovo\Anaconda3\DLLs\sqlite3.dll" "C:\Users\Lenovo\Anaconda3\Library\bin\"
```

### Step 2B: If sqlite3.dll DOES NOT EXIST
Download it manually:

1. Go to: https://www.sqlite.org/download.html
2. Download: **sqlite-dll-win64-x64-XXXXXXX.zip** (latest version)
3. Extract the zip file
4. Copy `sqlite3.dll` to both:
   - `C:\Users\Lenovo\Anaconda3\DLLs\`
   - `C:\Users\Lenovo\Anaconda3\Library\bin\`

### Step 3: Test if it works
```bash
python -c "import sqlite3; print('SQLite works!')"
```

If you see "SQLite works!" - you're good to go!

### Step 4: Run the server
```bash
run_server.bat
```

---

## Solution 2: Use Standalone Python (Alternative)

If Solution 1 doesn't work, install standalone Python:

### Step 1: Download Python
1. Go to: https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 (Windows installer)
3. **IMPORTANT**: Check "Add Python to PATH" during installation

### Step 2: Create new virtual environment
```bash
# Close current terminal and open a new one
cd C:\Users\Lenovo\Desktop\hackathon

# Create venv with standalone Python
py -m venv venv_standalone

# Activate it
venv_standalone\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run the server
```bash
python start_api.py
```

---

## Solution 3: Use PostgreSQL Instead of SQLite

If SQLite continues to cause issues, switch to PostgreSQL:

### Step 1: Install PostgreSQL
1. Download from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for the `postgres` user

### Step 2: Create database
Open pgAdmin or run in terminal:
```bash
psql -U postgres
CREATE DATABASE coreinventory;
\q
```

### Step 3: Update .env file
Change the DATABASE_URL in `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/coreinventory
SECRET_KEY=dev-secret-key-change-in-production
```

### Step 4: Install PostgreSQL driver
```bash
pip install psycopg2-binary
```

### Step 5: Run migrations and start server
```bash
alembic upgrade head
python start_api.py
```

---

## Quick Test Commands

After fixing the issue, test with these commands:

### 1. Test Python and SQLite
```bash
python -c "import sqlite3; print('SQLite:', sqlite3.sqlite_version)"
```

### 2. Test database connection
```bash
python -c "from core_inventory.database import engine; print('Database connected!')"
```

### 3. Start the API server
```bash
run_server.bat
```

### 4. Test the API
Open browser and go to:
```
http://localhost:5000/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2024-..."
}
```

---

## Still Having Issues?

### Check Python version
```bash
python --version
```
Should be Python 3.8 or higher.

### Check which Python is being used
```bash
where python
```

### Check installed packages
```bash
pip list | findstr -i "sqlalchemy flask"
```

### View detailed error
```bash
python start_api.py
```
Copy the full error message and we can troubleshoot further.

---

## Recommended Approach

**Try in this order:**
1. ✅ Solution 1 (Copy DLL) - Takes 2 minutes
2. ✅ Solution 2 (Standalone Python) - Takes 10 minutes
3. ✅ Solution 3 (PostgreSQL) - Takes 20 minutes but most reliable

Good luck! 🚀
