from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import (
    db, Job, User, Application, JobImage, HRFeedback,
    RecruiterNotification, ApplicantNotification, RecruiterEducation,
    JobTeamMember
)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
from datetime import date
import base64
import io
import secrets
import string
import os
import uuid
import json


def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


recruiter_bp = Blueprint('recruiter', __name__, url_prefix="/recruiter")


# ===============================
# HELPER — ban check
# ===============================
def check_banned():
    if current_user.is_authenticated and current_user.is_banned:
        from flask import render_template as rt
        return rt("account_banned.html", user=current_user)
    return None


# ===============================
# HELPER — recruiter profile completion check
# ===============================
def is_recruiter_profile_complete(profile):
    if not profile:
        return False
    return all([
        profile.first_name,
        profile.surname,
        profile.phone_number,
        profile.company_name,
        profile.company_industry,
        profile.country,
        profile.city,
    ])


# ===============================
# HELPER — allowed image extensions
# ===============================
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# ===============================
# RECRUITER PROFILE / DASHBOARD
# ===============================
@recruiter_bp.route('/profile')
@login_required
def profile():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile, Follow

    jobs = Job.query.filter_by(company_id=current_user.id).all()
    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()
    rec_profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()

    educations = []
    if rec_profile:
        educations = RecruiterEducation.query.filter_by(
            profile_id=rec_profile.id
        ).order_by(RecruiterEducation.created_at.desc()).all()

    follower_rows  = Follow.query.filter_by(followed_id=current_user.id).all()
    following_rows = Follow.query.filter_by(follower_id=current_user.id).all()
    followers = [User.query.get(r.follower_id) for r in follower_rows]
    following = [User.query.get(r.followed_id) for r in following_rows]
    followers = [u for u in followers if u]
    following = [u for u in following if u]

    profile_complete = is_recruiter_profile_complete(rec_profile)

    if current_user.is_verified and current_user.verification_status == "Approved":
        verify_state = "approved"
    elif current_user.verification_status == "Rejected":
        verify_state = "rejected"
    elif rec_profile and rec_profile.submitted_for_review:
        verify_state = "pending"
    elif profile_complete:
        verify_state = "complete_unsubmitted"
    else:
        verify_state = "incomplete"

    return render_template(
        'recruiter/profile.html',
        jobs=jobs,
        hrs=hrs,
        profile=rec_profile,
        educations=educations,
        follower_count=len(followers),
        following_count=len(following),
        followers=followers,
        following=following,
        profile_complete=profile_complete,
        verify_state=verify_state,
    )


# ===============================
# SUBMIT PROFILE FOR ADMIN REVIEW
# ===============================
@recruiter_bp.route('/submit-for-review', methods=['POST'])
@login_required
def submit_for_review():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile
    profile = current_user.recruiter_profile

    if not is_recruiter_profile_complete(profile):
        flash("Please complete all required profile fields before submitting for review.", "warning")
        return redirect(url_for('recruiter.profile'))

    if current_user.is_verified:
        flash("Your account is already verified.", "info")
        return redirect(url_for('recruiter.profile'))

    if profile.submitted_for_review and current_user.verification_status == "Pending":
        flash("Your account is already pending review.", "info")
        return redirect(url_for('recruiter.profile'))

    profile.submitted_for_review = True
    current_user.verification_status = "Pending"

    try:
        from routes.admin import push_admin_notif
        push_admin_notif(
            'account_request',
            f'Recruiter <strong>{current_user.username}</strong> has submitted their profile for verification.',
            user_id=current_user.id
        )
    except:
        pass

    db.session.commit()

    flash("Your profile has been submitted for admin review. You'll be notified once verified.", "success")
    return redirect(url_for('recruiter.profile'))


# ===============================
# UPLOAD PROFILE PICTURE
# ===============================
@recruiter_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    banned = check_banned()
    if banned:
        return banned

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
    banned = check_banned()
    if banned:
        return banned

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

        if profile.company_logo and not profile.company_logo.startswith('http'):
            old_path = os.path.join(upload_folder, profile.company_logo)
            if os.path.exists(old_path):
                os.remove(old_path)

        filename = f"logo_{current_user.id}_{uuid.uuid4().hex[:8]}.png"
        image.save(os.path.join(upload_folder, filename), 'PNG')

        profile.company_logo = filename
        db.session.commit()

        flash("Company logo updated!", "success")

    except Exception as e:
        flash(f"Upload failed: {str(e)}", "danger")

    return redirect(url_for('recruiter.profile'))


# ===============================
# RECRUITER UPDATE PROFILE
# ===============================
@recruiter_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile
    section = request.form.get('section')
    profile = current_user.recruiter_profile

    if not profile:
        profile = RecruiterProfile(user_id=current_user.id)
        db.session.add(profile)

    if section == 'personal':
        profile.first_name   = request.form.get('first_name', '').strip()
        profile.middle_name  = request.form.get('middle_name', '').strip()
        profile.surname      = request.form.get('surname', '').strip() or request.form.get('last_name', '').strip()
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

    elif section == 'company':
        profile.company_name         = request.form.get('company_name', '').strip()
        profile.company_industry     = request.form.get('industry', '').strip()
        profile.country              = request.form.get('country', '').strip()
        profile.city                 = request.form.get('city', '').strip()
        profile.company_address      = request.form.get('company_address', '').strip()
        profile.company_email_domain = request.form.get('company_website', '').strip()
        profile.company_description  = request.form.get('company_description', '').strip()

    elif section == 'account':
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != current_user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                flash("That username is already taken.", "danger")
                return redirect(url_for('recruiter.profile'))
            current_user.username = new_username

    db.session.flush()

    user_row = db.session.get(User, current_user.id)
    if not getattr(user_row, 'profile_completed', False):
        if is_recruiter_profile_complete(profile):
            user_row.profile_completed = True

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('recruiter.profile'))


# ===============================
# UPDATE SOCIAL LINKS
# ===============================
@recruiter_bp.route('/update-social', methods=['POST'])
@login_required
def update_social():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile
    profile = current_user.recruiter_profile

    if not profile:
        profile = RecruiterProfile(user_id=current_user.id)
        db.session.add(profile)

    profile.linkedin  = request.form.get('linkedin', '').strip()
    profile.github    = request.form.get('github', '').strip()
    profile.portfolio = request.form.get('portfolio', '').strip()

    db.session.commit()
    flash("Links updated successfully!", "success")
    return redirect(url_for('recruiter.profile'))


# ===============================
# ADD EDUCATION  (recruiter-specific)
# ===============================
@recruiter_bp.route('/add-education', methods=['POST'])
@login_required
def add_education():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile

    profile = current_user.recruiter_profile
    if not profile:
        profile = RecruiterProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()

    is_current = request.form.get('is_current') == '1'

    edu = RecruiterEducation(
        profile_id     = profile.id,
        school         = request.form.get('school', '').strip(),
        degree         = request.form.get('degree', '').strip(),
        field_of_study = request.form.get('field_of_study', '').strip(),
        start_date     = request.form.get('start_date', '').strip(),
        end_date       = '' if is_current else request.form.get('end_date', '').strip(),
        is_current     = is_current,
        description    = request.form.get('description', '').strip(),
    )

    db.session.add(edu)
    db.session.commit()

    flash("Education added!", "success")
    return redirect(url_for('recruiter.profile'))


# ===============================
# DELETE EDUCATION  (recruiter-specific)
# ===============================
@recruiter_bp.route('/delete-education/<int:edu_id>', methods=['POST'])
@login_required
def delete_education(edu_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    edu = RecruiterEducation.query.get_or_404(edu_id)

    profile = current_user.recruiter_profile
    if not profile or edu.profile_id != profile.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.profile'))

    db.session.delete(edu)
    db.session.commit()

    flash("Education removed.", "success")
    return redirect(url_for('recruiter.profile'))


# ===============================
# POST JOB  
# ===============================
@recruiter_bp.route('/post-job', methods=['POST'])
@login_required
def post_job():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if not current_user.is_verified:
        flash("Your account must be verified before you can post jobs.", "warning")
        return redirect(url_for('recruiter.profile'))

    title = request.form.get('title')
    description = request.form.get('description')
    field = request.form.get('field')
    job_type = request.form.get('job_type')
    location = request.form.get('location')
    salary = request.form.get('salary')
    currency = request.form.get('currency', 'PHP')
    expiration_date = request.form.get('expiration_date')

    arrangement        = request.form.get('arrangement')
    experience_level   = request.form.get('experience_level')
    years_exp          = request.form.get('years_exp')
    education          = request.form.get('education')
    required_skills    = request.form.get('required_skills')
    preferred_skills   = request.form.get('preferred_skills')
    languages          = request.form.get('languages')
    requirements_notes = request.form.get('requirements_notes')

    # Quota / toggle
    max_applications_str = request.form.get('max_applications', '').strip()
    max_applications = int(max_applications_str) if max_applications_str.isdigit() else None
    allow_applications = request.form.get('allow_applications') == 'on'

    # Company content
    about_company_raw = request.form.get('about_company', '').strip()
    about_company = about_company_raw or None

    # why_join_us arrives as a JSON string from the hidden input (built by job_posting.js)
    why_join_us_raw = request.form.get('why_join_us', '').strip()
    if why_join_us_raw:
        try:
            # Validate it's proper JSON; store as-is
            json.loads(why_join_us_raw)
            why_join_us = why_join_us_raw
        except (ValueError, TypeError):
            # Fall back: treat as plain text, wrap in JSON array
            lines = [l.strip() for l in why_join_us_raw.split('\n') if l.strip()]
            why_join_us = json.dumps(lines) if lines else None
    else:
        why_join_us = None

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
        currency=currency,
        expiration_date=expiration,
        arrangement=arrangement,
        experience_level=experience_level,
        years_exp=years_exp,
        education=education,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        languages=languages,
        requirements_notes=requirements_notes,
        max_applications=max_applications,
        allow_applications=allow_applications,
        about_company=about_company,
        why_join_us=why_join_us,
    )

    db.session.add(job)
    db.session.flush()  # get job.id before saving files

    # ── Cover photo (FIXED: was never saved before) ──────────────
    cover_file = request.files.get('cover_photo')
    if cover_file and cover_file.filename != '' and allowed_image(cover_file.filename):
        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_covers")
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(cover_file.filename)
        unique_name = f"cover_{job.id}_{uuid.uuid4().hex[:8]}_{filename}"
        cover_file.save(os.path.join(upload_folder, unique_name))
        job.cover_photo = unique_name

    # ── Gallery images ────────────────────────────────────────────
    poster_files = request.files.getlist("posters")
    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_posters")
    os.makedirs(upload_folder, exist_ok=True)

    for file in poster_files:
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4()}_{filename}"
            file.save(os.path.join(upload_folder, unique_name))
            image = JobImage(job_id=job.id, image_path=unique_name)
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
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()

    return render_template("recruiter/job_posting.html", jobs=jobs)


# ===============================
# MY JOB LIST
# ===============================
@recruiter_bp.route('/my-job-list')
@login_required
def my_job_list():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs = Job.query.filter_by(company_id=current_user.id).all()

    return render_template(
        "recruiter/my_job_list.html",
        jobs=jobs,
        current_date=date.today()
    )


# ===============================
# HR ACCOUNTS PAGE
# ===============================
@recruiter_bp.route('/hr-accounts')
@login_required
def hr_accounts():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if not current_user.is_verified:
        flash("Your account must be verified to manage HR accounts.", "warning")
        return redirect(url_for('recruiter.profile'))

    hrs = User.query.filter_by(
        created_by=current_user.id,
        role="hr",
        is_deleted=False
    ).all()

    return render_template("recruiter/hr_accounts.html", hrs=hrs)


# ===============================
# CREATE HR ACCOUNT
# ===============================
@recruiter_bp.route('/create-hr', methods=['POST'])
@login_required
def create_hr():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if not current_user.is_verified:
        flash("Your account must be verified to create HR accounts.", "warning")
        return redirect(url_for('recruiter.profile'))

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
        role="hr",
        is_deleted=False
    ).all()

    return render_template(
        "recruiter/hr_accounts.html",
        hrs=hrs,
        temp_password=temp_password
    )


# ================================================================
# SOFT-DELETE / UNDO-DELETE / COMMIT-DELETE HR (unchanged)
# ================================================================

@recruiter_bp.route('/soft-delete-hr/<int:hr_id>', methods=['POST'])
@login_required
def soft_delete_hr(hr_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id, is_deleted=False).first()
    if not hr:
        return jsonify({'success': False, 'error': 'HR account not found'}), 404

    hr.is_deleted = True
    hr.deleted_at = datetime.utcnow()
    hr.deleted_by = current_user.id
    db.session.commit()

    return jsonify({'success': True, 'hr_id': hr_id})


@recruiter_bp.route('/soft-delete-all-hr', methods=['POST'])
@login_required
def soft_delete_all_hr():
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    hrs = User.query.filter_by(created_by=current_user.id, role='hr', is_deleted=False).all()
    if not hrs:
        return jsonify({'success': True, 'deleted_ids': []})

    now = datetime.utcnow()
    deleted_ids = []
    for hr in hrs:
        hr.is_deleted = True
        hr.deleted_at = now
        hr.deleted_by = current_user.id
        deleted_ids.append(hr.id)

    db.session.commit()
    return jsonify({'success': True, 'deleted_ids': deleted_ids})


@recruiter_bp.route('/undo-delete-hr/<int:hr_id>', methods=['POST'])
@login_required
def undo_delete_hr(hr_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id, is_deleted=True).first()
    if not hr:
        return jsonify({'success': False, 'error': 'HR account not found or already committed'}), 404

    hr.is_deleted = False
    hr.deleted_at = None
    hr.deleted_by = None
    db.session.commit()

    return jsonify({'success': True})


@recruiter_bp.route('/undo-delete-all-hr', methods=['POST'])
@login_required
def undo_delete_all_hr():
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    data = request.get_json(silent=True) or {}
    ids  = data.get('ids', [])

    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'}), 400

    restored = 0
    for hr_id in ids:
        hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id, is_deleted=True).first()
        if hr:
            hr.is_deleted = False
            hr.deleted_at = None
            hr.deleted_by = None
            restored += 1

    db.session.commit()
    return jsonify({'success': True, 'restored': restored})


@recruiter_bp.route('/commit-delete-hr/<int:hr_id>', methods=['POST'])
@login_required
def commit_delete_hr(hr_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id, is_deleted=True).first()
    if not hr:
        return jsonify({'success': True, 'skipped': True})

    try:
        from sqlalchemy import text
        db.session.execute(text("DELETE FROM hr_feedback WHERE hr_id = :hr_id"), {"hr_id": hr.id})
        db.session.flush()

        if hr.hr_profile:
            db.session.delete(hr.hr_profile)
            db.session.flush()

        db.session.delete(hr)
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@recruiter_bp.route('/commit-delete-all-hr', methods=['POST'])
@login_required
def commit_delete_all_hr():
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    data = request.get_json(silent=True) or {}
    ids  = data.get('ids', [])

    if not ids:
        return jsonify({'success': True, 'message': 'Nothing to commit'})

    try:
        from sqlalchemy import text

        for hr_id in ids:
            hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id, is_deleted=True).first()
            if not hr:
                continue

            db.session.execute(text("DELETE FROM hr_feedback WHERE hr_id = :hr_id"), {"hr_id": hr_id})
            db.session.flush()

            if hr.hr_profile:
                db.session.delete(hr.hr_profile)
                db.session.flush()

            db.session.delete(hr)
            db.session.flush()

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@recruiter_bp.route('/delete-hr/<int:hr_id>', methods=['POST'])
@login_required
def delete_hr(hr_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id).first()
    if not hr:
        return jsonify({'success': False, 'error': 'HR account not found'}), 404

    try:
        from sqlalchemy import text
        db.session.execute(text("DELETE FROM hr_feedback WHERE hr_id = :hr_id"), {"hr_id": hr.id})
        db.session.flush()

        if hr.hr_profile:
            db.session.delete(hr.hr_profile)
            db.session.flush()

        db.session.delete(hr)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@recruiter_bp.route('/delete-all-hr', methods=['POST'])
@login_required
def delete_all_hr():
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()
    if not hrs:
        return jsonify({'success': True, 'message': 'No HR accounts to delete'})

    try:
        from sqlalchemy import text

        hr_ids = [hr.id for hr in hrs]

        for hr_id in hr_ids:
            db.session.execute(text("DELETE FROM hr_feedback WHERE hr_id = :hr_id"), {"hr_id": hr_id})
        db.session.flush()

        for hr in hrs:
            if hr.hr_profile:
                db.session.delete(hr.hr_profile)
                db.session.flush()
            db.session.delete(hr)
            db.session.flush()

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================
# VIEW JOB APPLICATIONS
# ===============================
@recruiter_bp.route('/job-applications/<int:job_id>')
@login_required
def view_job_applications(job_id):
    banned = check_banned()
    if banned:
        return banned

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
# UPDATE APPLICATION STATUS
# ===============================
@recruiter_bp.route('/update-application-status/<int:app_id>', methods=['POST'])
@login_required
def update_application_status(app_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job = Job.query.get_or_404(application.job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    new_status = request.form.get('status')
    new_remarks = request.form.get('recruiter_remarks')

    if new_status:
        application.status = new_status

    if new_remarks is not None:
        application.recruiter_remarks = new_remarks

    db.session.commit()

    applicant_user = User.query.get(application.applicant_id)
    job_for_notif = Job.query.get(application.job_id)

    if new_status:
        notif = RecruiterNotification(
            recruiter_id=current_user.id,
            type='new_application',
            message=f"Application status for <strong>{applicant_user.username}</strong> on <strong>{job_for_notif.title}</strong> updated to <strong>{new_status.capitalize()}</strong>.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(notif)

        app_notif = ApplicantNotification(
            applicant_id=application.applicant_id,
            type='application_status',
            message=f"Your application for <strong>{job_for_notif.title}</strong> has been updated to <strong>{new_status.capitalize()}</strong>.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(app_notif)
        db.session.commit()

    flash("Application status updated!", "success")
    return redirect(url_for('recruiter.view_job_applications', job_id=job.id))


# ===============================
# SCHEDULE INTERVIEW
# ===============================
@recruiter_bp.route('/schedule-interview/<int:app_id>', methods=['POST'])
@login_required
def schedule_interview(app_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job = Job.query.get_or_404(application.job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    interview_date_str = request.form.get('interview_date')

    if interview_date_str:
        application.interview_date = datetime.strptime(interview_date_str, "%Y-%m-%dT%H:%M")
        application.status = 'interview'
        db.session.commit()

        applicant = User.query.get(application.applicant_id)
        job_ref = Job.query.get(application.job_id)

        notif = RecruiterNotification(
            recruiter_id=current_user.id,
            type='interview_scheduled',
            message=f"Interview scheduled for <strong>{applicant.username}</strong> applying for <strong>{job_ref.title}</strong> on {application.interview_date.strftime('%b %d, %Y at %I:%M %p')}.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(notif)

        app_notif = ApplicantNotification(
            applicant_id=application.applicant_id,
            type='interview_scheduled',
            message=f"An interview has been scheduled for your application to <strong>{job_ref.title}</strong> on <strong>{application.interview_date.strftime('%b %d, %Y at %I:%M %p')}</strong>.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(app_notif)
        db.session.commit()

        flash("Interview scheduled successfully!", "success")
    else:
        flash("Please provide a valid date and time.", "danger")

    return redirect(url_for('recruiter.view_job_applications', job_id=job.id))


# ===============================
# EDIT JOB  (GET + POST)
# ===============================
@recruiter_bp.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.job_posting'))

    if request.method == "POST":

        job.title       = request.form.get('title')
        job.description = request.form.get('description')
        job.field       = request.form.get('field')
        job.job_type    = request.form.get('job_type')
        job.location    = request.form.get('location')
        job.salary      = request.form.get('salary')
        job.currency    = request.form.get('currency', 'PHP')
        job.arrangement = request.form.get('arrangement')

        job.experience_level   = request.form.get('experience_level')
        job.years_exp          = request.form.get('years_exp')
        job.education          = request.form.get('education')
        job.required_skills    = request.form.get('required_skills')
        job.preferred_skills   = request.form.get('preferred_skills')
        job.languages          = request.form.get('languages')
        job.requirements_notes = request.form.get('requirements_notes')

        expiration_date = request.form.get('expiration_date')
        if expiration_date:
            job.expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
        else:
            job.expiration_date = None

        # ── NEW fields ──
        max_applications_str = request.form.get('max_applications', '').strip()
        job.max_applications = int(max_applications_str) if max_applications_str.isdigit() else None
        job.allow_applications = request.form.get('allow_applications') == 'on'

        # ── About / Why Join / Company Overview (per-job override) ──
        job.about_company  = request.form.get('about_company', '').strip() or None
        job.why_join_us    = request.form.get('why_join_us', '').strip() or None
        job.company_values = request.form.get('company_values', '').strip() or None

        # ── Cover photo ──
        cover_file = request.files.get('cover_photo')
        if cover_file and cover_file.filename != '' and allowed_image(cover_file.filename):
            upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_covers")
            os.makedirs(upload_folder, exist_ok=True)

            # Delete old cover if exists
            if job.cover_photo:
                old_path = os.path.join(upload_folder, job.cover_photo)
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = secure_filename(cover_file.filename)
            unique_name = f"cover_{job.id}_{uuid.uuid4().hex[:8]}_{filename}"
            cover_file.save(os.path.join(upload_folder, unique_name))
            job.cover_photo = unique_name

        # ── Gallery images ──
        poster_files = request.files.getlist("posters")
        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_posters")
        os.makedirs(upload_folder, exist_ok=True)

        for poster_file in poster_files:
            if poster_file and poster_file.filename != "" and allowed_image(poster_file.filename):
                filename = secure_filename(poster_file.filename)
                unique_name = f"{uuid.uuid4()}_{filename}"
                poster_path = os.path.join(upload_folder, unique_name)
                poster_file.save(poster_path)
                new_image = JobImage(job_id=job.id, image_path=unique_name)
                db.session.add(new_image)

        # ── Force updated_at refresh ──
        job.updated_at = datetime.utcnow()

        db.session.commit()

        flash("Job updated successfully!", "success")
        return redirect(url_for('recruiter.edit_job', job_id=job.id))

    # GET — pass HR list for team assignment
    hr_list = User.query.filter_by(
        created_by=current_user.id,
        role='hr',
        is_deleted=False
    ).all()

    assigned_hr_ids = {tm.hr_id for tm in job.team_members}

    return render_template(
        "recruiter/edit_job.html",
        job=job,
        hr_list=hr_list,
        assigned_hr_ids=assigned_hr_ids,
    )


# ===============================
# UPDATE JOB COVER PHOTO  (AJAX)
# ===============================
@recruiter_bp.route('/update-job-cover/<int:job_id>', methods=['POST'])
@login_required
def update_job_cover(job_id):
    """Dedicated AJAX endpoint to change only the cover photo."""
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    cover_file = request.files.get('cover_photo')
    if not cover_file or cover_file.filename == '':
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    if not allowed_image(cover_file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400

    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "job_covers")
    os.makedirs(upload_folder, exist_ok=True)

    if job.cover_photo:
        old_path = os.path.join(upload_folder, job.cover_photo)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = secure_filename(cover_file.filename)
    unique_name = f"cover_{job.id}_{uuid.uuid4().hex[:8]}_{filename}"
    cover_file.save(os.path.join(upload_folder, unique_name))
    job.cover_photo = unique_name
    job.updated_at  = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'url': url_for('static', filename=f'uploads/job_covers/{unique_name}')
    })


# ===============================
# UPDATE JOB COMPANY CONTENT  (AJAX)
# ===============================
@recruiter_bp.route('/update-job-company-content/<int:job_id>', methods=['POST'])
@login_required
def update_job_company_content(job_id):
    """
    AJAX endpoint to update about_company, why_join_us, company_values
    for a specific job posting.
    """
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}

    section = data.get('section')

    if section == 'about':
        job.about_company = data.get('content', '').strip() or None

    elif section == 'why_join':
        # Expects a JSON array of strings
        items = data.get('items', [])
        job.why_join_us = json.dumps(items) if items else None

    elif section == 'values':
        # Expects a JSON array of {title, description}
        items = data.get('items', [])
        job.company_values = json.dumps(items) if items else None

    elif section == 'overview':
        # Plain text fields
        job.about_company = data.get('about', '').strip() or None

    else:
        return jsonify({'success': False, 'error': 'Unknown section'}), 400

    job.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})


# ===============================
# MANAGE JOB TEAM MEMBERS  (AJAX)
# ===============================
@recruiter_bp.route('/job-team/<int:job_id>/add', methods=['POST'])
@login_required
def add_job_team_member(job_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data  = request.get_json(silent=True) or {}
    hr_id = data.get('hr_id')

    # Validate the HR belongs to this recruiter
    hr = User.query.filter_by(id=hr_id, role='hr', created_by=current_user.id, is_deleted=False).first()
    if not hr:
        return jsonify({'success': False, 'error': 'HR member not found'}), 404

    existing = JobTeamMember.query.filter_by(job_id=job_id, hr_id=hr_id).first()
    if existing:
        return jsonify({'success': False, 'error': 'Already assigned'}), 409

    member = JobTeamMember(job_id=job_id, hr_id=hr_id)
    db.session.add(member)
    db.session.commit()

    return jsonify({
        'success': True,
        'member': {
            'id':       member.id,
            'hr_id':    hr.id,
            'username': hr.username,
            'email':    hr.email,
            'picture':  hr.profile_picture,
        }
    })


@recruiter_bp.route('/job-team/<int:job_id>/remove', methods=['POST'])
@login_required
def remove_job_team_member(job_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data  = request.get_json(silent=True) or {}
    hr_id = data.get('hr_id')

    member = JobTeamMember.query.filter_by(job_id=job_id, hr_id=hr_id).first()
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404

    db.session.delete(member)
    db.session.commit()

    return jsonify({'success': True})


# ===============================
# TOGGLE ALLOW APPLICATIONS  (AJAX)
# ===============================
@recruiter_bp.route('/job-toggle-applications/<int:job_id>', methods=['POST'])
@login_required
def toggle_allow_applications(job_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    value = data.get('allow', True)
    job.allow_applications = bool(value)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(job, 'allow_applications')
    job.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'allow_applications': job.allow_applications})


# ===============================
# DELETE JOB IMAGE
# ===============================
@recruiter_bp.route('/delete-job-image/<int:image_id>', methods=['POST'])
@login_required
def delete_job_image(image_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    image = JobImage.query.get_or_404(image_id)
    job = Job.query.get_or_404(image.job_id)

    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    file_path = os.path.join(
        current_app.root_path, "static", "uploads", "job_posters", image.image_path
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(image)
    db.session.commit()

    return jsonify({'success': True})


# ===============================
# DELETE JOB — with active-applications guard
# ===============================
@recruiter_bp.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('recruiter.job_posting'))

    # ── Guard: block deletion if active applications exist ──
    force = request.form.get('force_delete') == '1'
    active_apps = Application.query.filter_by(job_id=job_id).count()

    if active_apps > 0 and not force:
        flash(
            f"This job has {active_apps} application(s). "
            "To delete it, confirm deletion from the job management page.",
            "warning"
        )
        return redirect(url_for('recruiter.edit_job', job_id=job_id))

    # Delete gallery images
    for image in job.images:
        file_path = os.path.join(
            current_app.root_path, "static", "uploads", "job_posters", image.image_path
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(image)

    # Delete cover photo
    if job.cover_photo:
        cover_path = os.path.join(
            current_app.root_path, "static", "uploads", "job_covers", job.cover_photo
        )
        if os.path.exists(cover_path):
            os.remove(cover_path)

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully!", "success")
    return redirect(url_for('recruiter.my_job_list'))


# ===============================
# FORCE DELETE JOB  (AJAX — when there are active applicants)
# ===============================
@recruiter_bp.route('/force-delete-job/<int:job_id>', methods=['POST'])
@login_required
def force_delete_job(job_id):
    """Called when recruiter explicitly confirms deletion despite active applications."""
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from sqlalchemy import text

        # 1. Delete applicant notifications tied to this job's applications
        db.session.execute(text("""
            DELETE FROM applicant_notification
            WHERE application_id IN (
                SELECT id FROM application WHERE job_id = :job_id
            )
        """), {"job_id": job_id})

        # 2. Delete recruiter notifications tied to this job
        db.session.execute(text("""
            DELETE FROM recruiter_notification
            WHERE job_id = :job_id
            OR application_id IN (
                SELECT id FROM application WHERE job_id = :job_id
            )
        """), {"job_id": job_id})

        # 3. Delete HR notifications tied to this job
        db.session.execute(text("""
            DELETE FROM hr_notification
            WHERE job_id = :job_id
            OR application_id IN (
                SELECT id FROM application WHERE job_id = :job_id
            )
        """), {"job_id": job_id})

        db.session.flush()

        # 4. Remove gallery images from disk
        for image in job.images:
            file_path = os.path.join(
                current_app.root_path, "static", "uploads", "job_posters", image.image_path
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(image)

        # 5. Remove cover photo from disk
        if job.cover_photo:
            cover_path = os.path.join(
                current_app.root_path, "static", "uploads", "job_covers", job.cover_photo
            )
            if os.path.exists(cover_path):
                os.remove(cover_path)

        db.session.delete(job)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================
# RECRUITER NOTIFICATION HISTORY PAGE
# ===============================
@recruiter_bp.route('/notification-history')
@login_required
def notification_history():
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
    notifs = RecruiterNotification.query.filter_by(
        recruiter_id=current_user.id
    ).order_by(RecruiterNotification.created_at.desc()).all()
    RecruiterNotification.query.filter_by(
        recruiter_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return render_template('recruiter/notification_history.html', notifications=notifs)


@recruiter_bp.route('/clear-all-notifications', methods=['POST'])
@login_required
def clear_all_notifications():
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    RecruiterNotification.query.filter_by(recruiter_id=current_user.id).delete()
    db.session.commit()

    flash("All notifications cleared.", "success")
    return redirect(url_for('recruiter.notification_history'))


@recruiter_bp.route('/notifications')
@login_required
def get_notifications():
    if current_user.role != 'recruiter':
        return jsonify({'error': 'forbidden'}), 403
    notifs = RecruiterNotification.query.filter_by(
        recruiter_id=current_user.id
    ).order_by(RecruiterNotification.created_at.desc()).limit(50).all()
    unread_count = RecruiterNotification.query.filter_by(
        recruiter_id=current_user.id, is_read=False
    ).count()
    return jsonify({
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'type': n.type,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%b %d, %Y at %I:%M %p'),
                'job_id': n.job_id
            }
            for n in notifs
        ]
    })


@recruiter_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'recruiter':
        return jsonify({'error': 'forbidden'}), 403
    RecruiterNotification.query.filter_by(
        recruiter_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


@recruiter_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications_api():
    if current_user.role != 'recruiter':
        return jsonify({'error': 'forbidden'}), 403
    RecruiterNotification.query.filter_by(recruiter_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'ok': True})