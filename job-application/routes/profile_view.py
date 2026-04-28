# ================================================================
# PUBLIC PROFILE ROUTES
# File: routes/profile_view.py
# ================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from models import (
    db, User, ApplicantProfile, WorkExperience,
    Education, Skill, Project, Certification, Job, Follow, FollowRequest, UserSettings,
    JobTeamMember
)
from datetime import date
import json

profile_view_bp = Blueprint('profile_view', __name__, url_prefix='/profile')


def _get_follow_lists(user_id):
    follower_rows  = Follow.query.filter_by(followed_id=user_id).all()
    following_rows = Follow.query.filter_by(follower_id=user_id).all()
    followers = [u for u in (User.query.get(r.follower_id) for r in follower_rows) if u and not u.is_banned and not u.is_deleted]
    following = [u for u in (User.query.get(r.followed_id) for r in following_rows) if u and not u.is_banned and not u.is_deleted]
    return followers, following


def _get_settings(user_id):
    """Load UserSettings for the *viewed* user, with safe defaults."""
    s = UserSettings.query.filter_by(user_id=user_id).first()
    if not s:
        class DefaultSettings:
            show_name             = 'everyone'
            show_profile          = 'everyone'
            profile_audience_json = '["recruiter","hr","follower"]'
            profile_audience      = ['recruiter', 'hr', 'follower']
            show_follow_list      = 'yes'
            show_follow_count     = 'yes'
            who_can_message       = 'all'
        return DefaultSettings()

    try:
        s.profile_audience = json.loads(s.profile_audience_json) if s.profile_audience_json else ['recruiter', 'hr', 'follower']
    except Exception:
        s.profile_audience = ['recruiter', 'hr', 'follower']

    return s


def _is_follower(viewer_id, viewed_id):
    """True if viewer is following viewed (one-directional)."""
    if not viewer_id:
        return False
    return bool(Follow.query.filter_by(follower_id=viewer_id, followed_id=viewed_id).first())


def _is_mutual(viewer_id, viewed_id):
    """True if viewer follows viewed AND viewed follows viewer."""
    if not viewer_id:
        return False
    a = Follow.query.filter_by(follower_id=viewer_id, followed_id=viewed_id).first()
    b = Follow.query.filter_by(follower_id=viewed_id, followed_id=viewer_id).first()
    return bool(a and b)


def _can_see_profile(settings, viewer_role, viewer_id, viewed_id):
    """
    Controls visibility of personal info AND documents.
    'everyone'  — all visitors including guests
    'specific'  — only roles/relationships listed in profile_audience
    'none'      — completely private
    """
    if settings.show_profile == 'everyone':
        return True
    if settings.show_profile == 'none':
        return False
    if settings.show_profile == 'specific':
        audience = settings.profile_audience
        if viewer_role and viewer_role in audience:
            return True
        if 'follower' in audience and _is_follower(viewer_id, viewed_id):
            return True
        if 'mutual' in audience and _is_mutual(viewer_id, viewed_id):
            return True
    return False


def _can_see_name(settings, viewer_id, viewed_id):
    if settings.show_name == 'everyone':
        return True
    if settings.show_name == 'mutual':
        return _is_mutual(viewer_id, viewed_id)
    return False


def _can_see_follow_list(settings):
    return settings.show_follow_list == 'yes'


def _can_see_follow_count(settings):
    return settings.show_follow_count == 'yes'


def _can_message(settings, viewer_role, viewer_id, viewed_id):
    if settings.who_can_message == 'all':
        return True
    if settings.who_can_message == 'recruiters' and viewer_role == 'recruiter':
        return True
    if settings.who_can_message == 'mutual' and _is_mutual(viewer_id, viewed_id):
        return True
    return False


# ── SMART REDIRECT ──
@profile_view_bp.route('/<int:user_id>')
def view_profile(user_id):
    from models import UserBlock
    from sqlalchemy import or_, and_

    user = User.query.get_or_404(user_id)
    if user.is_deleted:
        abort(404)

    if user.is_banned:
        flash("This profile is not available.", "warning")
        return redirect(url_for('auth.index'))

    if current_user.is_authenticated and current_user.id == user_id:
        if user.role == 'applicant':
            return redirect(url_for('applicant.profile'))
        elif user.role == 'hr':
            return redirect(url_for('hr.profile'))
        elif user.role == 'recruiter':
            return redirect(url_for('recruiter.profile'))

    # Block check — redirect if either party has blocked the other
    if current_user.is_authenticated:
        _block = UserBlock.query.filter(
            or_(
                and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user.id),
                and_(UserBlock.blocker_id == user.id,         UserBlock.blocked_id == current_user.id),
            )
        ).first()
        if _block:
            flash("This profile is not available.", "warning")
            return redirect(url_for('chat.people'))

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
def view_applicant_profile(user_id):
    viewed_user = User.query.get_or_404(user_id)
    if viewed_user.role != 'applicant':
        flash("This profile is not an applicant.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))
    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('applicant.profile'))

    settings    = _get_settings(user_id)
    viewer_id   = current_user.id   if current_user.is_authenticated else None
    viewer_role = current_user.role if current_user.is_authenticated else None

    show_profile      = _can_see_profile(settings, viewer_role, viewer_id, user_id)
    show_name         = _can_see_name(settings, viewer_id, user_id)
    show_follow_list  = _can_see_follow_list(settings)
    show_follow_count = _can_see_follow_count(settings)
    can_message       = _can_message(settings, viewer_role, viewer_id, user_id)
    who_can_message   = settings.who_can_message

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
            follower_id=current_user.id, followed_id=user_id
        ).first() is not None

    # ── Check for a pending follow request from current viewer ──
    has_pending_request = False
    if current_user.is_authenticated and not is_following:
        settings_obj = _get_settings(user_id)
        audience = settings_obj.profile_audience if hasattr(settings_obj, 'profile_audience') else []
        viewer_role = current_user.role

        # Privileged viewers (recruiter/hr in audience) follow directly — no request shown
        viewer_bypasses = (
            (viewer_role == "recruiter" and "recruiter" in audience) or
            (viewer_role == "hr"        and "hr"        in audience) or
            settings_obj.show_profile == "everyone"
        )

        if not viewer_bypasses:
            has_pending_request = bool(FollowRequest.query.filter_by(
                sender_id=current_user.id,
                receiver_id=user_id,
                status='pending'
            ).first())

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
        has_pending_request=has_pending_request,
        followers=followers  if show_follow_list  else [],
        following=following  if show_follow_list  else [],
        follower_count=len(followers)  if show_follow_count else None,
        following_count=len(following) if show_follow_count else None,
        show_profile=show_profile,
        show_name=show_name,
        show_follow_list=show_follow_list,
        show_follow_count=show_follow_count,
        can_message=can_message,
        who_can_message=who_can_message,
    )


# ── RECRUITER PUBLIC PROFILE ──
@profile_view_bp.route('/recruiter/<int:user_id>')
def view_recruiter_profile(user_id):
    from models import RecruiterProfile, RecruiterEducation

    viewed_user = User.query.get_or_404(user_id)
    if viewed_user.role != 'recruiter':
        flash("This profile is not a recruiter.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))
    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('recruiter.profile'))

    settings    = _get_settings(user_id)
    viewer_id   = current_user.id   if current_user.is_authenticated else None
    viewer_role = current_user.role if current_user.is_authenticated else None

    show_profile      = _can_see_profile(settings, viewer_role, viewer_id, user_id)
    show_name         = _can_see_name(settings, viewer_id, user_id)
    show_follow_list  = _can_see_follow_list(settings)
    show_follow_count = _can_see_follow_count(settings)
    can_message       = _can_message(settings, viewer_role, viewer_id, user_id)
    who_can_message   = settings.who_can_message

    profile    = RecruiterProfile.query.filter_by(user_id=user_id).first()

    # FIX: use RecruiterEducation, not the generic Education model
    educations = RecruiterEducation.query.filter_by(
        profile_id=profile.id
    ).order_by(RecruiterEducation.created_at.desc()).all() if profile else []

    # FIX: removed the wrong filter that was dropping jobs without an expiration date
    posted_jobs = Job.query.filter_by(
        company_id=user_id,
        is_taken_down=False
    ).order_by(Job.id.desc()).all()

    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id, followed_id=user_id
        ).first() is not None

    followers, following = _get_follow_lists(user_id)

    return render_template(
        'recruiter/view_profile.html',
        viewed_user=viewed_user,
        profile=profile,
        educations=educations,
        posted_jobs=posted_jobs,
        is_following=is_following,
        followers=followers  if show_follow_list  else [],
        following=following  if show_follow_list  else [],
        follower_count=len(followers)  if show_follow_count else None,
        following_count=len(following) if show_follow_count else None,
        show_profile=show_profile,
        show_name=show_name,
        show_follow_list=show_follow_list,
        show_follow_count=show_follow_count,
        can_message=can_message,
        who_can_message=who_can_message,
        today=date.today(),
    )


# ── HR PUBLIC PROFILE ──
@profile_view_bp.route('/hr/<int:user_id>')
def view_hr_profile(user_id):
    from models import RecruiterProfile, HRProfile, HREducation

    viewed_user = User.query.get_or_404(user_id)
    if viewed_user.role != 'hr':
        flash("This profile is not an HR member.", "warning")
        return redirect(url_for('profile_view.view_profile', user_id=user_id))
    if current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for('hr.profile'))

    settings    = _get_settings(user_id)
    viewer_id   = current_user.id   if current_user.is_authenticated else None
    viewer_role = current_user.role if current_user.is_authenticated else None

    show_profile      = _can_see_profile(settings, viewer_role, viewer_id, user_id)
    show_name         = _can_see_name(settings, viewer_id, user_id)
    show_follow_list  = _can_see_follow_list(settings)
    show_follow_count = _can_see_follow_count(settings)
    can_message       = _can_message(settings, viewer_role, viewer_id, user_id)
    who_can_message   = settings.who_can_message

    profile           = HRProfile.query.filter_by(user_id=user_id).first()
    recruiter_profile = None
    if viewed_user.created_by:
        recruiter_profile = RecruiterProfile.query.filter_by(user_id=viewed_user.created_by).first()

    educations = []
    if profile:
        educations = HREducation.query.filter_by(
            profile_id=profile.id
        ).order_by(HREducation.created_at.desc()).all()

    # FIX: query assigned jobs and pass today for expiry checks in the template
    assigned_jobs = [
        tm.job for tm in JobTeamMember.query.filter_by(hr_id=user_id).all()
        if tm.job
    ]

    is_following = False
    if current_user.is_authenticated:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id, followed_id=user_id
        ).first() is not None

    followers, following = _get_follow_lists(user_id)

    return render_template(
        'hr/view_profile.html',
        viewed_user=viewed_user,
        profile=profile,
        recruiter_profile=recruiter_profile,
        educations=educations,
        assigned_jobs=assigned_jobs,
        is_following=is_following,
        followers=followers  if show_follow_list  else [],
        following=following  if show_follow_list  else [],
        follower_count=len(followers)  if show_follow_count else None,
        following_count=len(following) if show_follow_count else None,
        show_profile=show_profile,
        show_name=show_name,
        show_follow_list=show_follow_list,
        show_follow_count=show_follow_count,
        can_message=can_message,
        who_can_message=who_can_message,
        today=date.today(),
    )


# ── FOLLOW LIST API ──
@profile_view_bp.route('/follow-list/<int:user_id>')
def follow_list(user_id):
    settings = _get_settings(user_id)

    # ── Owner always sees their own list ──
    is_owner = current_user.is_authenticated and current_user.id == user_id

    list_is_private = not is_owner and not _can_see_follow_list(settings)

    if list_is_private:
        return jsonify({
            'followers': [],
            'following': [],
            'follower_count': None,
            'following_count': None,
            'list_is_private': True,
        })

    follower_rows  = Follow.query.filter_by(followed_id=user_id).all()
    following_rows = Follow.query.filter_by(follower_id=user_id).all()

    def serialize(u):
        if not u: return None
        pic = None
        if u.profile_picture:
            pic = u.profile_picture if u.profile_picture.startswith('http') \
                  else '/static/uploads/profile_pictures/' + u.profile_picture
        return {'id': u.id, 'username': u.username, 'role': u.role,
                'pic': pic, 'profile_url': '/profile/' + str(u.id)}

    followers = [serialize(u) for r in follower_rows
                for u in [User.query.get(r.follower_id)] if u and not u.is_banned and not u.is_deleted]
    following = [serialize(u) for r in following_rows
                for u in [User.query.get(r.followed_id)] if u and not u.is_banned and not u.is_deleted]

    show_count = _can_see_follow_count(settings)
    return jsonify({
        'followers':       followers,
        'following':       following,
        'follower_count':  len(followers) if show_count else None,
        'following_count': len(following) if show_count else None,
        'list_is_private': False,
    })