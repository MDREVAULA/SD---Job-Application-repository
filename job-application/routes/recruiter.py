from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Job, User, Application, JobImage
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import base64
import io
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
@recruiter_bp.route('/profile')
@login_required
def profile():
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()
    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()

    return render_template('recruiter/profile.html', jobs=jobs, hrs=hrs)


# ===============================
# UPLOAD PROFILE PICTURE
# ===============================
@recruiter_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    cropped_data = request.form.get('cropped_image')

    if not cropped_data:
        flash("No image data received.", "danger")
        return redirect(url_for('recruiter.profile'))

    try:
        header, encoded = cropped_data.split(',', 1)
        image_data = base64.b64decode(encoded)

        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image = image.resize((400, 400), Image.LANCZOS)

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
        os.makedirs(upload_folder, exist_ok=True)

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

    return redirect(url_for('recruiter.profile'))

# ===============================
# UPLOAD COMPANY LOGO
# ===============================
@recruiter_bp.route('/upload-company-logo', methods=['POST'])
@login_required
def upload_company_logo():
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    cropped_data = request.form.get('cropped_image')

    if not cropped_data:
        flash("No image data received.", "danger")
        return redirect(url_for('recruiter.profile'))

    try:
        header, encoded = cropped_data.split(',', 1)
        image_data = base64.b64decode(encoded)

        image = Image.open(io.BytesIO(image_data)).convert('RGBA')
        image.thumbnail((800, 800), Image.LANCZOS)

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'company_logos')
        os.makedirs(upload_folder, exist_ok=True)

        profile = current_user.recruiter_profile

        if profile is None:
            flash("Recruiter profile not found.", "danger")
            return redirect(url_for('recruiter.profile'))

        # Delete old logo if exists
        if profile.company_logo and not profile.company_logo.startswith('http'):
            old_path = os.path.join(upload_folder, profile.company_logo)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Save as PNG to preserve transparency
        filename = f"logo_{current_user.id}_{uuid.uuid4().hex[:8]}.png"
        image.save(os.path.join(upload_folder, filename), 'PNG')

        profile.company_logo = filename
        db.session.commit()

        flash("Company logo updated!", "success")

    except Exception as e:
        flash(f"Upload failed: {str(e)}", "danger")

    return redirect(url_for('recruiter.profile'))

# ===============================
# POST JOB
# ===============================
@recruiter_bp.route('/post-job', methods=['POST'])
@login_required
def post_job():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    title = request.form.get('title')
    description = request.form.get('description')
    field = request.form.get('field')
    job_type = request.form.get('job_type')
    location = request.form.get('location')
    salary = request.form.get('salary')
    expiration_date = request.form.get('expiration_date')

    expiration = None
    if expiration_date:
        expiration = datetime.strptime(expiration_date, "%Y-%m-%d").date()

    job = Job(
        title=title,
        description=description,
        company_id=current_user.id,
        field=field,
        job_type=job_type,
        location=location,
        salary=salary,
        expiration_date=expiration
    )

    db.session.add(job)
    db.session.commit()

    # IMAGE UPLOAD
    poster_files = request.files.getlist("posters")

    # ✅ FIXED: save to job_posters/ subfolder
    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_posters")
    os.makedirs(upload_folder, exist_ok=True)

    for file in poster_files:

        if file and file.filename != "":

            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4()}_{filename}"

            file.save(os.path.join(upload_folder, unique_name))

            image = JobImage(
                job_id=job.id,
                image_path=unique_name
            )

            db.session.add(image)

    db.session.commit()

    flash("Job posted successfully!", "success")

    return redirect(url_for('recruiter.job_posting'))


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
# MY JOB LIST
# ===============================
@recruiter_bp.route('/my-job-list')
@login_required
def my_job_list():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()

    return render_template(
        "recruiter/my_job_list.html",
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


# ===============================
# CREATE HR ACCOUNT
# ===============================
@recruiter_bp.route('/create-hr', methods=['POST'])
@login_required
def create_hr():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    username = request.form.get('username')
    email = request.form.get('email')

    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        flash("Username already exists. Please choose another.", "danger")
        return redirect(url_for('recruiter.hr_accounts'))

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        flash("Email is already registered.", "danger")
        return redirect(url_for('recruiter.hr_accounts'))

    temp_password = generate_temp_password()

    new_hr = User(
        username=username,
        email=email,
        password=generate_password_hash(temp_password),
        role="hr",
        created_by=current_user.id,
        must_change_password=True
    )

    db.session.add(new_hr)
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
# VIEW JOB APPLICATIONS (SPECIFIC JOB)
# ===============================
@recruiter_bp.route('/job-applications/<int:job_id>')
@login_required
def view_job_applications(job_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    applications = Application.query.filter_by(job_id=job_id).all()

    return render_template(
        "recruiter/job_applications.html",
        job=job,
        applications=applications
    )


# ===============================
# RECRUITER UPDATE APPLICATION STATUS
# ===============================
@recruiter_bp.route('/update-application-status/<int:app_id>', methods=['POST'])
@login_required
def update_application_status(app_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job = Job.query.get_or_404(application.job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    new_status = request.form.get('status')

    if new_status:
        application.status = new_status

    db.session.commit()

    flash("Application status updated!", "success")

    return redirect(url_for('recruiter.view_job_applications', job_id=job.id))


# ===============================
# EDIT JOB
# ===============================
@recruiter_bp.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.job_posting'))

    if request.method == "POST":

        job.title = request.form.get('title')
        job.description = request.form.get('description')
        job.field = request.form.get('field')
        job.job_type = request.form.get('job_type')
        job.location = request.form.get('location')
        job.salary = request.form.get('salary')

        expiration_date = request.form.get('expiration_date')

        if expiration_date:
            job.expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
        else:
            job.expiration_date = None

        # ===============================
        # UPLOAD NEW IMAGES
        # ===============================
        poster_files = request.files.getlist("posters")

        # ✅ FIXED: save to job_posters/ subfolder
        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_posters")
        os.makedirs(upload_folder, exist_ok=True)

        for poster_file in poster_files:

            if poster_file and poster_file.filename != "":

                filename = secure_filename(poster_file.filename)
                unique_name = f"{uuid.uuid4()}_{filename}"

                poster_path = os.path.join(upload_folder, unique_name)
                poster_file.save(poster_path)

                new_image = JobImage(
                    job_id=job.id,
                    image_path=unique_name
                )

                db.session.add(new_image)

        db.session.commit()

        flash("Job updated successfully!", "success")

        return redirect(url_for('recruiter.edit_job', job_id=job.id))

    return render_template(
        "recruiter/edit_job.html",
        job=job
    )


# ===============================
# DELETE JOB IMAGE
# ===============================
@recruiter_bp.route('/delete-job-image/<int:image_id>', methods=['POST'])
@login_required
def delete_job_image(image_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    image = JobImage.query.get_or_404(image_id)
    job = Job.query.get_or_404(image.job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.job_posting'))

    # ✅ FIXED: delete from job_posters/ subfolder
    file_path = os.path.join(
        current_app.root_path,
        "static", "uploads", "job_posters",
        image.image_path
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(image)
    db.session.commit()

    flash("Image deleted.", "success")

    return redirect(url_for('recruiter.edit_job', job_id=job.id))


# ===============================
# DELETE JOB
# ===============================
@recruiter_bp.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.job_posting'))

    for image in job.images:

        # ✅ FIXED: delete from job_posters/ subfolder
        file_path = os.path.join(
            current_app.root_path,
            "static", "uploads", "job_posters",
            image.image_path
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(image)

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully!", "success")

    return redirect(url_for('recruiter.my_job_list'))