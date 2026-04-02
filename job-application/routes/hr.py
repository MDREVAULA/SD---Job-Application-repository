from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Application, Job, HRProfile, HRFeedback, User
from werkzeug.security import generate_password_hash
from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import io
import os
import uuid

hr_bp = Blueprint('hr', __name__, url_prefix="/hr")


# =========================
# HR PROFILE PAGE
# =========================
@hr_bp.route('/profile')
@login_required
def profile():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile

    hr_profile = current_user.hr_profile

    # Fetch the recruiter who created this HR account
    recruiter_profile = None
    if current_user.created_by:
        recruiter_profile = RecruiterProfile.query.filter_by(
            user_id=current_user.created_by
        ).first()

    return render_template(
        "hr/profile.html",
        profile=hr_profile,
        recruiter_profile=recruiter_profile
    )


# ===============================
# UPLOAD PROFILE PICTURE
# ===============================
@hr_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    cropped_data = request.form.get('cropped_image')

    if not cropped_data:
        flash("No image data received.", "danger")
        return redirect(url_for('hr.profile'))

    try:
        header, encoded = cropped_data.split(',', 1)
        image_data = base64.b64decode(encoded)

        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image = image.resize((400, 400), Image.LANCZOS)

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
        os.makedirs(upload_folder, exist_ok=True)

        if current_user.profile_picture:
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

    return redirect(url_for('hr.profile'))

# =========================
# HR UPDATE PROFILE
# =========================
@hr_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    section = request.form.get('section')
    profile = current_user.hr_profile

    # If no profile row exists yet, create one first
    if not profile:
        profile = HRProfile(user_id=current_user.id)
        db.session.add(profile)

    if section == 'personal':
        profile.first_name   = request.form.get('first_name', '').strip()
        profile.middle_name  = request.form.get('middle_name', '').strip()
        profile.last_name    = request.form.get('last_name', '').strip()
        profile.gender       = request.form.get('gender', '').strip()
        profile.phone_number = request.form.get('phone_number', '').strip()
        profile.home_address = request.form.get('home_address', '').strip()
        profile.headline     = request.form.get('headline', '').strip()
        profile.bio          = request.form.get('bio', '').strip()
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            try:
                profile.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                pass

    elif section == 'location':
        profile.country      = request.form.get('country', '').strip()
        profile.city         = request.form.get('city', '').strip()
        profile.home_address = request.form.get('home_address', '').strip()

    elif section == 'account':
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != current_user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                flash("That username is already taken.", "danger")
                return redirect(url_for('hr.profile'))
            current_user.username = new_username

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('hr.profile'))

# =========================
# CHANGE PASSWORD
# =========================
@hr_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if request.method == "POST":

        new_password = request.form.get("password")

        current_user.password = generate_password_hash(new_password)
        current_user.must_change_password = False

        db.session.commit()

        flash("Password changed successfully! Please complete your profile.", "success")

        # Redirect to setup page after password change
        return redirect(url_for("hr.setup_profile"))

    return render_template("hr/change_password.html")


# =========================
# HR FIRST-TIME PROFILE SETUP
# =========================
@hr_bp.route('/setup-profile', methods=['GET', 'POST'])
@login_required
def setup_profile():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # If HR already has a profile, skip setup
    if current_user.hr_profile:
        return redirect(url_for('hr.profile'))

    if request.method == 'POST':

        dob_str = request.form.get('date_of_birth')
        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except:
                dob = None

        hr_profile = HRProfile(
            user_id=current_user.id,
            last_name=request.form.get('last_name') or '',
            first_name=request.form.get('first_name') or '',
            middle_name=request.form.get('middle_name') or '',
            date_of_birth=dob,
            gender=request.form.get('gender') or '',
            phone_number=request.form.get('phone_number') or '',
            country=request.form.get('country') or '',
            city=request.form.get('city') or '',
            home_address=request.form.get('home_address') or '',
        )

        db.session.add(hr_profile)
        db.session.commit()

        flash("Profile set up successfully! Welcome!", "success")
        return redirect(url_for('hr.profile'))

    return render_template("hr/setup_profile.html")

# =========================
# HR UPDATE SOCIAL LINKS
# =========================
@hr_bp.route('/update-social', methods=['POST'])
@login_required
def update_social():
 
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
 
    profile = current_user.hr_profile
 
    if not profile:
        profile = HRProfile(user_id=current_user.id)
        db.session.add(profile)
 
    profile.linkedin  = request.form.get('linkedin', '').strip()
    profile.github    = request.form.get('github', '').strip()
    profile.portfolio = request.form.get('portfolio', '').strip()
 
    db.session.commit()
    flash("Links updated successfully!", "success")
    return redirect(url_for('hr.profile'))

# ===============================
# HR JOB LIST (VIEW ALL JOBS)
# ===============================
@hr_bp.route('/job-list')
@login_required
def job_list():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.created_by).all()

    return render_template(
        "hr/job_list.html",
        jobs=jobs
    )


# ===============================
# HR VIEW JOB APPLICATIONS
# ===============================
@hr_bp.route('/job-applications/<int:job_id>')
@login_required
def job_applications(job_id):

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    applications = Application.query.filter_by(job_id=job_id).all()

    # Get the recruiter who owns this job for feedback display
    recruiter_user = User.query.get(job.company_id)

    return render_template(
        "hr/job_applications.html",
        job=job,
        applications=applications,
        recruiter_user=recruiter_user
    )


# ===============================
# HR UPDATE APPLICATION STATUS
# ===============================
@hr_bp.route('/update-application-status/<int:app_id>', methods=['POST'])
@login_required
def update_application_status(app_id):

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)

    new_status = request.form.get('status')
    new_feedback = request.form.get('hr_feedback')

    if new_status:
        application.status = new_status

    # Save or update this HR's feedback for this application
    if new_feedback is not None and new_feedback.strip() != '':
        existing = HRFeedback.query.filter_by(
            application_id=app_id,
            hr_id=current_user.id
        ).first()

        if existing:
            existing.feedback = new_feedback
            existing.updated_at = datetime.utcnow()
        else:
            new_fb = HRFeedback(
                application_id=app_id,
                hr_id=current_user.id,
                feedback=new_feedback
            )
            db.session.add(new_fb)

    db.session.commit()

    flash("Application updated successfully!", "success")

    return redirect(
        url_for('hr.job_applications', job_id=application.job_id)
    )


# ===============================
# HR SCHEDULE INTERVIEW
# ===============================
@hr_bp.route('/schedule-interview/<int:app_id>', methods=['POST'])
@login_required
def schedule_interview(app_id):

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)

    interview_date_str = request.form.get('interview_date')

    if interview_date_str:
        application.interview_date = datetime.strptime(interview_date_str, "%Y-%m-%dT%H:%M")
        application.status = 'interview'
        db.session.commit()
        flash("Interview scheduled successfully!", "success")
    else:
        flash("Please provide a valid date and time.", "danger")

    return redirect(
        url_for('hr.job_applications', job_id=application.job_id)
    )