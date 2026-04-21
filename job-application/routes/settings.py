"""
routes/settings.py
Settings routes for Applicant, HR, and Recruiter roles.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, UserSettings
from werkzeug.security import check_password_hash, generate_password_hash
import json

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


# ─────────────────────────────────────────────────────────────
#  Allowed roles helper
# ─────────────────────────────────────────────────────────────
ALLOWED_ROLES = {'applicant', 'hr', 'recruiter'}

def _role_allowed():
    return current_user.is_authenticated and current_user.role in ALLOWED_ROLES


# ─────────────────────────────────────────────────────────────
#  GET  /settings   — render the settings page
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/', methods=['GET'])
@login_required
def settings_page():
    if not _role_allowed():
        flash('Access denied.', 'error')
        return redirect(url_for('auth.login'))

    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()

    # Parse profile_audience JSON → Python list
    if user_settings.profile_audience_json:
        try:
            user_settings.profile_audience = json.loads(user_settings.profile_audience_json)
        except Exception:
            user_settings.profile_audience = []
    else:
        user_settings.profile_audience = []

    # Load blocked users for the Blocked tab
    from models import UserBlock, User
    blocked_rows = UserBlock.query.filter_by(blocker_id=current_user.id).all()
    blocked_users = []
    for row in blocked_rows:
        u = User.query.get(row.blocked_id)
        if u:
            pic = None
            if u.profile_picture:
                pic = u.profile_picture if u.profile_picture.startswith('http') \
                      else '/static/uploads/profile_pictures/' + u.profile_picture
            blocked_users.append({
                'id':          u.id,
                'username':    u.username,
                'role':        u.role,
                'pic':         pic,
                'blocked_at':  row.created_at.strftime('%b %d, %Y'),
            })

    return render_template('settings.html', settings=user_settings, blocked_users=blocked_users)


# ─────────────────────────────────────────────────────────────
#  POST /settings/save
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/save', methods=['POST'])
@login_required
def save_settings():
    if not _role_allowed():
        return jsonify({'success': False, 'message': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    section = data.get('section', '')

    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)

    # ── Privacy ──────────────────────────────────────────────
    if section == 'privacy':
        if 'show_name' in data:
            user_settings.show_name = data['show_name']
        if 'show_profile' in data:
            user_settings.show_profile = data['show_profile']
        if 'profile_audience' in data:
            user_settings.profile_audience_json = json.dumps(data['profile_audience'])
        if 'show_follow_list' in data:
            user_settings.show_follow_list = data['show_follow_list']
        if 'show_follow_count' in data:
            user_settings.show_follow_count = data['show_follow_count']
        if 'who_can_message' in data:
            user_settings.who_can_message = data['who_can_message']

    # ── Notifications ─────────────────────────────────────────
    elif section == 'notifications':
        user_settings.notif_app_status = bool(data.get('notif_app_status', False))
        user_settings.notif_messages   = bool(data.get('notif_messages',   False))
        user_settings.notif_followers  = bool(data.get('notif_followers',  False))
        user_settings.notif_jobs       = bool(data.get('notif_jobs',       False))

    # ── Security (2FA toggle) ─────────────────────────────────
    elif section == 'security':
        if 'two_factor' in data:
            user_settings.two_factor = bool(data['two_factor'])
            # Clear any leftover code when toggling
            user_settings.two_factor_code   = None
            user_settings.two_factor_expiry = None

    # ── Email ─────────────────────────────────────────────────
    elif section == 'email':
        new_email = data.get('new_email', '').strip()
        if not new_email:
            return jsonify({'success': False, 'message': 'Email cannot be empty.'}), 400
        from models import User
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != current_user.id:
            return jsonify({'success': False, 'message': 'That email is already in use.'}), 409
        current_user.email = new_email
        db.session.add(current_user)

    # ── Password ─────────────────────────────────────────────
    elif section == 'password':
        current_pass = data.get('current_password', '')
        new_pass     = data.get('new_password', '')
        confirm_pass = data.get('confirm_password', '')

        if not check_password_hash(current_user.password, current_pass):
            return jsonify({'success': False, 'message': 'Current password is incorrect.'}), 400
        if new_pass != confirm_pass:
            return jsonify({'success': False, 'message': 'New passwords do not match.'}), 400
        if len(new_pass) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters.'}), 400

        current_user.password = generate_password_hash(new_pass)
        db.session.add(current_user)

    # ── Appearance ────────────────────────────────────────────
    elif section == 'appearance':
        if 'theme' in data:
            user_settings.theme = data['theme']
        if 'density' in data:
            user_settings.density = data['density']

    # ── Language ─────────────────────────────────────────────
    elif section == 'language':
        if 'language' in data:
            user_settings.language = data['language']
        if 'timezone' in data:
            user_settings.timezone = data['timezone']

    else:
        return jsonify({'success': False, 'message': f'Unknown section: {section}'}), 400

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error. Please try again.'}), 500


# ─────────────────────────────────────────────────────────────
#  POST /settings/unblock/<id>
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/unblock/<int:target_id>', methods=['POST'])
@login_required
def unblock_user(target_id):
    from models import UserBlock
    block = UserBlock.query.filter_by(
        blocker_id=current_user.id, blocked_id=target_id
    ).first()
    if block:
        db.session.delete(block)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Block not found.'}), 404


# ─────────────────────────────────────────────────────────────
#  POST /settings/deactivate
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/deactivate', methods=['POST'])
@login_required
def deactivate_account():
    if not _role_allowed():
        return jsonify({'success': False}), 403

    current_user.is_active = False
    db.session.commit()

    from flask_login import logout_user
    logout_user()
    return jsonify({'success': True})


# ─────────────────────────────────────────────────────────────
#  POST /settings/logout-all
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/logout-all', methods=['POST'])
@login_required
def logout_all_devices():
    return jsonify({'success': True})