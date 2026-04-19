from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Message
from authlib.integrations.flask_client import OAuth

from models import db, User, RecruiterProfile, Job, ApplicantProfile

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
        return redirect(url_for("applicant.profile"))
    if user.role == "recruiter":
        return redirect(url_for("recruiter.profile"))
    if user.role == "hr":
        return redirect(url_for("hr.profile"))
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("auth.index"))


# =========================
# SEND VERIFICATION EMAIL
# =========================
def send_verification_email(user):
    """Send verification email to recruiters after admin approval."""
    try:
        from app import mail

        if user.role == "recruiter":
            subject = "Your Recruiter Account Has Been Verified – Job Portal"
            body = f"""Hello {user.username},

Great news! Your recruiter account has been reviewed and approved by our admin team.

You can now log in and start posting jobs at: http://127.0.0.1:5000/login

Welcome to Job Portal!

– The Job Portal Team"""
        else:
            return

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=body
        )
        mail.send(msg)

    except Exception as e:
        print(f"Failed to send verification email to {user.email}: {e}")


# =========================
# PUBLIC PAGES
# =========================
@auth_bp.route("/")
def index():
    return render_template("home.html")


@auth_bp.route("/jobs")
def jobs():
    from models import SavedJob
    
    try:
        jobs = Job.query.filter(
            (Job.expiration_date == None) | (Job.expiration_date >= date.today())
        ).all()
    except:
        jobs = Job.query.all()

    saved_job_ids = set()
    if current_user.is_authenticated and current_user.role == 'applicant':
        saved_job_ids = {
            s.job_id for s in SavedJob.query.filter_by(applicant_id=current_user.id).all()
        }

    return render_template("index.html", jobs=jobs, saved_job_ids=saved_job_ids)


@auth_bp.route("/help")
def help_page():
    return render_template("help.html")

@auth_bp.route("/about")
def about():
    return render_template("about.html")

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
            flash("Invalid email or password", "info")
            return redirect(url_for("auth.login"))

        # Block admin from using the public login page
        if user.role == "admin":
            flash("Invalid email or password", "info")
            return redirect(url_for("auth.login"))

        # Google-only account trying to use password login
        if user.google_id and not user.password:
            flash("This account uses Google sign-in. Please use the 'Sign in with Google' button.", "info")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user.password, password):
            flash("Invalid email or password", "login_error")
            return redirect(url_for("auth.login"))

        # ── Ban check (all roles) ──
        if user.is_banned:
            return render_template("account_banned.html", user=user)

        # ── RECRUITERS: pending/rejected checks ──
        if user.role == "recruiter":
            profile = user.recruiter_profile
            if profile and profile.submitted_for_review and user.verification_status == "Pending":
                flash("Your recruiter account is pending admin verification.", "login_warning")
                return redirect(url_for("auth.login"))
            if user.verification_status == "Rejected":
                return render_template("account_rejected.html", user=user)

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
    google_picture = info.get("picture")

    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        user = User.query.filter_by(email=email).first()

        if user:
            # Existing account — link Google to it
            if user.role == "admin":
                flash("Invalid login method.", "login_error")
                return redirect(url_for("auth.login"))

            user.google_id = google_id
            if google_picture and not user.profile_picture:
                user.profile_picture = google_picture
            db.session.commit()

        else:
            # Brand new Google user — ask for role selection
            session["google_id"] = google_id
            session["google_email"] = email
            session["google_name"] = name
            session["google_picture"] = google_picture

            return redirect(url_for("auth.google_role_select"))

    if user.role == "admin":
        flash("Invalid login method.", "login_error")
        return redirect(url_for("auth.login"))

    # ── Ban check ──
    if user.is_banned:
        return render_template("account_banned.html", user=user)

    # ── Recruiter checks ──
    if user.role == "recruiter":
        profile = user.recruiter_profile
        if profile and profile.submitted_for_review and user.verification_status == "Pending":
            flash("Your recruiter account is pending admin verification.", "login_warning")
            return redirect(url_for("auth.login"))
        if user.verification_status == "Rejected":
            return render_template("account_rejected.html", user=user)

    if google_picture and not user.profile_picture:
        user.profile_picture = google_picture
        db.session.commit()

    login_user(user)
    flash("Logged in with Google!", "success")
    return redirect_by_role(user)


# =========================
# GOOGLE ROLE SELECTION
# =========================
@auth_bp.route("/google-role-select", methods=["GET", "POST"])
def google_role_select():

    if not session.get("google_id"):
        flash("Session expired. Please try again.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        role = request.form.get("role")

        if role not in ["applicant", "recruiter"]:
            flash("Please select a valid role.", "error")
            return redirect(url_for("auth.google_role_select"))

        # Save role to session — don't create user yet
        session["google_role"] = role

        if role == "recruiter":
            flash("Please complete your company information to finish registration.", "info")
            return redirect(url_for("auth.google_recruiter_profile"))

        flash("Please complete your profile to finish registration.", "info")
        return redirect(url_for("auth.google_applicant_profile"))

    return render_template("auth/google_role_select.html")


# =========================
# GOOGLE APPLICANT PROFILE
# =========================
@auth_bp.route("/google-applicant-profile", methods=["GET", "POST"])
def google_applicant_profile():

    if not session.get("google_id"):
        flash("Session expired. Please try again.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        google_id = session.pop("google_id")
        email = session.pop("google_email")
        name = session.pop("google_name")
        google_picture = session.pop("google_picture", None)
        session.pop("google_role", None)

        # Create user
        user = User(
            username=name,
            email=email,
            google_id=google_id,
            role="applicant",
            verification_status="Approved",
            is_verified=True,
            profile_completed=False,
            profile_picture=google_picture
        )
        db.session.add(user)
        db.session.commit()

        dob_str = request.form.get("date_of_birth")
        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except:
                dob = None

        applicant_profile = ApplicantProfile(
            user_id=user.id,
            last_name=request.form.get("surname") or "",
            first_name=request.form.get("first_name") or "",
            middle_name=request.form.get("middle_name") or "",
            date_of_birth=dob,
            gender=request.form.get("gender") or "",
            phone_number=request.form.get("phone_number") or "",
            country=request.form.get("country") or "",
            city=request.form.get("city") or "",
            home_address=request.form.get("home_address") or "",
        )
        db.session.add(applicant_profile)
        db.session.commit()

        try:
            from routes.admin import push_admin_notif
            push_admin_notif(
                'account_request',
                f'New applicant account registered via Google: <strong>{user.username}</strong>',
                user_id=user.id
            )
        except:
            pass

        login_user(user)
        flash("Account created with Google! Welcome aboard.", "success")
        return redirect_by_role(user)

    return render_template("auth/google_applicant_profile.html")


# =========================
# GOOGLE RECRUITER PROFILE
# =========================
@auth_bp.route("/google-recruiter-profile", methods=["GET", "POST"])
def google_recruiter_profile():

    if not session.get("google_id"):
        flash("Session expired. Please try again.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        google_id = session.pop("google_id")
        email = session.pop("google_email")
        name = session.pop("google_name")
        google_picture = session.pop("google_picture", None)
        session.pop("google_role", None)

        # Create user
        user = User(
            username=name,
            email=email,
            google_id=google_id,
            role="recruiter",
            verification_status="Pending",
            is_verified=False,
            profile_completed=False,
            profile_picture=google_picture
        )
        db.session.add(user)
        db.session.commit()

        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "recruiter_documents")
        os.makedirs(upload_folder, exist_ok=True)

        logo_file = request.files.get("company_logo")
        proof_file = request.files.get("company_proof")

        logo_filename = save_uploaded_file(logo_file, upload_folder) if logo_file else None
        proof_filename = save_uploaded_file(proof_file, upload_folder) if proof_file else None

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

        try:
            from routes.admin import push_admin_notif
            push_admin_notif(
                'account_request',
                f'New recruiter account registered via Google: <strong>{user.username}</strong>',
                user_id=user.id
            )
        except:
            pass

        flash("Registration complete! Your account is pending admin verification.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/google_recruiter_profile.html")


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
            verification_status="Approved" if role == "applicant" else "Pending",
            is_verified=role == "applicant",
            profile_completed=False,
        )

        db.session.add(user)
        db.session.commit()

        try:
            from routes.admin import push_admin_notif
            push_admin_notif(
                'account_request',
                f'New {user.role} account registered: <strong>{user.username}</strong>',
                user_id=user.id
            )
        except:
            pass

        # =========================
        # APPLICANT
        # =========================
        if role == "applicant":
            dob_str = request.form.get("date_of_birth")
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                except:
                    dob = None

            applicant_profile = ApplicantProfile(
                user_id=user.id,
                last_name=request.form.get("surname") or "",
                first_name=request.form.get("first_name") or "",
                middle_name=request.form.get("middle_name") or "",
                date_of_birth=dob,
                gender=request.form.get("gender") or "",
                phone_number=request.form.get("phone_number") or "",
                country=request.form.get("country") or "",
                city=request.form.get("city") or "",
                home_address=request.form.get("home_address") or "",
            )
            db.session.add(applicant_profile)
            db.session.commit()

            login_user(user)
            flash("Account created! Complete your profile to unlock all features.", "success")
            return redirect_by_role(user)

        # =========================
        # RECRUITER
        # =========================
        if role == "recruiter":
            upload_folder = os.path.join(current_app.root_path, "static", "uploads", "recruiter_documents")
            os.makedirs(upload_folder, exist_ok=True)

            logo_file = request.files.get("company_logo")
            proof_file = request.files.get("company_proof")

            logo_filename = save_uploaded_file(logo_file, upload_folder) if logo_file else None
            proof_filename = save_uploaded_file(proof_file, upload_folder) if proof_file else None

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

            login_user(user)
            flash("Account created! Complete your company profile, then submit for admin verification.", "info")
            return redirect_by_role(user)

    return render_template("auth/register.html")


# =========================
# CHECK EMAIL/USERNAME AVAILABILITY
# =========================
@auth_bp.route("/check-availability", methods=["POST"])
def check_availability():
    data = request.get_json()

    email = data.get("email", "").strip()
    username = data.get("username", "").strip()

    email_taken = User.query.filter_by(email=email).first() is not None
    username_taken = User.query.filter_by(username=username).first() is not None

    return jsonify({
        "email_taken": email_taken,
        "username_taken": username_taken
    })


# =========================
# FORGOT PASSWORD
# =========================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user and user.google_id and not user.password:
            flash("This email is linked to a Google account. Please use 'Sign in with Google' instead.", "login_warning")
            return redirect(url_for("auth.login"))

        if user and user.password:
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
        else:
            flash("If that email is registered, a reset link has been sent.", "info")
            return redirect(url_for("auth.forgot_password"))

        flash("If that email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/forgot_password.html")


# =========================
# RESET PASSWORD
# =========================
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.reset_token_expiry:
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    expiry = user.reset_token_expiry.replace(tzinfo=None)
    if expiry < datetime.utcnow():
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