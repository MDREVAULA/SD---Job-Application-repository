from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Job, User, Application, JobImage, HRFeedback
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

    from models import RecruiterProfile, Education, Follow

    jobs = Job.query.filter_by(company_id=current_user.id).all()
    hrs = User.query.filter_by(created_by=current_user.id, role='hr').all()
    rec_profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()

    educations = []
    if rec_profile:
        educations = Education.query.filter_by(profile_id=rec_profile.id).order_by(Education.created_at.desc()).all()

    follower_rows  = Follow.query.filter_by(followed_id=current_user.id).all()
    following_rows = Follow.query.filter_by(follower_id=current_user.id).all()
    followers = [User.query.get(r.follower_id) for r in follower_rows]
    following = [User.query.get(r.followed_id) for r in following_rows]
    followers = [u for u in followers if u]
    following = [u for u in following if u]

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
    )


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
        profile.surname      = request.form.get('last_name', '').strip()       # ← fixed: was profile.last_name
        profile.gender       = request.form.get('gender', '').strip()
        profile.phone_number = request.form.get('phone_number', '').strip()
        profile.home_address = request.form.get('home_address', '').strip()
        profile.headline     = request.form.get('headline', '').strip()        # ← new
        profile.bio          = request.form.get('bio', '').strip()             # ← new
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            try:
                profile.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                pass

    elif section == 'company':
        profile.company_name         = request.form.get('company_name', '').strip()
        profile.company_industry     = request.form.get('industry', '').strip()        # ← fixed: was profile.industry
        profile.country              = request.form.get('country', '').strip()
        profile.city                 = request.form.get('city', '').strip()
        profile.company_address      = request.form.get('company_address', '').strip()
        profile.company_email_domain = request.form.get('company_website', '').strip() # ← fixed: was profile.company_website
        profile.company_description  = request.form.get('company_description', '').strip()

    elif section == 'account':
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != current_user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                flash("That username is already taken.", "danger")
                return redirect(url_for('recruiter.profile'))
            current_user.username = new_username

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('recruiter.profile'))


# ===============================
# UPDATE SOCIAL LINKS
# ===============================
@recruiter_bp.route('/update-social', methods=['POST'])
@login_required
def update_social():

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
# ADD EDUCATION
# ===============================
@recruiter_bp.route('/add-education', methods=['POST'])
@login_required
def add_education():

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile, Education

    profile = current_user.recruiter_profile
    if not profile:
        profile = RecruiterProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()

    is_current = request.form.get('is_current') == '1'

    edu = Education(
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
# DELETE EDUCATION
# ===============================
@recruiter_bp.route('/delete-education/<int:edu_id>', methods=['POST'])
@login_required
def delete_education(edu_id):

    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import Education

    edu = Education.query.get_or_404(edu_id)

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

    # ── Requirements tab fields ──
    arrangement        = request.form.get('arrangement')
    experience_level   = request.form.get('experience_level')
    years_exp          = request.form.get('years_exp')
    education          = request.form.get('education')
    required_skills    = request.form.get('required_skills')
    preferred_skills   = request.form.get('preferred_skills')
    languages          = request.form.get('languages')
    requirements_notes = request.form.get('requirements_notes')

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
        expiration_date=expiration,
        # ── newly saved fields ──
        arrangement=arrangement,
        experience_level=experience_level,
        years_exp=years_exp,
        education=education,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        languages=languages,
        requirements_notes=requirements_notes,
    )

    db.session.add(job)
    db.session.commit()

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
    new_remarks = request.form.get('recruiter_remarks')

    if new_status:
        application.status = new_status

    if new_remarks is not None:
        application.recruiter_remarks = new_remarks

    db.session.commit()

    flash("Application status updated!", "success")

    return redirect(url_for('recruiter.view_job_applications', job_id=job.id))


# ===============================
# RECRUITER SCHEDULE INTERVIEW
# ===============================
@recruiter_bp.route('/schedule-interview/<int:app_id>', methods=['POST'])
@login_required
def schedule_interview(app_id):

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
        flash("Interview scheduled successfully!", "success")
    else:
        flash("Please provide a valid date and time.", "danger")

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

        poster_files = request.files.getlist("posters")

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

# ================================================================
# PUBLIC PROFILE ROUTES
# File: routes/profile_view.py
# ================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import (
    db, User, ApplicantProfile, WorkExperience,
    Education, Skill, Project, Certification, Job, Follow
)
from datetime import date

profile_view_bp = Blueprint('profile_view', __name__, url_prefix='/profile')


# ── SMART REDIRECT — /profile/<user_id> → correct role view ──
@profile_view_bp.route('/<int:user_id>')
def view_profile(user_id):
    """
    Smart redirect: detects the user's role and sends the viewer
    to the correct public profile page.
    Also prevents logged-in users from viewing their own profile through
    this route (redirects them to their editable profile instead).
    """
    user = User.query.get_or_404(user_id)

    # Redirect self to their own editable profile (only if logged in)
    if current_user.is_authenticated and current_user.id == user_id:
        if user.role == 'applicant':
            return redirect(url_for('applicant.profile'))
        elif user.role == 'hr':
            return redirect(url_for('hr.profile'))
        elif user.role == 'recruiter':
            return redirect(url_for('recruiter.profile'))

    # Route to the correct public view
    if user.role == 'applicant':
        return redirect(url_for('profile_view.view_applicant_profile', user_id=user_id))
    elif user.role == 'hr':
        return redirect(url_for('profile_view.view_hr_profile', user_id=user_id))
    elif user.role == 'recruiter':
        return redirect(url_for('profile_view.view_recruiter_profile', user_id=user_id))
    else:
        abort(404)


# ── APPLICANT PUBLIC PROFILE ──
@profile_view_bp.route('/applicant/<int:user_id>')
@login_required
def view_applicant_profile(user_id):
    """
    Public read-only view of an applicant's profile.
    Accessible by any logged-in user (recruiter, hr, other applicants).
    """
    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'applicant':
        flash("This profile is not an applicant.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    # Redirect self to own editable profile
    if current_user.id == user_id:
        return redirect(url_for('applicant.profile'))

    prof = ApplicantProfile.query.filter_by(user_id=user_id).first()

    experiences    = WorkExperience.query.filter_by(profile_id=prof.id).order_by(WorkExperience.created_at.desc()).all() if prof else []
    educations     = Education.query.filter_by(profile_id=prof.id).order_by(Education.created_at.desc()).all() if prof else []
    skills         = Skill.query.filter_by(profile_id=prof.id).all() if prof else []
    projects       = Project.query.filter_by(profile_id=prof.id).order_by(Project.created_at.desc()).all() if prof else []
    certifications = Certification.query.filter_by(profile_id=prof.id).order_by(Certification.created_at.desc()).all() if prof else []

    return render_template(
        'applicant/view_profile.html',
        viewed_user=viewed_user,
        profile=prof,
        experiences=experiences,
        educations=educations,
        skills=skills,
        projects=projects,
        certifications=certifications
    )


# ── HR PUBLIC PROFILE ──
# routes/profile_view.py — fix view_hr_profile
@profile_view_bp.route('/hr/<int:user_id>')
@login_required
def view_hr_profile(user_id):
    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'hr':
        flash("This profile is not an HR member.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    if current_user.id == user_id:
        return redirect(url_for('hr.profile'))

    followers, following = _get_follow_lists(user_id)  # add this

    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first() is not None

    return render_template(
        'hr/view_profile.html',
        viewed_user=viewed_user,
        is_following=is_following,       # add these
        followers=followers,
        following=following,
        follower_count=len(followers),
        following_count=len(following),
    )


# ── RECRUITER PUBLIC PROFILE ──
# NOTE: No @login_required — guests can view recruiter profiles
@profile_view_bp.route('/recruiter/<int:user_id>')
def view_recruiter_profile(user_id):
    """
    Public read-only view of a recruiter's profile.
    Accessible by guests AND logged-in users.
    Guests can see everything but Follow/Message buttons redirect to login.
    """
    from models import RecruiterProfile

    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'recruiter':
        flash("This profile is not a recruiter.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    # Redirect self (logged-in recruiter) to own editable profile
    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('recruiter.profile'))

    # Fetch recruiter profile details
    profile = RecruiterProfile.query.filter_by(user_id=user_id).first()

    # Fetch education entries
    educations = []
    if profile:
        educations = Education.query.filter_by(
            profile_id=profile.id
        ).order_by(Education.created_at.desc()).all()

    # Fetch active job postings (all jobs, template decides expired vs active)
    posted_jobs = Job.query.filter_by(
        company_id=user_id
    ).order_by(Job.id.desc()).all()

    # Check if the current user is following this recruiter
    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first() is not None

    # Follower count
    follower_count = Follow.query.filter_by(followed_id=user_id).count()

    return render_template(
        'recruiter/view_profile.html',
        viewed_user=viewed_user,
        profile=profile,
        educations=educations,
        posted_jobs=posted_jobs,
        is_following=is_following,
        follower_count=follower_count,
        today=date.today()
    )