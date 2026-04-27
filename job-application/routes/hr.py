from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Application, Job, HRProfile, HRFeedback, User, HRNotification, ApplicantNotification, HREducation, Employee, get_ph_time  
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

    from models import RecruiterProfile, Follow

    hr_profile = current_user.hr_profile

    educations = []
    if hr_profile:
        educations = HREducation.query.filter_by(
            profile_id=hr_profile.id
        ).order_by(HREducation.created_at.desc()).all()

    recruiter_profile = None
    if current_user.created_by:
        recruiter_profile = RecruiterProfile.query.filter_by(
            user_id=current_user.created_by
        ).first()

    follower_rows  = Follow.query.filter_by(followed_id=current_user.id).all()
    following_rows = Follow.query.filter_by(follower_id=current_user.id).all()
    followers = [User.query.get(r.follower_id) for r in follower_rows]
    following = [User.query.get(r.followed_id) for r in following_rows]
    followers = [u for u in followers if u and not u.is_banned and not u.is_deleted]
    following = [u for u in following if u and not u.is_banned and not u.is_deleted]

    from models import JobTeamMember, Job
    assigned_jobs = [tm.job for tm in JobTeamMember.query.filter_by(hr_id=current_user.id).all()]

    return render_template(
        "hr/profile.html",
        profile=hr_profile,
        recruiter_profile=recruiter_profile,
        educations=educations,
        follower_count=len(followers),
        following_count=len(following),
        followers=followers,
        following=following,
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
        profile.education_level = request.form.get('education_level', '').strip()
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

        flash("Password changed successfully!", "success")
        return redirect(url_for("hr.profile"))

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

    profile.facebook  = request.form.get('facebook', '').strip()
    profile.github    = request.form.get('github', '').strip()
    profile.portfolio = request.form.get('portfolio', '').strip()

    db.session.commit()
    flash("Links updated successfully!", "success")
    return redirect(url_for('hr.profile'))

# ===============================
# ADD EDUCATION (HR)
# ===============================
@hr_bp.route('/add-education', methods=['POST'])
@login_required
def add_education():
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    profile = current_user.hr_profile
    if not profile:
        profile = HRProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()

    is_current = request.form.get('is_current') == '1'

    edu = HREducation(
        profile_id     = profile.id,
        school         = request.form.get('school', '').strip(),
        education_level= request.form.get('education_level', '').strip(),
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
    return redirect(url_for('hr.profile'))


# ===============================
# DELETE EDUCATION (HR)
# ===============================
@hr_bp.route('/delete-education/<int:edu_id>', methods=['POST'])
@login_required
def delete_education(edu_id):
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    edu = HREducation.query.get_or_404(edu_id)
    profile = current_user.hr_profile

    if not profile or edu.profile_id != profile.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('hr.profile'))

    db.session.delete(edu)
    db.session.commit()

    flash("Education removed.", "success")
    return redirect(url_for('hr.profile'))

# ===============================
# UPLOAD PORTFOLIO (HR)
# ===============================
@hr_bp.route('/profile/upload-portfolio', methods=['POST'])
@login_required
def upload_portfolio():
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = HRProfile.query.filter_by(user_id=current_user.id).first()
    if not prof:
        flash("Profile not found. Please complete your profile first.", "danger")
        return redirect(url_for('hr.profile'))

    file = request.files.get('portfolio_file')

    if not file or file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('hr.profile'))

    allowed = {'.pdf', '.jpg', '.jpeg', '.png'}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed:
        flash("Portfolio must be a PDF, JPG, or PNG file.", "danger")
        return redirect(url_for('hr.profile'))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 10 * 1024 * 1024:
        flash("Portfolio file exceeds the 10MB limit.", "danger")
        return redirect(url_for('hr.profile'))

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'hr_portfolios')
    os.makedirs(folder, exist_ok=True)

    if prof.portfolio_file:
        old = os.path.join(folder, prof.portfolio_file)
        if os.path.exists(old):
            os.remove(old)

    filename = f"hr_portfolio_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    file.save(os.path.join(folder, filename))
    prof.portfolio_file = filename
    db.session.commit()
    flash("Portfolio uploaded successfully!", "success")
    return redirect(url_for('hr.profile'))


# ===============================
# DELETE PORTFOLIO (HR)
# ===============================
@hr_bp.route('/profile/delete-portfolio', methods=['POST'])
@login_required
def delete_portfolio():
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    prof = HRProfile.query.filter_by(user_id=current_user.id).first()
    if prof and prof.portfolio_file:
        path = os.path.join(current_app.root_path, 'static', 'uploads', 'hr_portfolios', prof.portfolio_file)
        if os.path.exists(path):
            os.remove(path)
        prof.portfolio_file = None
        db.session.commit()
        flash("Portfolio removed successfully.", "success")
    else:
        flash("No portfolio file found to delete.", "warning")
    
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

    from models import JobTeamMember

    # Get IDs of jobs this HR is assigned to
    assigned_job_ids = {
        tm.job_id for tm in JobTeamMember.query.filter_by(hr_id=current_user.id).all()
    }

    # All jobs by their recruiter boss
    recruiter = User.query.get(current_user.created_by)
    all_jobs = [] if (recruiter and (recruiter.is_banned or recruiter.is_deleted)) else Job.query.filter_by(company_id=current_user.created_by).all()

    return render_template(
        "hr/job_list.html",
        jobs=all_jobs,
        assigned_job_ids=assigned_job_ids,
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

    from models import JobTeamMember

    # Check if this HR is assigned to this job
    is_assigned = JobTeamMember.query.filter_by(
        job_id=job_id,
        hr_id=current_user.id
    ).first()

    if not is_assigned:
        flash("You are not assigned to review this job.", "warning")
        return redirect(url_for('hr.job_list'))

    job = Job.query.get_or_404(job_id)

    _ACTIVE_STATUSES = ('pending', 'interview', 'waitlisted', 'accepted', 'employed')
    _ARCHIVED_STATUSES = ('rejected', 'resigned', 'fired')

    applications = (
        Application.query
        .join(User, Application.applicant_id == User.id)
        .filter(
            Application.job_id == job_id,
            Application.status.in_(_ACTIVE_STATUSES),
            User.is_banned == False,
            User.is_deleted == False
        ).all()
    )

    archived_applications = (
        Application.query
        .join(User, Application.applicant_id == User.id)
        .filter(
            Application.job_id == job_id,
            Application.status.in_(_ARCHIVED_STATUSES),
            User.is_banned == False
        ).all()
    )
    recruiter_user = User.query.get(job.company_id)

    return render_template(
        "hr/job_applications.html",
        job=job,
        applications=applications,
        archived_applications=archived_applications,
        recruiter_user=recruiter_user,
    )

@hr_bp.route('/job-applications/<int:job_id>/archived')
@login_required
def archived_applications(job_id):
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
 
    from models import JobTeamMember
 
    is_assigned = JobTeamMember.query.filter_by(
        job_id=job_id,
        hr_id=current_user.id
    ).first()
 
    if not is_assigned:
        flash("You are not assigned to review this job.", "warning")
        return redirect(url_for('hr.job_list'))
 
    job = Job.query.get_or_404(job_id)
 
    _ARCHIVED_STATUSES = ('rejected', 'resigned', 'fired')
    archived_applications = Application.query.filter(
        Application.job_id == job_id,
        Application.status.in_(_ARCHIVED_STATUSES)
    ).order_by(Application.created_at.desc()).all()
 
    return render_template(
        "shared/archived_applications.html",   # put the template in templates/shared/
        job=job,
        archived_applications=archived_applications,
        back_url=url_for('hr.job_applications', job_id=job_id),
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
    if Employee.query.filter_by(application_id=app_id).first():
        flash("This applicant is already a confirmed employee. Status cannot be changed.", "warning")
        return redirect(url_for('hr.job_applications', job_id=application.job_id))

    new_status        = request.form.get('status')
    new_feedback      = request.form.get('hr_feedback')
    interview_date_str = request.form.get('interview_date')
    interview_session  = request.form.get('interview_session')
    meeting_type_val   = request.form.get('meeting_type')
    meeting_link_val   = request.form.get('meeting_link')

    if new_status:
        application.status = new_status

    if new_status == 'interview':
        if interview_date_str:
            application.interview_date = datetime.strptime(interview_date_str, "%Y-%m-%dT%H:%M")

        if interview_session == 'online':
            application.meeting_type = meeting_type_val or None
            application.meeting_link = meeting_link_val or None
        elif interview_session == 'face-to-face':
            application.meeting_type = 'face-to-face'
            application.meeting_link = None
        # if interview_session is None, leave existing values untouched
    elif new_status in ('accepted', 'waitlisted', 'rejected', 'pending'):
        application.interview_date = None
        application.meeting_type   = None
        application.meeting_link   = None

    if new_feedback is not None and new_feedback.strip() != '':
        existing = HRFeedback.query.filter_by(
            application_id=app_id,
            hr_id=current_user.id
        ).first()

        if existing:
            existing.feedback   = new_feedback
            existing.updated_at = get_ph_time()
        else:
            new_fb = HRFeedback(
                application_id=app_id,
                hr_id=current_user.id,
                feedback=new_feedback
            )
            db.session.add(new_fb)

    db.session.commit()

    if new_status:
        applicant_user = User.query.get(application.applicant_id)
        job_for_notif  = Job.query.get(application.job_id)

        hr_notif = HRNotification(
            hr_id=current_user.id,
            type='new_application',
            message=f"Application status for <strong>{applicant_user.username}</strong> on "
                    f"<strong>{job_for_notif.title}</strong> updated to "
                    f"<strong>{new_status.capitalize()}</strong>.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(hr_notif)

        app_notif = ApplicantNotification(
            applicant_id=application.applicant_id,
            type='application_status',
            message=f"Your application for <strong>{job_for_notif.title}</strong> has been "
                    f"updated to <strong>{new_status.capitalize()}</strong>.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(app_notif)
        db.session.commit()

    flash("Application updated successfully!", "success")
    return redirect(url_for('hr.job_applications', job_id=application.job_id))

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

        applicant = User.query.get(application.applicant_id)
        job_notif = Job.query.get(application.job_id)

        # --- HR NOTIFICATION: interview scheduled (HR's own log) ---
        hr_notif = HRNotification(
            hr_id=current_user.id,
            type='interview_scheduled',
            message=f"Interview scheduled for <strong>{applicant.username}</strong> applying for <strong>{job_notif.title}</strong> on {application.interview_date.strftime('%b %d, %Y at %I:%M %p')}.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(hr_notif)

        # --- APPLICANT NOTIFICATION: interview scheduled ---
        app_notif = ApplicantNotification(
            applicant_id=application.applicant_id,
            type='interview_scheduled',
            message=f"An interview has been scheduled for your application to <strong>{job_notif.title}</strong> on <strong>{application.interview_date.strftime('%b %d, %Y at %I:%M %p')}</strong>.",
            application_id=application.id,
            job_id=application.job_id
        )
        db.session.add(app_notif)
        db.session.commit()

        flash("Interview scheduled successfully!", "success")
    else:
        flash("Please provide a valid date and time.", "danger")

    return redirect(
        url_for('hr.job_applications', job_id=application.job_id)
    )


# ===============================
# HR NOTIFICATIONS API
# ===============================
from flask import jsonify

@hr_bp.route('/notifications')
@login_required
def get_notifications():
    if current_user.role != 'hr':
        return jsonify({'error': 'forbidden'}), 403
    notifs = HRNotification.query.filter_by(
        hr_id=current_user.id
    ).order_by(HRNotification.created_at.desc()).limit(50).all()
    unread_count = HRNotification.query.filter_by(
        hr_id=current_user.id, is_read=False
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
                'sender_id': n.sender_id
            }
            for n in notifs
        ]
    })

@hr_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'hr':
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    notif_id = data.get('id')
    if notif_id:
        HRNotification.query.filter_by(
            id=notif_id, hr_id=current_user.id
        ).update({'is_read': True})
    else:
        HRNotification.query.filter_by(
            hr_id=current_user.id, is_read=False
        ).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})

@hr_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    if current_user.role != 'hr':
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'forbidden'}), 403
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
 
    HRNotification.query.filter_by(hr_id=current_user.id).delete()
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})
 
    flash("All notifications cleared.", "success")
    return redirect(url_for('hr.notification_history'))


# ===============================
# HR NOTIFICATION HISTORY PAGE
# ===============================
@hr_bp.route('/notification-history')
@login_required
def notification_history():
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
    notifs = HRNotification.query.filter_by(
        hr_id=current_user.id
    ).order_by(HRNotification.created_at.desc()).all()
    # Mark all as read when page is opened
    HRNotification.query.filter_by(
        hr_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return render_template('hr/notification_history.html', notifications=notifs)