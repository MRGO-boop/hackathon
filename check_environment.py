"""Check if the environment is properly set up."""
import sys

print("=" * 60)
print("CoreInventory Environment Check")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check SQLite
try:
    import sqlite3
    print(f"✓ SQLite3 module: OK (version {sqlite3.sqlite_version})")
    sqlite_ok = True
except ImportError as e:
    print(f"✗ SQLite3 module: FAILED")
    print(f"  Error: {e}")
    sqlite_ok = False

# Check required packages
packages = [
    'sqlalchemy',
    'flask',
    'flask_cors',
    'alembic',
    'bcrypt',
    'python-dotenv',
    'hypothesis'
]

print("\nChecking required packages:")
missing_packages = []
for package in packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"  ✓ {package}")
    except ImportError:
        print(f"  ✗ {package} - NOT INSTALLED")
        missing_packages.append(package)

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)

if not sqlite_ok:
    print("\n⚠️  SQLite3 is not working!")
    print("\nQuick fixes:")
    print("1. Download sqlite3.dll from: https://www.sqlite.org/download.html")
    print("   Look for: sqlite-dll-win64-x64-XXXXXXX.zip")
    print("   Extract and copy sqlite3.dll to:")
    print(f"   - C:\\Users\\Lenovo\\Anaconda3\\DLLs\\")
    print(f"   - C:\\Users\\Lenovo\\Anaconda3\\Library\\bin\\")
    print("\n2. OR install standalone Python from python.org")
    print("\n3. OR use PostgreSQL instead (see FIX_SQLITE_ISSUE.md)")

if missing_packages:
    print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
    print(f"\nRun: pip install {' '.join(missing_packages)}")

if sqlite_ok and not missing_packages:
    print("\n✅ Environment is ready!")
    print("\nYou can now run: python start_api.py")
else:
    print("\n❌ Environment needs fixes before running the API")

print("=" * 60)
