from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import (
    db, Job, Application, User,
    ApplicantProfile, WorkExperience,
    ApplicantEducation,
    Skill, Project, Certification,
    RecruiterNotification, HRNotification, ApplicantNotification,
    SavedJob
)   
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import base64
import io
import os
import uuid
import json

applicant_bp = Blueprint('applicant', __name__, url_prefix="/applicant")


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
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import Follow

    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()

    experiences    = WorkExperience.query.filter_by(profile_id=prof.id).order_by(WorkExperience.created_at.desc()).all()    if prof else []
    educations     = ApplicantEducation.query.filter_by(profile_id=prof.id).order_by(ApplicantEducation.created_at.desc()).all() if prof else []
    skills         = Skill.query.filter_by(profile_id=prof.id).all()                                                        if prof else []
    projects       = Project.query.filter_by(profile_id=prof.id).order_by(Project.created_at.desc()).all()                 if prof else []
    certifications = Certification.query.filter_by(profile_id=prof.id).order_by(Certification.created_at.desc()).all()     if prof else []

    follower_rows  = Follow.query.filter_by(followed_id=current_user.id).all()
    following_rows = Follow.query.filter_by(follower_id=current_user.id).all()

    from models import User as UserModel
    followers = [UserModel.query.get(r.follower_id) for r in follower_rows]
    following = [UserModel.query.get(r.followed_id) for r in following_rows]
    followers = [u for u in followers if u]
    following = [u for u in following if u]

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
    )


# ===============================
# UPDATE PERSONAL INFO
# ===============================
@applicant_bp.route('/profile/update-personal', methods=['POST'])
@login_required
def update_personal():
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

    db.session.commit()
    flash("Personal information updated!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# UPDATE SOCIAL LINKS
# ===============================
@applicant_bp.route('/profile/update-social', methods=['POST'])
@login_required
def update_social():
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
# EDUCATION — ADD  (applicant-only)
# ===============================
@applicant_bp.route('/profile/add-education', methods=['POST'])
@login_required
def add_education():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()

    # ── Write into applicant_education, never recruiter_education ──
    edu = ApplicantEducation(
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
# EDUCATION — DELETE  (applicant-only)
# ===============================
@applicant_bp.route('/profile/delete-education/<int:edu_id>', methods=['POST'])
@login_required
def delete_education(edu_id):
    edu = ApplicantEducation.query.get_or_404(edu_id)
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


@applicant_bp.route('/status')
@login_required
def status():
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

    saved_job_ids = {
        s.job_id for s in SavedJob.query.filter_by(applicant_id=current_user.id).all()
    }

    return render_template(
        'applicant/status.html',
        applications=applications,
        saved_job_ids=saved_job_ids
    )


# ===============================
# JOB DETAILS
# ===============================
@applicant_bp.route('/job/<int:job_id>')
def job_details(job_id):
    from models import SavedJob
    job = Job.query.get_or_404(job_id)
    job_owner = User.query.get(job.company_id)

    saved_job_ids = set()
    if current_user.is_authenticated and current_user.role == 'applicant':
        saved_job_ids = {
            s.job_id for s in SavedJob.query.filter_by(applicant_id=current_user.id).all()
        }

    return render_template("applicant/job_details.html", job=job, job_owner=job_owner, saved_job_ids=saved_job_ids)


# ===============================
# APPLY FOR JOB
# ===============================
@applicant_bp.route('/apply/<int:job_id>', methods=["GET", "POST"])
@login_required
def apply_job(job_id):
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if not current_user.is_verified:
        flash("Your account is still waiting for admin verification.", "warning")
        return redirect(url_for('applicant.status'))

    job = Job.query.get_or_404(job_id)

    existing = Application.query.filter_by(
        applicant_id=current_user.id,
        job_id=job_id
    ).first()

    if existing:
        flash("You already applied for this job!", "warning")
        return redirect(url_for('applicant.status'))

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

        job_owner = Job.query.get(application.job_id)
        notif = RecruiterNotification(
            recruiter_id=job_owner.company_id,
            type='new_application',
            message=f"<strong>{current_user.username}</strong> has applied for your job posting: <strong>{job_owner.title}</strong>.",
            application_id=application.id,
            job_id=job_id
        )
        db.session.add(notif)

        hr_users = User.query.filter_by(
            created_by=job_owner.company_id,
            role='hr'
        ).all()

        for hr in hr_users:
            hr_notif = HRNotification(
                hr_id=hr.id,
                type='new_application',
                message=f"<strong>{current_user.username}</strong> has applied for <strong>{job_owner.title}</strong>.",
                application_id=application.id,
                job_id=job_id
            )
            db.session.add(hr_notif)

        app_notif = ApplicantNotification(
            applicant_id=current_user.id,
            type='job_update',
            message=f"Your application for <strong>{job_owner.title}</strong> has been submitted successfully.",
            application_id=application.id,
            job_id=job_id
        )
        db.session.add(app_notif)

        db.session.commit()

        flash("Application submitted successfully!", "success")
        return redirect(url_for('applicant.status'))

    return render_template("applicant/apply_job.html", job=job)


# ===============================
# UPLOAD RESUME
# ===============================
@applicant_bp.route('/profile/upload-resume', methods=['POST'])
@login_required
def upload_resume():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()
    file = request.files.get('resume_file')

    if not file or file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('applicant.profile'))

    if not file.filename.lower().endswith('.pdf'):
        flash("Resume must be a PDF file.", "danger")
        return redirect(url_for('applicant.profile'))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        flash("Resume exceeds the 5MB limit.", "danger")
        return redirect(url_for('applicant.profile'))

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'applicant_resumes')
    os.makedirs(folder, exist_ok=True)

    if prof.resume_file:
        old = os.path.join(folder, prof.resume_file)
        if os.path.exists(old):
            os.remove(old)

    filename = f"resume_{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
    file.save(os.path.join(folder, filename))
    prof.resume_file = filename
    db.session.commit()
    flash("Resume uploaded successfully!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# DELETE RESUME
# ===============================
@applicant_bp.route('/profile/delete-resume', methods=['POST'])
@login_required
def delete_resume():
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if prof and prof.resume_file:
        path = os.path.join(current_app.root_path, 'static', 'uploads', 'applicant_resumes', prof.resume_file)
        if os.path.exists(path):
            os.remove(path)
        prof.resume_file = None
        db.session.commit()
        flash("Resume removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# UPLOAD PORTFOLIO
# ===============================
@applicant_bp.route('/profile/upload-portfolio', methods=['POST'])
@login_required
def upload_portfolio():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()
    file = request.files.get('portfolio_file')

    if not file or file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('applicant.profile'))

    allowed = {'.pdf', '.jpg', '.jpeg', '.png'}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed:
        flash("Portfolio must be a PDF, JPG, or PNG file.", "danger")
        return redirect(url_for('applicant.profile'))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 10 * 1024 * 1024:
        flash("Portfolio file exceeds the 10MB limit.", "danger")
        return redirect(url_for('applicant.profile'))

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'applicant_resumes')
    os.makedirs(folder, exist_ok=True)

    if prof.portfolio_file:
        old = os.path.join(folder, prof.portfolio_file)
        if os.path.exists(old):
            os.remove(old)

    filename = f"portfolio_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    file.save(os.path.join(folder, filename))
    prof.portfolio_file = filename
    db.session.commit()
    flash("Portfolio uploaded successfully!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# DELETE PORTFOLIO
# ===============================
@applicant_bp.route('/profile/delete-portfolio', methods=['POST'])
@login_required
def delete_portfolio():
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if prof and prof.portfolio_file:
        path = os.path.join(current_app.root_path, 'static', 'uploads', 'applicant_resumes', prof.portfolio_file)
        if os.path.exists(path):
            os.remove(path)
        prof.portfolio_file = None
        db.session.commit()
        flash("Portfolio removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# UPLOAD CERTIFICATE
# ===============================
@applicant_bp.route('/profile/upload-certificate', methods=['POST'])
@login_required
def upload_certificate():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = get_or_create_profile()
    file = request.files.get('certificate_file')

    if not file or file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('applicant.profile'))

    allowed = {'.pdf', '.jpg', '.jpeg', '.png'}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed:
        flash("Certificate must be a PDF, JPG, or PNG file.", "danger")
        return redirect(url_for('applicant.profile'))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        flash("Certificate file exceeds the 5MB limit.", "danger")
        return redirect(url_for('applicant.profile'))

    existing = json.loads(prof.certificate_files) if prof.certificate_files else []
    if len(existing) >= 5:
        flash("You can upload a maximum of 5 certificates.", "warning")
        return redirect(url_for('applicant.profile'))

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'applicant_resumes')
    os.makedirs(folder, exist_ok=True)

    filename = f"cert_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    file.save(os.path.join(folder, filename))
    existing.append(filename)
    prof.certificate_files = json.dumps(existing)
    db.session.commit()
    flash("Certificate uploaded successfully!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# DELETE CERTIFICATE
# ===============================
@applicant_bp.route('/profile/delete-certificate/<filename>', methods=['POST'])
@login_required
def delete_certificate(filename):
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof:
        return redirect(url_for('applicant.profile'))

    certs = json.loads(prof.certificate_files) if prof.certificate_files else []
    if filename in certs:
        path = os.path.join(current_app.root_path, 'static', 'uploads', 'applicant_resumes', filename)
        if os.path.exists(path):
            os.remove(path)
        certs.remove(filename)
        prof.certificate_files = json.dumps(certs)
        db.session.commit()
        flash("Certificate removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# APPLICANT NOTIFICATIONS API
# ===============================
@applicant_bp.route('/notifications')
@login_required
def get_notifications():
    if current_user.role != 'applicant':
        return jsonify({'error': 'forbidden'}), 403
    notifs = ApplicantNotification.query.filter_by(
        applicant_id=current_user.id
    ).order_by(ApplicantNotification.created_at.desc()).limit(50).all()
    unread_count = ApplicantNotification.query.filter_by(
        applicant_id=current_user.id, is_read=False
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
                'job_id': n.job_id,
                'application_id': n.application_id
            }
            for n in notifs
        ]
    })


@applicant_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'applicant':
        return jsonify({'error': 'forbidden'}), 403
    ApplicantNotification.query.filter_by(
        applicant_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


@applicant_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    if current_user.role != 'applicant':
        if request.is_json:
            return jsonify({'error': 'forbidden'}), 403
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    ApplicantNotification.query.filter_by(
        applicant_id=current_user.id
    ).delete()
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})

    flash("All notifications cleared.", "success")
    return redirect(url_for('applicant.notification_history'))


# ===============================
# NOTIFICATION HISTORY PAGE
# ===============================
@applicant_bp.route('/notification-history')
@login_required
def notification_history():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
    notifs = ApplicantNotification.query.filter_by(
        applicant_id=current_user.id
    ).order_by(ApplicantNotification.created_at.desc()).all()
    ApplicantNotification.query.filter_by(
        applicant_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return render_template('applicant/notification_history.html', notifications=notifs)

# ===============================
# SAVE / UNSAVE JOB (AJAX)
# ===============================
@applicant_bp.route('/save-job/<int:job_id>', methods=['POST'])
@login_required
def save_job(job_id):
    if current_user.role != 'applicant':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    existing = SavedJob.query.filter_by(
        applicant_id=current_user.id,
        job_id=job_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'saved': False})
    else:
        saved = SavedJob(applicant_id=current_user.id, job_id=job_id)
        db.session.add(saved)
        db.session.commit()
        return jsonify({'success': True, 'saved': True})


# ===============================
# SAVED JOBS PAGE
# ===============================
@applicant_bp.route('/saved-jobs')
@login_required
def saved_jobs():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    saved = SavedJob.query.filter_by(
        applicant_id=current_user.id
    ).order_by(SavedJob.created_at.desc()).all()

    # Get the IDs of all saved jobs for the bookmark check
    saved_job_ids = {s.job_id for s in saved}

    return render_template(
        'applicant/saved_jobs.html',
        saved=saved,
        saved_job_ids=saved_job_ids
    )