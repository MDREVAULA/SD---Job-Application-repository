from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    # Guest homepage — show jobs to anyone
    from models import Job
    jobs = Job.query.all()
    return render_template('index.html', jobs=jobs)

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully", "success")
            # Redirect based on role
            if user.role == "applicant":
                return redirect(url_for('applicant.dashboard'))
            elif user.role == "recruiter":
                return redirect(url_for('recruiter.dashboard'))
            elif user.role == "hr":
                return redirect(url_for('hr.dashboard'))
            elif user.role == "admin":
                return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid email or password", "danger")
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']  # Only Applicant or Recruiter
        if role not in ['applicant', 'recruiter']:
            flash("Invalid role", "danger")
            return redirect(url_for('auth.register'))

        # Check email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already exists", "danger")
            return redirect(url_for('auth.register'))

        # ✅ Check username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash("Username already exists", "danger")
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            email=email,
            password=password,
            role=role,
            is_verified=False
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('auth.index'))