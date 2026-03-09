from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Job, Application

applicant_bp = Blueprint('applicant', __name__, url_prefix="/applicant")


@applicant_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.all()

    applications = Application.query.filter_by(
        applicant_id=current_user.id
    ).all()

    return render_template(
        'applicant/applicant_dashboard.html',
        jobs=jobs,
        applications=applications
    )


@applicant_bp.route('/apply/<int:job_id>')
@login_required
def apply_job(job_id):

    # Prevent non-applicants
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # 🚨 Prevent unverified applicants from applying
    if not current_user.is_verified:
        flash("Your account is still waiting for admin verification.", "warning")
        return redirect(url_for('applicant.dashboard'))

    # Check if already applied
    existing = Application.query.filter_by(
        applicant_id=current_user.id,
        job_id=job_id
    ).first()

    if existing:
        flash("You already applied for this job!", "warning")

    else:
        application = Application(
            applicant_id=current_user.id,
            job_id=job_id
        )

        db.session.add(application)
        db.session.commit()

        flash("Application submitted successfully!", "success")

    return redirect(url_for('applicant.dashboard'))