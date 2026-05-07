# 01 - Database Setup

## Overview

Implement the SQLite database layer for Spendly by replacing the placeholder logic in `database/db.py`.

This establishes the foundational persistence layer required for all future application features including:

- Authentication
- User profiles
- Expense tracking
- Reporting

The implementation must use raw SQLite queries only (no ORM).

---

# Objectives

- Create a working SQLite connection helper
- Initialize database schema automatically
- Seed demo data safely
- Enforce relational integrity
- Ensure startup initialization from `app.py`

---

# Dependencies

None.

This is the first implementation step of the project.

---

# Routes

No route changes are required.

Existing placeholder routes in `app.py` should remain unchanged.

---

# Database Schema

## users Table

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| email | TEXT | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| created_at | TEXT | DEFAULT datetime('now') |

---

## expenses Table

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | FOREIGN KEY → users.id, NOT NULL |
| amount | REAL | NOT NULL |
| category | TEXT | NOT NULL |
| date | TEXT | NOT NULL (YYYY-MM-DD) |
| description | TEXT | Nullable |
| created_at | TEXT | DEFAULT datetime('now') |

---

# Functions to Implement

File: `database/db.py`

---

## 1. get_db()

### Responsibilities

- Open SQLite connection to:
  - `spendly.db`
  - or `expense_tracker.db`
- Enable dictionary-style row access
- Enable foreign key enforcement

### Requirements

```python
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
```

### Returns

A working SQLite connection object.

---

## 2. init_db()

### Responsibilities

- Create all required tables
- Use `CREATE TABLE IF NOT EXISTS`
- Be safe to run multiple times

### Tables Created

- users
- expenses

### Requirements

- Must not crash on repeated runs
- Must fully prepare database before app usage

---

## 3. seed_db()

### Responsibilities

Populate the database with demo data.

### Requirements

#### Prevent Duplicate Seeds

- Check if users already exist
- If data exists:
  - return immediately
  - do not insert duplicates

#### Insert Demo User

| Field | Value |
|---|---|
| name | Demo User |
| email | demo@spendly.com |
| password | demo123 |

Password must be hashed using:

```python
from werkzeug.security import generate_password_hash
```

---

### Insert Sample Expenses

Insert:

- 8 sample expenses
- Linked to demo user
- Multiple categories
- Current month dates
- At least one entry per category

---

# app.py Changes

## Import Functions

```python
from database.db import get_db, init_db, seed_db
```

---

## Initialize Database on Startup

Inside application startup:

```python
with app.app_context():
    init_db()
    seed_db()
```

This ensures:

- tables exist before routes run
- demo data is available immediately

---

# Files to Modify

## Update

- `database/db.py`
- `app.py`

---

# Files to Create

None.

---

# Dependencies

No new packages are required.

Use only:

- `sqlite3`
- `werkzeug.security`

---

# Fixed Expense Categories

Use exactly these category values:

- Food
- Transport
- Bills
- Health
- Entertainment
- Shopping
- Other

---

# Implementation Rules

## Database Rules

- No ORM usage
- No SQLAlchemy
- SQLite only

---

## Query Rules

Use parameterized queries exclusively.

Correct:

```python
cursor.execute(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    (name, email)
)
```

Incorrect:

```python
cursor.execute(
    f"INSERT INTO users VALUES ('{name}')"
)
```

---

## Foreign Key Rules

Enable on every connection:

```python
PRAGMA foreign_keys = ON
```

---

## Password Rules

Passwords must be hashed.

Required import:

```python
from werkzeug.security import generate_password_hash
```

---

## Amount Rules

- Store amounts as REAL
- Never INTEGER

---

## Date Rules

Use consistent format:

```text
YYYY-MM-DD
```

---

# Expected Behavior

## get_db()

Returns a connection with:

- sqlite3.Row support
- foreign key enforcement enabled

---

## init_db()

- Creates tables safely
- Works on repeated executions

---

## seed_db()

- Inserts data only once
- Never duplicates records

---

## Database Constraints

The database must enforce:

- UNIQUE email addresses
- Valid foreign key relationships

---

# Error Handling Expectations

## Duplicate Email

Attempting to insert duplicate emails should fail with:

- UNIQUE constraint error

---

## Invalid user_id

Attempting to insert expenses with invalid users should fail with:

- FOREIGN KEY constraint error

---

## Invalid Queries

Errors should remain visible for debugging purposes.

Do not silently suppress exceptions.

---

# Definition of Done

- [ ] Database file created automatically on startup
- [ ] users table exists with correct schema
- [ ] expenses table exists with correct schema
- [ ] Demo user inserted successfully
- [ ] Demo password stored as hash
- [ ] 8 sample expenses inserted
- [ ] Seed process does not duplicate data
- [ ] App starts without database errors
- [ ] Foreign key enforcement works
- [ ] All queries use parameterized SQL
