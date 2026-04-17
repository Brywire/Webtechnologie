from extensions import db
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from models import User
from werkzeug.security import check_password_hash, generate_password_hash


def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Vul alle verplichte velden in.", "error")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Wachtwoorden komen niet overeen.", "error")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Wachtwoord moet minimaal 6 tekens zijn.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("Deze gebruikersnaam is al in gebruik.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Dit e-mailadres is al in gebruik.", "error")
            return redirect(url_for("register"))

        new_user = User(
            username=username, email=email, password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account aangemaakt! Je kunt nu inloggen.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Gebruikersnaam of wachtwoord klopt niet.", "error")
            return redirect(url_for("login"))

        login_user(user)
        flash(f"Welkom terug, {user.username}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@login_required
def logout():
    logout_user()
    flash("Je bent uitgelogd.", "success")
    return redirect(url_for("login"))
