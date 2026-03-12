from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Job, User, Application
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import secrets
import string
import os
import uuid


def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


recruiter_bp = Blueprint('recruiter', __name__, url_prefix="/recruiter")


# ===============================
# RECRUITER DASHBOARD
# ===============================
@recruiter_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()

    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()

    return render_template(
        'recruiter/recruiter_profile.html',
        jobs=jobs,
        hrs=hrs
    )


# ===============================
# POST JOB
# ===============================
@recruiter_bp.route('/post-job', methods=['POST'])
@login_required
def post_job():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    title = request.form['title']
    description = request.form['description']
    field = request.form.get('field')
    job_type = request.form.get('job_type')
    location = request.form.get('location')
    salary = request.form.get('salary')
    expiration_date = request.form.get('expiration_date')

    poster_file = request.files.get('poster')

    poster_filename = None

    # ===============================
    # CREATE UPLOAD FOLDER IF MISSING
    # ===============================
    upload_folder = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # ===============================
    # SAVE POSTER IMAGE
    # ===============================
    if poster_file and poster_file.filename != "":

        filename = secure_filename(poster_file.filename)

        # prevent duplicate filenames
        unique_name = f"{uuid.uuid4()}_{filename}"

        poster_path = os.path.join(upload_folder, unique_name)

        poster_file.save(poster_path)

        poster_filename = unique_name

    # ===============================
    # HANDLE EXPIRATION DATE
    # ===============================
    expiration = None
    if expiration_date:
        expiration = datetime.strptime(expiration_date, "%Y-%m-%d")

    job = Job(
        title=title,
        description=description,
        company_id=current_user.id,
        field=field,
        job_type=job_type,
        location=location,
        salary=salary,
        poster=poster_filename,
        expiration_date=expiration
    )

    db.session.add(job)
    db.session.commit()

    flash("Job posted successfully!", "success")

    return redirect(url_for('recruiter.job_posting'))


# ===============================
# CREATE HR ACCOUNT
# ===============================
@recruiter_bp.route('/create-hr', methods=['POST'])
@login_required
def create_hr():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    username = request.form['username']
    email = request.form['email']

    temp_password = generate_temp_password()

    hashed_password = generate_password_hash(temp_password)

    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    if User.query.filter_by(email=email).first():
        flash("Email already exists!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    hr_user = User(
        username=username,
        email=email,
        password=hashed_password,
        role='hr',
        created_by=current_user.id,
        must_change_password=True
    )

    db.session.add(hr_user)
    db.session.commit()

    hrs = User.query.filter_by(
        created_by=current_user.id,
        role="hr"
    ).all()

    return render_template(
        "recruiter/hr_accounts.html",
        hrs=hrs,
        temp_password=temp_password
    )


# ===============================
# SCHEDULE INTERVIEW
# ===============================
@recruiter_bp.route('/schedule-interview/<int:app_id>', methods=['POST'])
@login_required
def schedule_interview(app_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    date_time = request.form['datetime']

    application = Application.query.get_or_404(app_id)

    application.remarks = f"Interview Scheduled: {date_time}"

    db.session.commit()

    flash("Interview scheduled successfully!", "success")

    return redirect(url_for('recruiter.dashboard'))


# ===============================
# UPDATE APPLICATION STATUS
# ===============================
@recruiter_bp.route('/update-application/<int:app_id>', methods=['POST'])
@login_required
def update_application(app_id):

    if current_user.role != "recruiter":
        flash("Access denied", "danger")
        return redirect(url_for("auth.index"))

    application = Application.query.get_or_404(app_id)

    status = request.form.get("status")
    remarks = request.form.get("remarks")

    application.status = status
    application.remarks = remarks

    db.session.commit()

    flash("Application updated.", "success")

    return redirect(url_for("recruiter.dashboard"))


# ===============================
# JOB POSTING PAGE
# ===============================
@recruiter_bp.route('/job-posting')
@login_required
def job_posting():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()

    return render_template(
        "recruiter/job_posting.html",
        jobs=jobs
    )


# ===============================
# HR ACCOUNTS PAGE
# ===============================
@recruiter_bp.route('/hr-accounts')
@login_required
def hr_accounts():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    hrs = User.query.filter_by(
        created_by=current_user.id,
        role="hr"
    ).all()

    return render_template(
        "recruiter/hr_accounts.html",
        hrs=hrs
    )

@recruiter_bp.route('/review-applications')
@login_required
def review_applications():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Get applications for jobs posted by this recruiter
    applications = Application.query.join(Application.job).filter_by(
        company_id=current_user.id
    ).all()

    return render_template(
        "recruiter/review_applications.html",
        applications=applications
    )


@recruiter_bp.route('/review/<int:app_id>', methods=['POST'])
@login_required
def review_application(app_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)

    status = request.form['status']
    remarks = request.form['remarks']

    application.status = status
    application.remarks = remarks

    db.session.commit()

    flash("Application reviewed successfully!", "success")

    return redirect(url_for('recruiter.review_applications'))