from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Job, Application, User
from werkzeug.utils import secure_filename
from PIL import Image
import base64
import io
import os
import uuid

applicant_bp = Blueprint('applicant', __name__, url_prefix="/applicant")

# ===============================
# APPLICANT PROFILE
# ===============================
@applicant_bp.route('/profile')
@login_required
def profile():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    return render_template('applicant/profile.html')


# ===============================
# UPLOAD PROFILE PICTURE
# ===============================
@applicant_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    cropped_data = request.form.get('cropped_image')

    if not cropped_data:
        flash("No image data received.", "danger")
        return redirect(url_for('applicant.profile'))

    try:
        # Strip the base64 header: "data:image/jpeg;base64,..."
        header, encoded = cropped_data.split(',', 1)
        image_data = base64.b64decode(encoded)

        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        # Enforce square + resize to 400x400
        image = image.resize((400, 400), Image.LANCZOS)

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
        os.makedirs(upload_folder, exist_ok=True)

        # ✅ FIXED: skip deletion if old picture is a Google URL (starts with http)
        if current_user.profile_picture and not current_user.profile_picture.startswith('http'):
            old_path = os.path.join(upload_folder, current_user.profile_picture)
            if os.path.exists(old_path):
                os.remove(old_path)

        filename = f"pfp_{current_user.id}_{uuid.uuid4().hex[:8]}.jpg"
        image.save(os.path.join(upload_folder, filename), 'JPEG', quality=90)

        current_user.profile_picture = filename
        db.session.commit()

        flash("Profile picture updated!", "success")

    except Exception as e:
        flash(f"Upload failed: {str(e)}", "danger")

    return redirect(url_for('applicant.profile'))


# ===============================
# APPLICANT DASHBOARD
# ===============================
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
        'applicant/dashboard.html',
        jobs=jobs,
        applications=applications
    )


# ===============================
# JOB DETAILS
# ===============================
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
# APPLY FOR JOB
# ===============================
@applicant_bp.route('/apply/<int:job_id>', methods=["GET", "POST"])
@login_required
def apply_job(job_id):

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Prevent unverified users
    if not current_user.is_verified:
        flash("Your account is still waiting for admin verification.", "warning")
        return redirect(url_for('applicant.dashboard'))

    job = Job.query.get_or_404(job_id)

    # Prevent duplicate applications
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

            # ✅ CORRECT: resumes saved to applicant_resumes/ subfolder
            upload_folder = os.path.join(
                current_app.root_path,
                "static", "uploads", "applicant_resumes"
            )

            os.makedirs(upload_folder, exist_ok=True)

            # Secure + unique filename
            filename = secure_filename(resume_file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"

            resume_path = os.path.join(upload_folder, unique_filename)

            resume_file.save(resume_path)

            resume_filename = unique_filename

        # Save application
        application = Application(
            applicant_id=current_user.id,
            job_id=job_id,
            resume=resume_filename,
            cover_letter=cover_letter
        )

        db.session.add(application)
        db.session.commit()

        flash("Application submitted successfully!", "success")

        return redirect(url_for('applicant.dashboard'))

    return render_template(
        "applicant/apply_job.html",
        job=job
    )