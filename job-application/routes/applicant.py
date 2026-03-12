from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Job, Application, User
from werkzeug.utils import secure_filename
import os
import uuid

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


@applicant_bp.route('/job/<int:job_id>')
def job_details(job_id):

    job = Job.query.get_or_404(job_id)

    job_owner = User.query.get(job.company_id)

    return render_template(
        "applicant/job_details.html",
        job=job,
        job_owner=job_owner
    )


# ===============================
# APPLICATION FORM PAGE
# ===============================
@applicant_bp.route('/apply/<int:job_id>', methods=["GET", "POST"])
@login_required
def apply_job(job_id):

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if not current_user.is_verified:
        flash("Your account is still waiting for admin verification.", "warning")
        return redirect(url_for('applicant.dashboard'))

    job = Job.query.get_or_404(job_id)

    # prevent duplicate applications
    existing = Application.query.filter_by(
        applicant_id=current_user.id,
        job_id=job_id
    ).first()

    if existing:
        flash("You already applied for this job!", "warning")
        return redirect(url_for('applicant.dashboard'))

    # ===============================
    # SUBMIT APPLICATION
    # ===============================
    if request.method == "POST":

        cover_letter = request.form.get("cover_letter")
        resume_file = request.files.get("resume")

        resume_filename = None

        if resume_file and resume_file.filename != "":

            upload_folder = os.path.join(current_app.root_path, "static", "resumes")
            os.makedirs(upload_folder, exist_ok=True)

            filename = secure_filename(resume_file.filename)
            unique_name = f"{uuid.uuid4()}_{filename}"

            resume_file.save(os.path.join(upload_folder, unique_name))

            resume_filename = unique_name

        application = Application(
            applicant_id=current_user.id,
            job_id=job_id,
            resume=resume_filename,
            remarks=cover_letter
        )

        db.session.add(application)
        db.session.commit()

        flash("Application submitted successfully!", "success")

        return redirect(url_for('applicant.dashboard'))

    return render_template(
        "applicant/apply_job.html",
        job=job
    )