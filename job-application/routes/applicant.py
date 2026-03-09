# routes/applicant.py
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os, uuid
from models import db, ApplicantProfile, Job, Application

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

applicant_bp = Blueprint('applicant', __name__, url_prefix="/applicant")

# ------------------ Dashboard ------------------
@applicant_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.all()
    applications = Application.query.filter_by(applicant_id=current_user.id).all()
    return render_template('applicant_dashboard.html', jobs=jobs, applications=applications)

# ------------------ Apply Job ------------------
@applicant_bp.route('/apply/<int:job_id>')
@login_required
def apply_job(job_id):
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    existing = Application.query.filter_by(applicant_id=current_user.id, job_id=job_id).first()
    if existing:
        flash("You already applied for this job!", "warning")
    else:
        application = Application(applicant_id=current_user.id, job_id=job_id)
        db.session.add(application)
        db.session.commit()
        flash("Application submitted successfully!", "success")

    return redirect(url_for('applicant.dashboard'))

# ------------------ Profile ------------------
@applicant_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Get or create profile
    profile = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = ApplicantProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    if request.method == 'POST':
        # Update text fields
        profile.first_name = request.form.get('first_name')
        profile.last_name = request.form.get('last_name')
        profile.middle_name = request.form.get('middle_name')

        dob = request.form.get('date_of_birth')
        profile.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None

        profile.gender = request.form.get('gender')
        profile.phone_number = request.form.get('phone_number')
        profile.country = request.form.get('country')
        profile.city = request.form.get('city')
        profile.home_address = request.form.get('home_address')

        # Handle profile picture safely
        picture_file = request.files.get('profile_picture')
        if picture_file and picture_file.filename and allowed_image(picture_file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(picture_file.filename)}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Save file safely
            try:
                picture_file.save(filepath)
                profile.profile_picture = filename  # update profile picture
            except Exception as e:
                flash(f"Failed to save profile picture: {str(e)}", "danger")

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('applicant.profile'))

    # GET request
    return render_template('applicant_profile.html', profile=profile)