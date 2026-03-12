from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, RecruiterProfile, Job
import os
import uuid

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


auth_bp = Blueprint('auth', __name__)


# =========================
# Home Page
# =========================
@auth_bp.route('/')
def index():
    return render_template('home.html')

@auth_bp.route('/jobs')
def jobs():
    jobs = Job.query.all()
    return render_template('index.html', jobs=jobs)

@auth_bp.route("/help")
def help_page():
    return render_template("help.html")

# =========================
# Login
# =========================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            # 🚫 BLOCK REJECTED RECRUITERS
            if user.role == "recruiter" and user.verification_status == "Rejected":
                return render_template(
                    "account_rejected.html",
                    user=user
                )

            # ⚠️ BLOCK PENDING RECRUITERS
            if user.role == "recruiter" and user.verification_status == "Pending":
                flash("Your recruiter account is still pending admin verification.", "warning")
                return redirect(url_for("auth.login"))

            login_user(user)

            flash("Logged in successfully", "success")

            if user.role == "applicant":
                return redirect(url_for('applicant.dashboard'))

            elif user.role == "recruiter":
                return redirect(url_for('recruiter.dashboard'))

            elif user.role == "hr":
                return redirect(url_for('hr.dashboard'))

            elif user.role == "admin":
                return redirect(url_for('admin.dashboard'))

        flash("Invalid email or password", "danger")

    return render_template('auth/login.html')


# =========================
# Register
# =========================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        role = request.form.get('role')
        username = request.form.get('username')
        email = request.form.get('email')
        password_raw = request.form.get('password')

        if role not in ['applicant', 'recruiter']:
            flash("Invalid role", "danger")
            return redirect(url_for('auth.register'))

        if not username:
            username = email.split('@')[0]

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('auth.register'))

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

        # =========================
        # Recruiter Profile Section
        # =========================
        if role == "recruiter":

            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            company_logo = request.files.get('company_logo')
            company_proof = request.files.get('company_proof')

            logo_filename = None
            proof_filename = None

            if company_logo and company_logo.filename:

                logo_filename = f"{uuid.uuid4()}_{secure_filename(company_logo.filename)}"
                logo_path = os.path.join(upload_folder, logo_filename)

                company_logo.save(logo_path)

            if company_proof and company_proof.filename:

                proof_filename = f"{uuid.uuid4()}_{secure_filename(company_proof.filename)}"
                proof_path = os.path.join(upload_folder, proof_filename)

                company_proof.save(proof_path)

            profile = RecruiterProfile(
                user_id=user.id,
                surname=request.form.get('surname') or "",
                first_name=request.form.get('first_name') or "",
                middle_name=request.form.get('middle_name') or "",
                phone_number=request.form.get('phone_number') or "",
                company_name=request.form.get('company_name') or "",
                company_industry=request.form.get('company_industry') or "",
                company_description=request.form.get('company_description') or "",
                company_address=request.form.get('company_address') or "",
                country=request.form.get('country') or "",
                city=request.form.get('city') or "",
                office_address=request.form.get('office_address') or "",
                company_email_domain=request.form.get('company_email_domain') or "",
                company_logo=logo_filename,
                company_proof=proof_filename
            )

            db.session.add(profile)
            db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# =========================
# Account Rejected Page
# =========================
@auth_bp.route('/account-rejected/<int:user_id>')
def account_rejected(user_id):

    user = User.query.get_or_404(user_id)

    return render_template(
        'account_rejected.html',
        user=user
    )


# =========================
# Logout
# =========================
@auth_bp.route('/logout')
@login_required
def logout():

    logout_user()

    flash("Logged out successfully", "info")

    return redirect(url_for('auth.index'))