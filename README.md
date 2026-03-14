# CoreInventory

A document-based inventory management system that tracks products, stock levels, and movements across multiple locations.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure database:
- Copy `.env.example` to `.env`
- Update `DATABASE_URL` with your database connection string

5. Run migrations:
```bash
alembic upgrade head
```

## Database Support

The system supports:
- PostgreSQL (recommended for production)
- MySQL
- SQLite (for development/testing)

## Project Structure

```
core_inventory/
├── models/          # Database models
├── components/      # Business logic components
├── migrations/      # Alembic migration scripts
└── tests/          # Unit and property-based tests
```
