"""
routes/settings.py
Settings routes for Applicant, HR, and Recruiter roles.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, UserSettings   # see note below about model additions
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

    # Load or create settings row for this user
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()

    # Convert stored JSON list to Python list (docs_audience)
    if user_settings.docs_audience_json:
        try:
            user_settings.docs_audience = json.loads(user_settings.docs_audience_json)
        except Exception:
            user_settings.docs_audience = []
    else:
        user_settings.docs_audience = []

    return render_template('settings.html', settings=user_settings)


# ─────────────────────────────────────────────────────────────
#  POST /settings/save  — save any settings section as JSON
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
        if 'show_docs' in data:
            user_settings.show_docs = data['show_docs']
        if 'docs_audience' in data:
            user_settings.docs_audience_json = json.dumps(data['docs_audience'])
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

    # ── Email ─────────────────────────────────────────────────
    elif section == 'email':
        new_email = data.get('new_email', '').strip()
        if not new_email:
            return jsonify({'success': False, 'message': 'Email cannot be empty.'}), 400
        # Check uniqueness
        from models import User
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != current_user.id:
            return jsonify({'success': False, 'message': 'That email is already in use.'}), 409
        current_user.email = new_email
        db.session.add(current_user)

    # ── Password ─────────────────────────────────────────────
    elif section == 'password':
        current_pass  = data.get('current_password', '')
        new_pass      = data.get('new_password', '')
        confirm_pass  = data.get('confirm_password', '')

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
#  POST /settings/logout-all   (stub — expand with session mgmt)
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/logout-all', methods=['POST'])
@login_required
def logout_all_devices():
    # If you use server-side sessions (e.g. Flask-Session) you can
    # iterate and invalidate them here. For now we return success.
    return jsonify({'success': True})