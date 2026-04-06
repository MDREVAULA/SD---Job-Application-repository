from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Job, Application, User, ApplicantProfile, WorkExperience, Education, Skill, Project, Certification
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import base64
import io
import os
import uuid

applicant_bp = Blueprint('applicant', __name__, url_prefix="/applicant")


# ===============================
# HELPER — check ban on every request
# ===============================
def check_banned():
    """Returns a redirect response if the user is banned, else None."""
    if current_user.is_authenticated and current_user.is_banned:
        from flask import render_template as rt
        return rt("account_banned.html", user=current_user)
    return None


# ===============================
# HELPER — profile completion check
# Minimum required: first_name, last_name, phone_number, city, country
# ===============================
def is_profile_complete(prof):
    if not prof:
        return False
    return all([
        prof.first_name,
        prof.last_name,
        prof.phone_number,
        prof.city,
        prof.country,
    ])


# ===============================
# HELPER — get or create profile
# ===============================
def get_or_create_profile():
    profile = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = ApplicantProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    return profile


# ===============================
# APPLICANT PROFILE
# ===============================
@applicant_bp.route('/profile')
@login_required
def profile():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import Follow

    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()

    experiences    = WorkExperience.query.filter_by(profile_id=prof.id).order_by(WorkExperience.created_at.desc()).all() if prof else []
    educations     = Education.query.filter_by(profile_id=prof.id).order_by(Education.created_at.desc()).all() if prof else []
    skills         = Skill.query.filter_by(profile_id=prof.id).all() if prof else []
    projects       = Project.query.filter_by(profile_id=prof.id).order_by(Project.created_at.desc()).all() if prof else []
    certifications = Certification.query.filter_by(profile_id=prof.id).order_by(Certification.created_at.desc()).all() if prof else []

    follower_rows  = Follow.query.filter_by(followed_id=current_user.id).all()
    following_rows = Follow.query.filter_by(follower_id=current_user.id).all()

    from models import User as UserModel
    followers = [UserModel.query.get(r.follower_id) for r in follower_rows]
    following = [UserModel.query.get(r.followed_id) for r in following_rows]
    followers = [u for u in followers if u]
    following = [u for u in following if u]

    profile_complete = is_profile_complete(prof)

    return render_template(
        'applicant/profile.html',
        profile=prof,
        experiences=experiences,
        educations=educations,
        skills=skills,
        projects=projects,
        certifications=certifications,
        follower_count=len(followers),
        following_count=len(following),
        followers=followers,
        following=following,
        profile_complete=profile_complete,
    )


# ===============================
# UPDATE PERSONAL INFO
# ===============================
@applicant_bp.route('/profile/update-personal', methods=['POST'])
@login_required
def update_personal():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    prof.first_name   = request.form.get('first_name', '').strip()
    prof.last_name    = request.form.get('last_name', '').strip()
    prof.middle_name  = request.form.get('middle_name', '').strip()
    prof.gender       = request.form.get('gender', '').strip()
    prof.phone_number = request.form.get('phone_number', '').strip()
    prof.country      = request.form.get('country', '').strip()
    prof.city         = request.form.get('city', '').strip()
    prof.home_address = request.form.get('home_address', '').strip()
    prof.headline     = request.form.get('headline', '').strip()
    prof.bio          = request.form.get('bio', '').strip()

    dob_str = request.form.get('date_of_birth', '').strip()
    if dob_str:
        try:
            prof.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except:
            pass

    # Sync profile_completed flag on User
    current_user.profile_completed = is_profile_complete(prof)
    db.session.commit()

    flash("Personal information updated!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# UPDATE SOCIAL LINKS
# ===============================
@applicant_bp.route('/profile/update-social', methods=['POST'])
@login_required
def update_social():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()
    prof.linkedin  = request.form.get('linkedin', '').strip()
    prof.github    = request.form.get('github', '').strip()
    prof.portfolio = request.form.get('portfolio', '').strip()

    db.session.commit()
    flash("Social links updated!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# WORK EXPERIENCE — ADD
# ===============================
@applicant_bp.route('/profile/add-experience', methods=['POST'])
@login_required
def add_experience():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    exp = WorkExperience(
        profile_id  = prof.id,
        job_title   = request.form.get('job_title', '').strip(),
        company     = request.form.get('company', '').strip(),
        location    = request.form.get('location', '').strip(),
        start_date  = request.form.get('start_date', '').strip(),
        end_date    = request.form.get('end_date', '').strip() if not request.form.get('is_current') else None,
        is_current  = bool(request.form.get('is_current')),
        description = request.form.get('description', '').strip()
    )
    db.session.add(exp)
    db.session.commit()
    flash("Work experience added!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# WORK EXPERIENCE — DELETE
# ===============================
@applicant_bp.route('/profile/delete-experience/<int:exp_id>', methods=['POST'])
@login_required
def delete_experience(exp_id):
    exp = WorkExperience.query.get_or_404(exp_id)
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or exp.profile_id != prof.id:
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))
    db.session.delete(exp)
    db.session.commit()
    flash("Work experience removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# EDUCATION — ADD
# ===============================
@applicant_bp.route('/profile/add-education', methods=['POST'])
@login_required
def add_education():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    edu = Education(
        profile_id     = prof.id,
        school         = request.form.get('school', '').strip(),
        degree         = request.form.get('degree', '').strip(),
        field_of_study = request.form.get('field_of_study', '').strip(),
        start_date     = request.form.get('start_date', '').strip(),
        end_date       = request.form.get('end_date', '').strip() if not request.form.get('is_current') else None,
        is_current     = bool(request.form.get('is_current')),
        description    = request.form.get('description', '').strip()
    )
    db.session.add(edu)
    db.session.commit()
    flash("Education added!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# EDUCATION — DELETE
# ===============================
@applicant_bp.route('/profile/delete-education/<int:edu_id>', methods=['POST'])
@login_required
def delete_education(edu_id):
    edu = Education.query.get_or_404(edu_id)
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or edu.profile_id != prof.id:
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))
    db.session.delete(edu)
    db.session.commit()
    flash("Education removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# SKILL — ADD
# ===============================
@applicant_bp.route('/profile/add-skill', methods=['POST'])
@login_required
def add_skill():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    skill = Skill(
        profile_id = prof.id,
        name       = request.form.get('name', '').strip(),
        level      = request.form.get('level', 'Beginner').strip()
    )
    db.session.add(skill)
    db.session.commit()
    flash("Skill added!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# SKILL — DELETE
# ===============================
@applicant_bp.route('/profile/delete-skill/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or skill.profile_id != prof.id:
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))
    db.session.delete(skill)
    db.session.commit()
    flash("Skill removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# PROJECT — ADD
# ===============================
@applicant_bp.route('/profile/add-project', methods=['POST'])
@login_required
def add_project():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    proj = Project(
        profile_id  = prof.id,
        title       = request.form.get('title', '').strip(),
        description = request.form.get('description', '').strip(),
        url         = request.form.get('url', '').strip(),
        start_date  = request.form.get('start_date', '').strip(),
        end_date    = request.form.get('end_date', '').strip()
    )
    db.session.add(proj)
    db.session.commit()
    flash("Project added!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# PROJECT — DELETE
# ===============================
@applicant_bp.route('/profile/delete-project/<int:proj_id>', methods=['POST'])
@login_required
def delete_project(proj_id):
    proj = Project.query.get_or_404(proj_id)
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or proj.profile_id != prof.id:
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))
    db.session.delete(proj)
    db.session.commit()
    flash("Project removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# CERTIFICATION — ADD
# ===============================
@applicant_bp.route('/profile/add-certification', methods=['POST'])
@login_required
def add_certification():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    cert = Certification(
        profile_id     = prof.id,
        name           = request.form.get('name', '').strip(),
        issuer         = request.form.get('issuer', '').strip(),
        issue_date     = request.form.get('issue_date', '').strip(),
        expiry_date    = request.form.get('expiry_date', '').strip(),
        credential_url = request.form.get('credential_url', '').strip()
    )
    db.session.add(cert)
    db.session.commit()
    flash("Certification added!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# CERTIFICATION — DELETE
# ===============================
@applicant_bp.route('/profile/delete-certification/<int:cert_id>', methods=['POST'])
@login_required
def delete_certification(cert_id):
    cert = Certification.query.get_or_404(cert_id)
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or cert.profile_id != prof.id:
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))
    db.session.delete(cert)
    db.session.commit()
    flash("Certification removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# UPLOAD PROFILE PICTURE
# ===============================
@applicant_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    cropped_data = request.form.get('cropped_image')
    if not cropped_data:
        flash("No image data received.", "danger")
        return redirect(url_for('applicant.profile'))

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

    return redirect(url_for('applicant.profile'))


# ===============================
# APPLICANT DASHBOARD
# ── Gated: profile must be complete to apply for jobs
# ===============================
@applicant_bp.route('/dashboard')
@login_required
def dashboard():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    applications = (
        Application.query
        .filter_by(applicant_id=current_user.id)
        .options(
            joinedload(Application.job),
            joinedload(Application.hr_feedbacks)
        )
        .order_by(Application.created_at.desc())
        .all()
    )

    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    profile_complete = is_profile_complete(prof)

    return render_template(
        'applicant/dashboard.html',
        applications=applications,
        profile_complete=profile_complete,
    )


# ===============================
# JOB DETAILS
# ===============================
@applicant_bp.route('/job/<int:job_id>')
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    job_owner = User.query.get(job.company_id)
    return render_template("applicant/job_details.html", job=job, job_owner=job_owner)


# ===============================
# APPLY FOR JOB
# ── Requires profile completion (not admin verification)
# ===============================
@applicant_bp.route('/apply/<int:job_id>', methods=["GET", "POST"])
@login_required
def apply_job(job_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Gate: profile must be complete to apply
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not is_profile_complete(prof):
        flash("Please complete your profile before applying for jobs.", "warning")
        return redirect(url_for('applicant.profile'))

    job = Job.query.get_or_404(job_id)

    existing = Application.query.filter_by(
        applicant_id=current_user.id,
        job_id=job_id
    ).first()

    if existing:
        flash("You already applied for this job!", "warning")
        return redirect(url_for('applicant.dashboard'))

    if request.method == "POST":
        cover_letter = request.form.get("cover_letter")
        resume_file  = request.files.get("resume")
        resume_filename = None

        if resume_file and resume_file.filename != "":
            upload_folder = os.path.join(current_app.root_path, "static", "uploads", "applicant_resumes")
            os.makedirs(upload_folder, exist_ok=True)
            filename        = secure_filename(resume_file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            resume_file.save(os.path.join(upload_folder, unique_filename))
            resume_filename = unique_filename

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

    return render_template("applicant/apply_job.html", job=job)