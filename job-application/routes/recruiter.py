from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Job, User, Application
from werkzeug.security import generate_password_hash

recruiter_bp = Blueprint('recruiter', __name__, url_prefix="/recruiter")

@recruiter_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()
    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()
    return render_template('recruiter_dashboard.html', jobs=jobs, hrs=hrs)

@recruiter_bp.route('/post-job', methods=['POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter' or not current_user.is_verified:
        flash("Access denied or not verified!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    title = request.form['title']
    description = request.form['description']

    job = Job(title=title, description=description, company_id=current_user.id)
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
    password = generate_password_hash(request.form['password'])

    # ✅ Check duplicate username
    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        flash("Username already exists!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    # ✅ Check duplicate email
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        flash("Email already exists!", "danger")
        return redirect(url_for('recruiter.dashboard'))

    hr_user = User(
        username=username,
        email=email,
        password=password,
        role='hr',
        created_by=current_user.id
    )

    db.session.add(hr_user)
    db.session.commit()

    flash("HR account created successfully!", "success")
    return redirect(url_for('recruiter.dashboard'))

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