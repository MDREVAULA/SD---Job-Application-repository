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


def _get_follow_lists(user_id):
    """Return (followers_list, following_list) as User objects for a given user_id."""
    follower_rows  = Follow.query.filter_by(followed_id=user_id).all()
    following_rows = Follow.query.filter_by(follower_id=user_id).all()
    followers  = [User.query.get(r.follower_id)  for r in follower_rows  if User.query.get(r.follower_id)]
    following  = [User.query.get(r.followed_id)  for r in following_rows if User.query.get(r.followed_id)]
    return followers, following


# ── SMART REDIRECT — /profile/<user_id> → correct role view ──
@profile_view_bp.route('/<int:user_id>')
def view_profile(user_id):
    user = User.query.get_or_404(user_id)

    if current_user.is_authenticated and current_user.id == user_id:
        if user.role == 'applicant':
            return redirect(url_for('applicant.profile'))
        elif user.role == 'hr':
            return redirect(url_for('hr.profile'))
        elif user.role == 'recruiter':
            return redirect(url_for('recruiter.profile'))

    if user.role == 'applicant':
        return redirect(url_for('profile_view.view_applicant_profile', user_id=user_id))
    elif user.role == 'hr':
        return redirect(url_for('profile_view.view_hr_profile', user_id=user_id))
    elif user.role == 'recruiter':
        return redirect(url_for('profile_view.view_recruiter_profile', user_id=user_id))
    else:
        abort(404)


# ── APPLICANT PUBLIC PROFILE ──
# No @login_required — accessible to guests
@profile_view_bp.route('/applicant/<int:user_id>')
def view_applicant_profile(user_id):
    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'applicant':
        flash("This profile is not an applicant.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    # Redirect logged-in user viewing their own profile
    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('applicant.profile'))

    prof = ApplicantProfile.query.filter_by(user_id=user_id).first()

    experiences    = WorkExperience.query.filter_by(profile_id=prof.id).order_by(WorkExperience.created_at.desc()).all() if prof else []
    educations     = Education.query.filter_by(profile_id=prof.id).order_by(Education.created_at.desc()).all() if prof else []
    skills         = Skill.query.filter_by(profile_id=prof.id).all() if prof else []
    projects       = Project.query.filter_by(profile_id=prof.id).order_by(Project.created_at.desc()).all() if prof else []
    certifications = Certification.query.filter_by(profile_id=prof.id).order_by(Certification.created_at.desc()).all() if prof else []
    followers, following = _get_follow_lists(user_id)

    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first() is not None

    return render_template(
        'applicant/view_profile.html',
        viewed_user=viewed_user,
        profile=prof,
        experiences=experiences,
        educations=educations,
        skills=skills,
        projects=projects,
        certifications=certifications,
        is_following=is_following,
        followers=followers,
        following=following,
        follower_count=len(followers),
        following_count=len(following),
    )

# ── RECRUITER PUBLIC PROFILE ──
@profile_view_bp.route('/recruiter/<int:user_id>')
def view_recruiter_profile(user_id):
    from models import RecruiterProfile

    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'recruiter':
        flash("This profile is not a recruiter.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('recruiter.profile'))

    profile = RecruiterProfile.query.filter_by(user_id=user_id).first()

    educations = []
    if profile:
        educations = Education.query.filter_by(
            profile_id=profile.id
        ).order_by(Education.created_at.desc()).all()

    posted_jobs = Job.query.filter_by(
        company_id=user_id
    ).order_by(Job.id.desc()).all()

    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first() is not None

    followers, following = _get_follow_lists(user_id)

    return render_template(
        'recruiter/view_profile.html',
        viewed_user=viewed_user,
        profile=profile,
        educations=educations,
        posted_jobs=posted_jobs,
        is_following=is_following,
        followers=followers,
        following=following,
        follower_count=len(followers),
        following_count=len(following),
        today=date.today()
    )

# ── HR PUBLIC PROFILE ──
@profile_view_bp.route('/hr/<int:user_id>')
def view_hr_profile(user_id):
    from models import RecruiterProfile, HRProfile

    viewed_user = User.query.get_or_404(user_id)

    if viewed_user.role != 'hr':
        flash("This profile is not an HR member.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))

    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('hr.profile'))

    profile = HRProfile.query.filter_by(user_id=user_id).first()

    recruiter_profile = None
    if viewed_user.created_by:
        recruiter_profile = RecruiterProfile.query.filter_by(
            user_id=viewed_user.created_by
        ).first()

    followers, following = _get_follow_lists(user_id)

    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first() is not None

    return render_template(
        'hr/view_profile.html',
        viewed_user=viewed_user,
        profile=profile,
        recruiter_profile=recruiter_profile,
        is_following=is_following,
        followers=followers,
        following=following,
        follower_count=len(followers),
        following_count=len(following),
    )

# ── FOLLOW LIST API — returns followers/following as JSON ──
@profile_view_bp.route('/follow-list/<int:user_id>')
def follow_list(user_id):
    """
    Returns followers and following for a user as JSON.
    Used by the real-time modal update after follow/unfollow.
    """
    from flask import jsonify

    follower_rows  = Follow.query.filter_by(followed_id=user_id).all()
    following_rows = Follow.query.filter_by(follower_id=user_id).all()

    def serialize(u):
        if not u:
            return None
        pic = None
        if u.profile_picture:
            if u.profile_picture.startswith('http'):
                pic = u.profile_picture
            else:
                pic = '/static/uploads/profile_pictures/' + u.profile_picture
        return {
            'id':       u.id,
            'username': u.username,
            'role':     u.role,
            'pic':      pic,
            'profile_url': '/profile/' + str(u.id),
        }

    followers  = [serialize(User.query.get(r.follower_id))  for r in follower_rows]
    following  = [serialize(User.query.get(r.followed_id))  for r in following_rows]
    followers  = [u for u in followers  if u]
    following  = [u for u in following  if u]

    return jsonify({
        'followers':       followers,
        'following':       following,
        'follower_count':  len(followers),
        'following_count': len(following),
    })