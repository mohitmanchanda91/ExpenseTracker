# 01 — Database Setup

## Context

The Spendly Flask app (`/Users/phonato-mohit/Claude_projects/expense-tracker`) currently runs on port 5001 with placeholder routes that render templates but have no persistence. `database/db.py` is a comment-only stub and `app.py` has no DB wiring. This step implements the SQLite foundation that every subsequent feature (auth, profile, expenses, reporting) depends on, per `Claude/Specs/01-database-setup.md`. Outcome: app starts, creates `spendly.db` automatically, runs idempotently, and has a demo user with 8 sample expenses ready for development.

## Scope

Two files modified, no files created, no new dependencies.

- **Modify** `database/db.py` — implement `get_db()`, `init_db()`, `seed_db()`
- **Modify** `app.py` — import the three helpers and call `init_db()` + `seed_db()` once on startup

Stack: `sqlite3` (stdlib), `werkzeug.security.generate_password_hash` (already in `requirements.txt`). No ORM. Raw parameterized SQL only.

---

## File 1 — `database/db.py`

### Module-level

- `import sqlite3`
- `from werkzeug.security import generate_password_hash`
- `DATABASE = "spendly.db"` — chosen over `expense_tracker.db` (spec allows either; matches product name and is shorter). Stored at repo root because that's where `python app.py` runs from.

### `get_db()`

- `conn = sqlite3.connect(DATABASE)`
- `conn.row_factory = sqlite3.Row` — dict-style row access
- `conn.execute("PRAGMA foreign_keys = ON")` — must be set **per connection**; SQLite doesn't persist this pragma
- `return conn`

### `init_db()`

- Open a connection via `get_db()`, use a `with conn:` block so commits/rollbacks are automatic, close in `finally`.
- Two `CREATE TABLE IF NOT EXISTS` statements, schema exactly per spec:

  **users**
  ```sql
  CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now'))
  );
  ```

  **expenses**
  ```sql
  CREATE TABLE IF NOT EXISTS expenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      amount REAL NOT NULL,
      category TEXT NOT NULL,
      date TEXT NOT NULL,
      description TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (user_id) REFERENCES users(id)
  );
  ```

- Idempotent — safe to call on every startup.

### `seed_db()`

1. Open a connection via `get_db()`.
2. Guard against duplicate seeding:
   ```python
   count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
   if count > 0:
       conn.close()
       return
   ```
3. Insert demo user with **parameterized** query:
   - `name="Demo User"`, `email="demo@spendly.com"`
   - `password_hash = generate_password_hash("demo123")`
   - Capture `cursor.lastrowid` for `user_id`.
4. Insert **8 expenses** linked to that `user_id` via `executemany` with parameter tuples. Dates use the current month (May 2026) in `YYYY-MM-DD` format. All 7 spec categories covered (Food appears twice):

   | amount | category | date | description |
   |---|---|---|---|
   | 12.50 | Food | 2026-05-01 | Coffee and pastry |
   | 45.00 | Transport | 2026-05-02 | Monthly metro pass |
   | 89.99 | Bills | 2026-05-03 | Internet bill |
   | 30.00 | Health | 2026-05-04 | Pharmacy |
   | 18.00 | Entertainment | 2026-05-05 | Movie ticket |
   | 64.20 | Shopping | 2026-05-06 | Running shoes |
   | 25.00 | Other | 2026-05-07 | Birthday gift |
   | 22.75 | Food | 2026-05-08 | Team lunch |

5. `conn.commit()`, `conn.close()`.

### Implementation rules (from spec)

- No ORM, no SQLAlchemy.
- Every query parameterized (`?` placeholders, never f-strings).
- Errors propagate — do not wrap in bare `try/except` that swallows exceptions.

---

## File 2 — `app.py`

Two changes, both at the top of the file, after `app = Flask(__name__)` and **before** the route definitions:

```python
from database.db import get_db, init_db, seed_db

with app.app_context():
    init_db()
    seed_db()
```

Placed at module scope (not inside `if __name__ == "__main__":`) so the DB is initialized regardless of whether the app is started via `python app.py` or `flask run`. The existing routes and the `__main__` block remain unchanged.

`get_db` is imported now even though `app.py` doesn't use it yet — subsequent steps (auth, expenses) will, and the spec lists it in the import line. Acceptable because it's a real, used symbol within the next step or two; if preferred, it can be dropped to `from database.db import init_db, seed_db` and re-added later. **Decision: follow spec verbatim and import all three.**

---

## Critical files

- `/Users/phonato-mohit/Claude_projects/expense-tracker/database/db.py` — replace stub
- `/Users/phonato-mohit/Claude_projects/expense-tracker/app.py` — add import + startup block
- `/Users/phonato-mohit/Claude_projects/expense-tracker/Claude/Specs/01-database-setup.md` — source of truth (read-only)

---

## Existing utilities to reuse

None — this is the first persistence layer; nothing pre-exists to reuse. `database/__init__.py` already exists (empty) so `from database.db import ...` works without further changes.

---

## Verification

Run from repo root with the project venv activated (per memory: `source venv/bin/activate && ...` or use `venv/bin/python` directly).

1. **Cold start creates DB and seeds**
   ```bash
   rm -f spendly.db
   venv/bin/python app.py &
   sleep 2 && curl -s http://localhost:5001/ -o /dev/null -w "%{http_code}\n"
   # expect 200, and spendly.db now exists
   ```

2. **Schema is correct**
   ```bash
   sqlite3 spendly.db ".schema users"
   sqlite3 spendly.db ".schema expenses"
   ```
   Confirm columns, types, UNIQUE on `email`, FOREIGN KEY on `expenses.user_id`.

3. **Seed inserted exactly once**
   ```bash
   sqlite3 spendly.db "SELECT COUNT(*) FROM users;"      # 1
   sqlite3 spendly.db "SELECT COUNT(*) FROM expenses;"   # 8
   sqlite3 spendly.db "SELECT DISTINCT category FROM expenses;"  # all 7 categories
   ```

4. **Idempotency** — restart the app; counts above must remain 1 and 8 (no duplicates).

5. **Password is hashed**
   ```bash
   sqlite3 spendly.db "SELECT password_hash FROM users WHERE email='demo@spendly.com';"
   ```
   Confirm it starts with `scrypt:` or `pbkdf2:` (Werkzeug default), not the literal `demo123`.

6. **Foreign key enforcement**
   ```bash
   sqlite3 spendly.db "PRAGMA foreign_keys = ON; INSERT INTO expenses (user_id, amount, category, date) VALUES (999, 1.0, 'Food', '2026-05-01');"
   ```
   Expect `FOREIGN KEY constraint failed`.

7. **UNIQUE email**
   ```bash
   sqlite3 spendly.db "INSERT INTO users (name, email, password_hash) VALUES ('Dup', 'demo@spendly.com', 'x');"
   ```
   Expect `UNIQUE constraint failed: users.email`.

8. **Tear down** — stop the background app process when verification is done.

---

## Definition of done (mirrors spec checklist)

- [ ] `spendly.db` is created automatically on first startup
- [ ] `users` and `expenses` tables match the spec schema
- [ ] Demo user inserted; password stored as a Werkzeug hash
- [ ] 8 sample expenses inserted, covering all 7 categories
- [ ] Re-running `seed_db()` does not duplicate data
- [ ] App starts cleanly without DB errors
- [ ] Foreign key enforcement and UNIQUE email both raise as expected
- [ ] All queries use `?` parameter binding

---

## Note on plan file location

In plan mode I can only write to this designated plan file. The user asked for the plan at `claude/plans/01-database-setup.md` in the repo. On approval, the **first execution step** will be to copy this file to `/Users/phonato-mohit/Claude_projects/expense-tracker/claude/plans/01-database-setup.md` (creating the directory) so the plan lives next to the spec.
