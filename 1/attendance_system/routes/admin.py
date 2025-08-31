from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models.user import User
from app import db, login_manager

auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("✅ Logged in successfully!", "success")

            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "teacher":
                return redirect(url_for("teacher.dashboard"))
            elif user.role == "student":
                return redirect(url_for("student.dashboard"))
        else:
            flash("❌ Invalid credentials", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for("auth.login"))
