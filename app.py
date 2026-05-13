import os
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id") is not None:
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id") is not None:
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _validate_registration(name, email, password)
    if error:
        return render_template("register.html", error=error, name=name, email=email)

    conn = get_db()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
    except sqlite3.IntegrityError:
        return render_template(
            "register.html",
            error="An account with that email already exists.",
            name=name,
            email=email,
        )
    finally:
        conn.close()

    return redirect(url_for("login"))


def _validate_registration(name, email, password):
    if not name:
        return "Please enter your name."
    if len(name) > 100:
        return "Name must be 100 characters or fewer."
    if not email:
        return "Please enter your email."
    at = email.find("@")
    if at < 1 or "." not in email[at + 1:] or len(email) > 254:
        return "Please enter a valid email address."
    if not password:
        return "Please enter a password."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") is not None:
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email:
        return render_template("login.html", error="Please enter your email.", email=email)
    if not password:
        return render_template("login.html", error="Please enter your password.", email=email)

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if row is None or not check_password_hash(row["password_hash"], password):
        return render_template(
            "login.html",
            error="Invalid email or password.",
            email=email,
        )

    session["user_id"] = row["id"]
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    user = {
        "name": row["name"],
        "email": row["email"],
        "initials": _initials(row["name"]),
        "member_since": _format_member_since(row["created_at"]),
    }

    stats = {
        "total_spent": "₹4,820.45",
        "transaction_count": 28,
        "top_category": "Food",
    }

    transactions = [
        {"date": "May 11", "description": "Team lunch", "category": "Food", "amount": "₹22.75"},
        {"date": "May 10", "description": "Birthday gift", "category": "Other", "amount": "₹25.00"},
        {"date": "May 09", "description": "Running shoes", "category": "Shopping", "amount": "₹64.20"},
        {"date": "May 08", "description": "Movie ticket", "category": "Entertainment", "amount": "₹18.00"},
        {"date": "May 07", "description": "Pharmacy", "category": "Health", "amount": "₹30.00"},
        {"date": "May 06", "description": "Internet bill", "category": "Bills", "amount": "₹89.99"},
        {"date": "May 05", "description": "Metro pass", "category": "Transport", "amount": "₹45.00"},
        {"date": "May 04", "description": "Coffee and pastry", "category": "Food", "amount": "₹12.50"},
    ]

    categories = [
        {"name": "Food", "slug": "food", "total": "₹1,420.30", "percent": 32},
        {"name": "Shopping", "slug": "shopping", "total": "₹1,080.50", "percent": 24},
        {"name": "Bills", "slug": "bills", "total": "₹890.00", "percent": 20},
        {"name": "Transport", "slug": "transport", "total": "₹620.00", "percent": 14},
        {"name": "Entertainment", "slug": "entertainment", "total": "₹450.00", "percent": 10},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


def _initials(name):
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _format_member_since(created_at):
    if not created_at:
        return ""
    try:
        return datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except ValueError:
        return created_at


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
