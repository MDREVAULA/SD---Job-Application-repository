from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Job, User, Application
from werkzeug.security import generate_password_hash
import secrets
import string

def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

recruiter_bp = Blueprint('recruiter', __name__, url_prefix="/recruiter")


@recruiter_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Jobs posted by this recruiter
    jobs = Job.query.filter_by(company_id=current_user.id).all()

    # HR accounts created by this recruiter
    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()

    return render_template(
        'recruiter/recruiter_profile.html',
        jobs=jobs,
        hrs=hrs
    )


@recruiter_bp.route('/post-job', methods=['POST'])
@login_required
def post_job():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Only approved recruiters can post
    if current_user.verification_status != "Approved":
        flash("Your recruiter account is not verified.", "danger")
        return redirect(url_for('recruiter.dashboard'))

    title = request.form['title']
    description = request.form['description']

    job = Job(
        title=title,
        description=description,
        company_id=current_user.id
    )

    db.session.add(job)
    db.session.commit()

    flash("Job posted successfully!", "success")

    return redirect(url_for('recruiter.dashboard'))


@recruiter_bp.route('/create-hr', methods=['POST'])
@login_required
def create_hr():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    username = request.form['username']
    email = request.form['email']

    # Generate automatic temporary password
    temp_password = generate_temp_password()

    hashed_password = generate_password_hash(temp_password)

    # Check duplicate username
    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    # Check duplicate email
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


@recruiter_bp.route('/schedule-interview/<int:app_id>', methods=['POST'])
@login_required
def schedule_interview(app_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    date_time = request.form['datetime']

    application = Application.query.get(app_id)

    application.remarks = f"Interview Scheduled: {date_time}"

    db.session.commit()

    flash("Interview scheduled successfully!", "success")

    return redirect(url_for('recruiter.dashboard'))

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