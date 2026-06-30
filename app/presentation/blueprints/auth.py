"""Authentication blueprint."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.application.services.audit_service import ActivityService, AuditService
from app.application.services.auth_service import AuthenticationService
from app.domain.exceptions.domain_exceptions import ValidationError

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        try:
            user, token = AuthenticationService().register(
                request.form.get("username", ""),
                request.form.get("email", ""),
                request.form.get("password", ""),
            )
            flash(f"Account created. Mock email verification token: {token}", "success")
            AuditService().record(actor_id=user.id, action="auth.register", resource_type="user")
            return redirect(url_for("auth.login"))
        except ValidationError as exc:
            flash(str(exc), "error")
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        try:
            user = AuthenticationService().authenticate(
                request.form.get("identifier", ""),
                request.form.get("password", ""),
                remember=request.form.get("remember") == "on",
            )
            ActivityService().record(owner_id=user.id, action="login", message="Logged in")
            AuditService().record(actor_id=user.id, action="auth.login", resource_type="user")
            return redirect(request.args.get("next") or url_for("dashboard.index"))
        except ValidationError as exc:
            AuditService().record(
                actor_id=None,
                action="auth.login_failed",
                resource_type="user",
                outcome="failure",
                metadata={"identifier": request.form.get("identifier", "")},
            )
            flash(str(exc), "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    ActivityService().record(owner_id=current_user.id, action="logout", message="Logged out")
    AuditService().record(actor_id=current_user.id, action="auth.logout", resource_type="user")
    AuthenticationService().logout()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    token = None
    if request.method == "POST":
        token = AuthenticationService().request_password_reset(request.form.get("email", ""))
        flash("If that email exists, a reset token was generated locally.", "info")
    return render_template("auth/forgot_password.html", token=token)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        ok = AuthenticationService().reset_password(
            request.form.get("token", ""), request.form.get("password", "")
        )
        flash("Password reset complete." if ok else "Invalid or expired token.", "success" if ok else "error")
        if ok:
            return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html")


@auth_bp.route("/verify-email/<token>")
def verify_email(token: str):
    ok = AuthenticationService().verify_email(token)
    flash("Email verified." if ok else "Invalid or expired verification token.", "success" if ok else "error")
    return redirect(url_for("auth.login"))

