import os
from functools import wraps
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

auth_bp = Blueprint("auth", __name__)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD not set in environment")


# -----------------------------
# Decorators
# -----------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "role" not in session:
            return redirect(url_for("auth.role_select"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return decorated


# -----------------------------
# Role Selection
# -----------------------------

@auth_bp.route("/", methods=["GET"])
def role_select():
    return render_template("role.html")


# -----------------------------
# Admin Login
# -----------------------------

@auth_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["role"] = "admin"
            return redirect("/admin/dashboard")

        return render_template(
            "admin_login.html",
            error="Wrong password"
        )

    return render_template("admin_login.html")


# -----------------------------
# Student Entry
# -----------------------------

@auth_bp.route("/student")
def student_entry():
    session["role"] = "user"
    return redirect("/dashboard")


# -----------------------------
# Logout
# -----------------------------

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.role_select"))
