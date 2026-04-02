# ================================================================
# PUBLIC PROFILE ROUTES
# File: routes/profile_view.py
#
# Add this new Blueprint to your app.py:
#   from routes.profile_view import profile_view_bp
#   app.register_blueprint(profile_view_bp)
#
# URLs produced:
#   /profile/applicant/<int:user_id>   → view_applicant_profile
#   /profile/hr/<int:user_id>          → view_hr_profile
#   /profile/recruiter/<int:user_id>   → view_recruiter_profile
#   /profile/<int:user_id>             → smart redirect based on role
# ================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import (
    db, User, ApplicantProfile, WorkExperience,
    Education, Skill, Project, Certification, Job
)

profile_view_bp = Blueprint('profile_view', __name__, url_prefix='/profile')


# ── SMART REDIRECT — /profile/<user_id> → correct role view ──
@profile_view_bp.route('/<int:user_id>')
@login_required
def view_profile(user_id):
    """
    Smart redirect: detects the user's role and sends the viewer
    to the correct public profile page.
    Also prevents users from viewing their own profile through
    this route (redirects them to their editable profile instead).
    """
    user = User.query.get_or_404(user_id)

    # Redirect self to their own editable profile
    if current_user.id == user_id:
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
@profile_view_bp.route('/hr/<int:user_id>')
@login_required
def view_hr_profile(user_id):
    """
    Public read-only view of an HR member's profile.
    """
    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'hr':
        flash("This profile is not an HR member.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    # Redirect self to own editable profile
    if current_user.id == user_id:
        return redirect(url_for('hr.profile'))

    return render_template(
        'hr/view_profile.html',
        viewed_user=viewed_user
    )


# ── RECRUITER PUBLIC PROFILE ──
@profile_view_bp.route('/recruiter/<int:user_id>')
@login_required
def view_recruiter_profile(user_id):
    """
    Public read-only view of a recruiter's profile.
    Also shows their active job postings.
    """
    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'recruiter':
        flash("This profile is not a recruiter.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    # Redirect self to own editable profile
    if current_user.id == user_id:
        return redirect(url_for('recruiter.profile'))

    # Fetch their active job postings
    posted_jobs = Job.query.filter_by(company_id=user_id).order_by(Job.id.desc()).all()

    return render_template(
        'recruiter/view_profile.html',
        viewed_user=viewed_user,
        posted_jobs=posted_jobs
    )