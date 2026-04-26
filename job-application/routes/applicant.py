from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import (
    db, Job, Application, User,
    ApplicantProfile, WorkExperience,
    ApplicantEducation,
    Skill, Project, Certification,
    RecruiterNotification, HRNotification, ApplicantNotification,
    SavedJob, Employee
)
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime, date
import base64
import io
import os
import uuid
import json

applicant_bp = Blueprint('applicant', __name__, url_prefix="/applicant")


# ===============================
# HELPER — check ban on every request
# ===============================
def check_banned():
    if current_user.is_authenticated and current_user.is_banned:
        from flask import render_template as rt
        return rt("account_banned.html", user=current_user)
    return None


# ===============================
# HELPER — profile completion check
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
        prof.home_address,
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


# ================================================================
# BEFORE REQUEST GATE
# ================================================================
@applicant_bp.before_request
def gate_applicant_features():
    if not current_user.is_authenticated:
        return
    if current_user.role != 'applicant':
        return

    db.session.expire(current_user)

    if getattr(current_user, 'profile_completed', False):
        return

    ALLOWED = {
        'applicant.profile',
        'applicant.update_personal',
        'applicant.update_social',
        'applicant.upload_profile_picture',
        'applicant.add_experience',     'applicant.delete_experience',
        'applicant.add_education',      'applicant.delete_education',
        'applicant.add_project',        'applicant.delete_project',
        'applicant.add_skill',          'applicant.delete_skill',
        'applicant.add_certification',  'applicant.delete_certification',
        'applicant.upload_resume',      'applicant.delete_resume',
        'applicant.upload_portfolio',   'applicant.delete_portfolio',
        'applicant.upload_certificate', 'applicant.delete_certificate',
        'applicant.upload_experience_certificates',
        'applicant.delete_experience_certificate',
        'applicant.archived',
        'auth.logout',
    }

    if request.endpoint not in ALLOWED:
        flash("Please complete your profile first to access this feature.", "info")
        return redirect(url_for('applicant.profile'))


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
    educations     = ApplicantEducation.query.filter_by(profile_id=prof.id).order_by(ApplicantEducation.created_at.desc()).all() if prof else []
    skills         = Skill.query.filter_by(profile_id=prof.id).all() if prof else []
    projects       = Project.query.filter_by(profile_id=prof.id).order_by(Project.created_at.desc()).all() if prof else []
    certifications = Certification.query.filter_by(profile_id=prof.id).order_by(Certification.created_at.desc()).all() if prof else []

    follower_rows  = Follow.query.filter_by(followed_id=current_user.id).all()
    following_rows = Follow.query.filter_by(follower_id=current_user.id).all()

    from models import User as UserModel
    followers = [UserModel.query.get(r.follower_id) for r in follower_rows]
    following = [UserModel.query.get(r.followed_id) for r in following_rows]
    followers = [u for u in followers if u and not u.is_banned and not u.is_deleted]
    following = [u for u in following if u and not u.is_banned and not u.is_deleted]

    profile_complete = is_profile_complete(prof)

    if profile_complete and not current_user.profile_completed:
        current_user.profile_completed = True
        db.session.commit()
    elif not profile_complete and current_user.profile_completed:
        current_user.profile_completed = False
        db.session.commit()

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
        profile_completed=profile_complete,
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
        except Exception:
            pass

    was_complete = getattr(current_user, 'profile_completed', False)

    if not was_complete and is_profile_complete(prof):
        current_user.profile_completed = True
        notif = ApplicantNotification(
            applicant_id=current_user.id,
            type='profile_complete',
            message='Your profile is now <strong>complete</strong>! You can now browse and apply for jobs on the platform.',
        )
        db.session.add(notif)

    from models import FollowRequest, UserSettings, Follow
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()

    show_profile = (settings.show_profile if settings else 'everyone') or 'everyone'
    try:
        audience = json.loads(settings.profile_audience_json) if (settings and settings.profile_audience_json) else ['recruiter', 'hr', 'follower']
    except Exception:
        audience = ['recruiter', 'hr', 'follower']

    pending_reqs = FollowRequest.query.filter_by(
        receiver_id=current_user.id, status='pending'
    ).all()

    for req in pending_reqs:
        sender = User.query.get(req.sender_id)
        if not sender:
            continue

        should_auto_accept = False

        if show_profile == 'everyone':
            should_auto_accept = True
        elif show_profile == 'specific':
            if sender.role == 'recruiter' and 'recruiter' in audience:
                should_auto_accept = True
            elif sender.role == 'hr' and 'hr' in audience:
                should_auto_accept = True

        if should_auto_accept:
            req.status = 'accepted'
            existing = Follow.query.filter_by(
                follower_id=req.sender_id, followed_id=current_user.id
            ).first()
            if not existing:
                db.session.add(Follow(follower_id=req.sender_id, followed_id=current_user.id))

    db.session.commit()
    db.session.expire(current_user)

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
    prof.facebook  = request.form.get('facebook', '').strip()
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
    db.session.flush()

    cert_files = request.files.getlist('cert_files')
    _save_experience_certs(exp.id, cert_files)

    db.session.commit()
    flash("Work experience added!", "success")
    return redirect(url_for('applicant.profile'))


def _save_experience_certs(experience_id, file_list):
    from models import WorkExperienceCertificate

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'experience_certs')
    os.makedirs(folder, exist_ok=True)

    existing_count = WorkExperienceCertificate.query.filter_by(experience_id=experience_id).count()
    allowed = {'.pdf', '.jpg', '.jpeg', '.png'}
    max_certs = 10
    saved = 0

    for f in file_list:
        if not f or not f.filename:
            continue
        if existing_count + saved >= max_certs:
            break
        ext = os.path.splitext(f.filename.lower())[1]
        if ext not in allowed:
            continue
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > 5 * 1024 * 1024:
            continue
        filename = f"ecert_{experience_id}_{uuid.uuid4().hex[:10]}{ext}"
        f.save(os.path.join(folder, filename))
        cert = WorkExperienceCertificate(
            experience_id=experience_id,
            file_path=filename,
            original_name=secure_filename(f.filename)
        )
        db.session.add(cert)
        saved += 1


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

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'experience_certs')
    for cert in exp.certificates:
        path = os.path.join(folder, cert.file_path)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(exp)
    db.session.commit()
    flash("Work experience removed.", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# EXPERIENCE CERTIFICATES — UPLOAD
# ===============================
@applicant_bp.route('/profile/experience/<int:exp_id>/upload-certs', methods=['POST'])
@login_required
def upload_experience_certificates(exp_id):
    exp = WorkExperience.query.get_or_404(exp_id)
    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or exp.profile_id != prof.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': False, 'error': 'Access denied'}), 403
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))

    from models import WorkExperienceCertificate

    existing_count = WorkExperienceCertificate.query.filter_by(experience_id=exp_id).count()
    if existing_count >= 10:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': False, 'error': 'Maximum 10 certificates per experience.'}), 400
        flash("Maximum of 10 certificates per experience reached.", "warning")
        return redirect(url_for('applicant.profile'))

    cert_files = request.files.getlist('cert_files')
    if not cert_files or all(not f.filename for f in cert_files):
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': False, 'error': 'No files provided.'}), 400
        flash("No files selected.", "danger")
        return redirect(url_for('applicant.profile'))

    _save_experience_certs(exp_id, cert_files)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        certs = WorkExperienceCertificate.query.filter_by(experience_id=exp_id).order_by(WorkExperienceCertificate.created_at).all()
        return jsonify({
            'ok': True,
            'certs': [
                {
                    'id': c.id,
                    'file_path': c.file_path,
                    'original_name': c.original_name or c.file_path,
                    'ext': c.file_path.rsplit('.', 1)[-1].lower(),
                    'url': url_for('static', filename='uploads/experience_certs/' + c.file_path),
                    'delete_url': url_for('applicant.delete_experience_certificate', cert_id=c.id),
                }
                for c in certs
            ],
            'count': len(certs),
        })

    flash("Certificate(s) uploaded!", "success")
    return redirect(url_for('applicant.profile'))


# ===============================
# EXPERIENCE CERTIFICATES — DELETE
# ===============================
@applicant_bp.route('/profile/experience-cert/<int:cert_id>/delete', methods=['POST'])
@login_required
def delete_experience_certificate(cert_id):
    from models import WorkExperienceCertificate
    cert = WorkExperienceCertificate.query.get_or_404(cert_id)

    prof = ApplicantProfile.query.filter_by(user_id=current_user.id).first()
    if not prof or cert.experience.profile_id != prof.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': False, 'error': 'Access denied'}), 403
        flash("Access denied!", "danger")
        return redirect(url_for('applicant.profile'))

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'experience_certs')
    path = os.path.join(folder, cert.file_path)
    if os.path.exists(path):
        os.remove(path)

    exp_id = cert.experience_id
    db.session.delete(cert)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from models import WorkExperienceCertificate as WEC
        remaining = WEC.query.filter_by(experience_id=exp_id).count()
        return jsonify({'ok': True, 'remaining': remaining})

    flash("Certificate removed.", "success")
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

    edu = ApplicantEducation(
        profile_id     = prof.id,
        school         = request.form.get('school', '').strip(),
        education_level= request.form.get('education_level', '').strip(),
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
# FOLLOW REQUESTS — LIST (AJAX)
# ===============================
@applicant_bp.route('/follow-requests')
@login_required
def get_follow_requests():
    from models import FollowRequest
    if current_user.role != 'applicant':
        return jsonify({'error': 'forbidden'}), 403

    pending = FollowRequest.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).order_by(FollowRequest.created_at.desc()).all()

    return jsonify({
        'count': len(pending),
        'requests': [
            {
                'id':          r.id,
                'sender_id':   r.sender_id,
                'username':    r.sender.username,
                'profile_url': f'/profile/{r.sender_id}',
                'pic': (
                    r.sender.profile_picture
                    if r.sender.profile_picture and r.sender.profile_picture.startswith('http')
                    else ('/static/uploads/profile_pictures/' + r.sender.profile_picture
                          if r.sender.profile_picture else None)
                ),
                'created_at': r.created_at.strftime('%b %d, %Y'),
            }
            for r in pending
        ]
    })


# ===============================
# FOLLOW REQUESTS — RESPOND (AJAX)
# ===============================
@applicant_bp.route('/follow-request/<int:req_id>/respond', methods=['POST'])
@login_required
def respond_follow_request(req_id):
    from models import FollowRequest, Follow
    req = FollowRequest.query.get_or_404(req_id)

    if req.receiver_id != current_user.id:
        return jsonify({'ok': False, 'error': 'Access denied'}), 403

    action = request.form.get('action')  # 'accept' or 'reject'

    if action == 'accept':
        req.status = 'accepted'
        existing = Follow.query.filter_by(
            follower_id=req.sender_id, followed_id=current_user.id
        ).first()
        if not existing:
            db.session.add(Follow(follower_id=req.sender_id, followed_id=current_user.id))

        sender = User.query.get(req.sender_id)
        if sender and sender.role == 'applicant':
            notif = ApplicantNotification(
                applicant_id=req.sender_id,
                type='follow_accepted',
                message=f"<strong>{current_user.username}</strong> accepted your follow request.",
                sender_id=current_user.id,
            )
            db.session.add(notif)
        elif sender and sender.role == 'recruiter':
            from models import RecruiterNotification
            db.session.add(RecruiterNotification(
                recruiter_id=req.sender_id,
                type='follow_accepted',
                message=f"<strong>{current_user.username}</strong> accepted your follow request.",
                sender_id=current_user.id,
            ))
        elif sender and sender.role == 'hr':
            from models import HRNotification
            db.session.add(HRNotification(
                hr_id=req.sender_id,
                type='follow_accepted',
                message=f"<strong>{current_user.username}</strong> accepted your follow request.",
                sender_id=current_user.id,
            ))

        db.session.commit()
        return jsonify({'ok': True, 'action': 'accepted'})

    elif action == 'reject':
        req.status = 'rejected'
        db.session.commit()
        return jsonify({'ok': True, 'action': 'rejected'})

    return jsonify({'ok': False, 'error': 'Invalid action'}), 400


# ===============================
# APPLICATION STATUS PAGE
# ===============================
_ACTIVE_STATUSES   = ('pending', 'interview', 'accepted', 'employed')
_ARCHIVED_STATUSES = ('rejected', 'resigned', 'fired')

@applicant_bp.route('/status')
@login_required
def status():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    applications = (
        Application.query
        .join(Job, Application.job_id == Job.id)
        .join(User, Job.company_id == User.id)
        .filter(
            Application.applicant_id == current_user.id,
            Application.status.in_(_ACTIVE_STATUSES),
            User.is_banned == False
        )
        .options(joinedload(Application.job))
        .order_by(Application.created_at.desc())
        .all()
    )

    return render_template(
        'applicant/status.html',
        applications=applications,
    )

@applicant_bp.route('/archived')
@login_required
def archived():
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    archived_applications = (
        Application.query
        .filter(
            Application.applicant_id == current_user.id,
            Application.status.in_(_ARCHIVED_STATUSES)
        )
        .options(joinedload(Application.job))
        .order_by(Application.created_at.desc())
        .all()
    )

    return render_template(
        'applicant/archived.html',
        archived_applications=archived_applications,
    )

# ===============================
# APPLICATION DETAIL PAGE
# ===============================
@applicant_bp.route('/application/<int:app_id>')
@login_required
def application_detail(app_id):
    banned = check_banned()
    if banned:
        return banned

    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = (
        Application.query
        .filter_by(id=app_id, applicant_id=current_user.id)
        .options(
            joinedload(Application.job),
            joinedload(Application.hr_feedbacks),
        )
        .first_or_404()
    )

    job = application.job

    recruiter        = None
    recruiter_user   = None
    if job:
        from models import RecruiterProfile
        recruiter      = RecruiterProfile.query.filter_by(user_id=job.company_id).first()
        recruiter_user = User.query.get(job.company_id)

    return render_template(
        'applicant/application_detail.html',
        application=application,
        job=job,
        recruiter=recruiter,
        recruiter_user=recruiter_user,
    )


# ===============================
# JOB DETAILS
# ===============================
@applicant_bp.route('/job/<int:job_id>')
def job_details(job_id):
    job = Job.query.get_or_404(job_id)

    if job.is_taken_down:
        flash("This job posting is currently unavailable.", "warning")
        return redirect(url_for('auth.jobs'))

    job_owner = User.query.get(job.company_id)

    # ── Expiry check ──────────────────────────────────────────────
    is_expired = bool(job.expiration_date and job.expiration_date < date.today())
    is_closed  = not job.allow_applications

    saved_job_ids = set()
    existing_application = None
    if current_user.is_authenticated and current_user.role == 'applicant':
        saved_job_ids = {
            s.job_id for s in SavedJob.query.filter_by(applicant_id=current_user.id).all()
        }
        existing_application = Application.query.filter(
            Application.applicant_id == current_user.id,
            Application.job_id == job_id,
            Application.status.in_(_ACTIVE_STATUSES)
        ).first()

    active_application_count = Application.query.filter(
        Application.job_id == job_id,
        Application.status.in_(_ACTIVE_STATUSES)
    ).count()

    employee_count = Employee.query.join(
        Job, Employee.job_id == Job.id
    ).filter(Job.company_id == job.company_id).count()

    return render_template(
        "applicant/job_details.html",
        job=job,
        job_owner=job_owner,
        saved_job_ids=saved_job_ids,
        existing_application=existing_application,
        active_application_count=active_application_count,
        employee_count=employee_count,
        is_expired=is_expired,      # ← NEW
        is_closed=is_closed,        # ← NEW
    )


# ===============================
# APPLY FOR JOB
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

    if not getattr(current_user, 'profile_completed', False):
        flash("Please complete your profile before applying for jobs.", "warning")
        return redirect(url_for('applicant.profile'))

    job = Job.query.get_or_404(job_id)

    if job.is_taken_down:
        flash("This job posting is currently unavailable.", "warning")
        return redirect(url_for('auth.jobs'))

    # ── Block applications to expired jobs ────────────────────────
    if job.expiration_date and job.expiration_date < date.today():
        flash("This job posting has already expired and is no longer accepting applications.", "warning")
        return redirect(url_for('applicant.job_details', job_id=job_id))

    # ── Block applications when recruiter closed the listing ──────
    if not job.allow_applications:
        flash("This job posting is currently closed and not accepting applications.", "warning")
        return redirect(url_for('applicant.job_details', job_id=job_id))

    existing = Application.query.filter(
        Application.applicant_id == current_user.id,
        Application.job_id == job_id,
        Application.status.in_(_ACTIVE_STATUSES)
    ).first()

    if existing:
        flash("You already applied for this job!", "warning")
        return redirect(url_for('applicant.job_details', job_id=job_id))

    if job.max_applications is not None:
        current_count = Application.query.filter(
            Application.job_id == job_id,
            Application.status.in_(_ACTIVE_STATUSES)
        ).count()
        if current_count >= job.max_applications:
            flash("This job has reached its application quota.", "warning")
            return redirect(url_for('applicant.job_details', job_id=job_id))

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

        hr_users = User.query.filter_by(created_by=job_owner.company_id, role='hr', is_deleted=False).all()
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
        return redirect(url_for('applicant.job_details', job_id=job_id))

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
# UPLOAD CERTIFICATE (legacy global)
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
# DELETE CERTIFICATE (legacy global)
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
                'application_id': n.application_id,
                'sender_id': n.sender_id
            }
            for n in notifs
        ]
    })


@applicant_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'applicant':
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    notif_id = data.get('id')
    if notif_id:
        ApplicantNotification.query.filter_by(
            id=notif_id, applicant_id=current_user.id
        ).update({'is_read': True})
    else:
        ApplicantNotification.query.filter_by(
            applicant_id=current_user.id, is_read=False
        ).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


# ===============================
# CLEAR ALL NOTIFICATIONS
# ===============================
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
# APPLICANT NOTIFICATION HISTORY PAGE
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

    saved = [
        s for s in saved
        if s.job and not s.job.is_taken_down
        and not User.query.get(s.job.company_id).is_banned
        and not User.query.get(s.job.company_id).is_deleted
    ]

    return render_template('applicant/saved_jobs.html', saved=saved)