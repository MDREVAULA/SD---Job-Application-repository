from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Message
from authlib.integrations.flask_client import OAuth

from models import db, User, RecruiterProfile, Job

import os
import uuid
import secrets
from datetime import date, datetime, timedelta

auth_bp = Blueprint("auth", __name__)


# =========================
# CONFIG
# =========================
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "doc", "docx"}


# =========================
# HELPERS
# =========================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder):
    if file and file.filename:
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None


def redirect_by_role(user):
    if user.role == "applicant":
        return redirect(url_for("applicant.dashboard"))
    if user.role == "recruiter":
        return redirect(url_for("recruiter.dashboard"))
    if user.role == "hr":
        return redirect(url_for("hr.dashboard"))
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("auth.index"))


# =========================
# PUBLIC PAGES
# =========================
@auth_bp.route("/")
def index():
    return render_template("home.html")


@auth_bp.route("/jobs")
def jobs():
    try:
        jobs = Job.query.filter(
            (Job.expiration_date == None) | (Job.expiration_date >= date.today())
        ).all()
    except:
        jobs = Job.query.all()

    return render_template("index.html", jobs=jobs)


@auth_bp.route("/help")
def help_page():
    return render_template("help.html")


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Invalid email or password", "login_error")
            return redirect(url_for("auth.login"))

        # Google-only account trying to use password login
        if user.google_id and not user.password:
            flash("This account uses Google sign-in. Please use the 'Sign in with Google' button.", "login_warning")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user.password, password):
            flash("Invalid email or password", "login_error")
            return redirect(url_for("auth.login"))

        # Recruiter rejected
        if user.role == "recruiter" and user.verification_status == "Rejected":
            return render_template("account_rejected.html", user=user)

        # Recruiter pending
        if user.role == "recruiter" and user.verification_status == "Pending":
            flash("Your recruiter account is pending admin verification.", "login_warning")
            return redirect(url_for("auth.login"))

        login_user(user)

        # HR temporary password check
        if user.role == "hr" and user.must_change_password:
            flash("You must change your temporary password.", "hr_password_notice")
            return redirect(url_for("hr.change_password"))

        flash("Logged in successfully", "success")
        return redirect_by_role(user)

    return render_template("auth/login.html")


# =========================
# GOOGLE OAuth
# =========================
def get_oauth():
    from app import oauth
    return oauth


@auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return get_oauth().google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/google/callback")
def google_callback():
    token = get_oauth().google.authorize_access_token()
    info = token.get("userinfo")

    if not info:
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    google_id = info["sub"]
    email = info["email"]
    name = info.get("name", email.split("@")[0])

    # Check if user exists by Google ID
    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        # Check if email already registered manually
        user = User.query.filter_by(email=email).first()

        if user:
            # Link Google to existing account
            user.google_id = google_id
            db.session.commit()
        else:
            # Create brand new account
            user = User(
                username=name,
                email=email,
                google_id=google_id,
                role="applicant",
                verification_status="Approved",
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()

    # Block rejected recruiters
    if user.role == "recruiter" and user.verification_status == "Rejected":
        return render_template("account_rejected.html", user=user)

    # Block pending recruiters
    if user.role == "recruiter" and user.verification_status == "Pending":
        flash("Your recruiter account is pending admin verification.", "login_warning")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Logged in with Google!", "success")
    return redirect_by_role(user)


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        role = request.form.get("role")
        username = request.form.get("username")
        email = request.form.get("email")
        password_raw = request.form.get("password")

        if role not in ["applicant", "recruiter"]:
            flash("Invalid role", "register_error")
            return redirect(url_for("auth.register"))

        if not username:
            username = email.split("@")[0]

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "register_error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "register_error")
            return redirect(url_for("auth.register"))

        password = generate_password_hash(password_raw)

        user = User(
            username=username,
            email=email,
            password=password,
            role=role,
            verification_status="Pending"
        )

        db.session.add(user)
        db.session.commit()

        if role == "recruiter":

            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)

            logo_file = request.files.get("company_logo")
            proof_file = request.files.get("company_proof")

            logo_filename = save_uploaded_file(logo_file, upload_folder)
            proof_filename = save_uploaded_file(proof_file, upload_folder)

            profile = RecruiterProfile(
                user_id=user.id,
                surname=request.form.get("surname") or "",
                first_name=request.form.get("first_name") or "",
                middle_name=request.form.get("middle_name") or "",
                phone_number=request.form.get("phone_number") or "",
                company_name=request.form.get("company_name") or "",
                company_industry=request.form.get("company_industry") or "",
                company_description=request.form.get("company_description") or "",
                company_address=request.form.get("company_address") or "",
                country=request.form.get("country") or "",
                city=request.form.get("city") or "",
                office_address=request.form.get("office_address") or "",
                company_email_domain=request.form.get("company_email_domain") or "",
                company_logo=logo_filename,
                company_proof=proof_filename
            )

            db.session.add(profile)
            db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# =========================
# FORGOT PASSWORD
# =========================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user and user.password:  # only send if they have a password (not Google-only)
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()

            reset_url = url_for("auth.reset_password", token=token, _external=True)

            from app import mail
            msg = Message(
                subject="Reset Your Password – Job Portal",
                recipients=[email],
                body=f"Hello {user.username},\n\nClick the link below to reset your password. It expires in 30 minutes.\n\n{reset_url}\n\nIf you did not request this, ignore this email."
            )
            mail.send(msg)

        # Always show same message — don't reveal if email exists
        flash("If that email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/forgot_password.html")


# =========================
# RESET PASSWORD
# =========================
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("password")

        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


# =========================
# ACCOUNT REJECTED PAGE
# =========================
@auth_bp.route("/account-rejected/<int:user_id>")
def account_rejected(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("account_rejected.html", user=user)


# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("auth.index"))