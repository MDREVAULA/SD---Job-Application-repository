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
#  GET  /settings
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

    # Load blocked users
    from models import UserBlock, User
    blocked_rows  = UserBlock.query.filter_by(blocker_id=current_user.id).all()
    blocked_users = []
    for row in blocked_rows:
        u = User.query.get(row.blocked_id)
        if u:
            pic = None
            if u.profile_picture:
                pic = u.profile_picture if u.profile_picture.startswith('http') \
                      else '/static/uploads/profile_pictures/' + u.profile_picture
            blocked_users.append({
                'id':         u.id,
                'username':   u.username,
                'role':       u.role,
                'pic':        pic,
                'blocked_at': row.created_at.strftime('%b %d, %Y'),
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

    data    = request.get_json(silent=True) or {}
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

        # Auto-accept pending follow requests if profile is now open
        if 'show_profile' in data or 'profile_audience' in data:
            try:
                from models import FollowRequest, Follow, User as UserModel

                new_show = user_settings.show_profile or 'everyone'
                try:
                    new_audience = json.loads(user_settings.profile_audience_json) \
                                   if user_settings.profile_audience_json else []
                except Exception:
                    new_audience = []

                pending = FollowRequest.query.filter_by(
                    receiver_id=current_user.id, status='pending'
                ).all()

                for req in pending:
                    sender = UserModel.query.get(req.sender_id)
                    if not sender:
                        continue
                    auto = False
                    if new_show == 'everyone':
                        auto = True
                    elif new_show == 'specific':
                        if sender.role == 'recruiter' and 'recruiter' in new_audience:
                            auto = True
                        elif sender.role == 'hr' and 'hr' in new_audience:
                            auto = True
                    if auto:
                        req.status = 'accepted'
                        exists = Follow.query.filter_by(
                            follower_id=req.sender_id,
                            followed_id=current_user.id
                        ).first()
                        if not exists:
                            db.session.add(Follow(
                                follower_id=req.sender_id,
                                followed_id=current_user.id
                            ))
            except Exception as e:
                # Never let the follow-request logic crash the whole save
                print(f'[settings] follow-request auto-accept error: {e}')

    # ── Notifications ─────────────────────────────────────────
    elif section == 'notifications':
        user_settings.notif_app_status = bool(data.get('notif_app_status', False))
        user_settings.notif_messages   = bool(data.get('notif_messages',   False))
        user_settings.notif_followers  = bool(data.get('notif_followers',  False))
        user_settings.notif_jobs       = bool(data.get('notif_jobs',       False))

    # ── Security (2FA toggle) ─────────────────────────────────
    elif section == 'security':
        if 'two_factor' in data:
            user_settings.two_factor        = bool(data['two_factor'])
            user_settings.two_factor_code   = None   # clear any leftover PIN
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

        if not current_user.password:
            return jsonify({'success': False, 'message': 'Password change not available for Google accounts.'}), 400
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
        import traceback
        traceback.print_exc()
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
#  POST /settings/delete-account
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    if not _role_allowed():
        return jsonify({'success': False, 'message': 'Access denied.'}), 403

    data           = request.get_json(silent=True) or {}
    password_input = data.get('password', '')

    # Google users have no password — skip check
    if current_user.password:
        if not password_input:
            return jsonify({'success': False, 'message': 'Please enter your password to confirm.'}), 400
        if not check_password_hash(current_user.password, password_input):
            return jsonify({'success': False, 'message': 'Incorrect password.'}), 400

    user_id = current_user.id
    role    = current_user.role

    try:
        from sqlalchemy import text

        uid = user_id

        # ══════════════════════════════════════════════
        # Mirrors admin._delete_user_data() exactly,
        # adapted for ORM + SQLAlchemy text() style.
        # ══════════════════════════════════════════════

        def _run(sql, **kw):
            db.session.execute(text(sql), kw)
            db.session.flush()

        def _delete_user_data(target_uid):
            u = target_uid  # shorthand

            # 1. Break message reply_to_id self-ref FIRST
            _run("""UPDATE message SET reply_to_id = NULL
                    WHERE reply_to_id IN (
                        SELECT id FROM (
                            SELECT id FROM message
                            WHERE sender_id = :u OR receiver_id = :u
                        ) AS _m
                    )""", u=u)

            # 2. Message reactions
            _run("""DELETE FROM message_reaction
                    WHERE user_id = :u
                       OR message_id IN (
                           SELECT id FROM (
                               SELECT id FROM message
                               WHERE sender_id = :u OR receiver_id = :u
                           ) AS _m2
                       )""", u=u)

            # 3. Messages
            _run("DELETE FROM message WHERE sender_id = :u OR receiver_id = :u", u=u)

            # 4. Follows & follow requests
            _run("DELETE FROM follow_request WHERE sender_id = :u OR receiver_id = :u", u=u)
            _run("DELETE FROM follow WHERE follower_id = :u OR followed_id = :u", u=u)

            # 5. User blocks
            _run("DELETE FROM user_block WHERE blocker_id = :u OR blocked_id = :u", u=u)

            # 6. User reports — NULL reviewed_by first to avoid FK error
            _run("UPDATE user_report SET reviewed_by = NULL WHERE reviewed_by = :u", u=u)
            _run("DELETE FROM user_report WHERE reporter_id = :u OR reported_id = :u", u=u)

            # 7. Saved jobs (as applicant)
            _run("DELETE FROM saved_job WHERE applicant_id = :u", u=u)

            # 8. Job team memberships (as HR)
            _run("DELETE FROM job_team_member WHERE hr_id = :u", u=u)

            # 9. HR feedback written by this user
            _run("DELETE FROM hr_feedback WHERE hr_id = :u", u=u)

            # 10. NULL employee.confirmed_by (FK — can't delete yet)
            _run("UPDATE employee SET confirmed_by = NULL WHERE confirmed_by = :u", u=u)

            # 11. NULL resignation_request.reviewed_by
            _run("UPDATE resignation_request SET reviewed_by = NULL WHERE reviewed_by = :u", u=u)

            # 12. Resignation requests where this user IS the applicant
            _run("DELETE FROM resignation_request WHERE applicant_id = :u", u=u)
            # ...and any linked to this user's employee records
            _run("""DELETE FROM resignation_request
                    WHERE employee_id IN (
                        SELECT id FROM employee
                        WHERE user_id = :u
                           OR application_id IN (
                               SELECT id FROM application WHERE applicant_id = :u
                           )
                    )""", u=u)

            # 13. Employee records
            _run("""DELETE FROM employee
                    WHERE user_id = :u
                       OR application_id IN (
                           SELECT id FROM application WHERE applicant_id = :u
                       )""", u=u)

            # 14. Employment onboarding
            _run("""DELETE FROM employment_onboarding
                    WHERE application_id IN (
                        SELECT id FROM application WHERE applicant_id = :u
                    )""", u=u)

            # 15. Employment submissions
            _run("""DELETE FROM employment_submission
                    WHERE application_id IN (
                        SELECT id FROM application WHERE applicant_id = :u
                    )""", u=u)

            # 16. HR feedback ON this user's applications
            _run("""DELETE FROM hr_feedback
                    WHERE application_id IN (
                        SELECT id FROM application WHERE applicant_id = :u
                    )""", u=u)

            # 17. All notifications — both as owner AND as sender_id
            _run("""DELETE FROM applicant_notification
                    WHERE applicant_id = :u
                       OR sender_id    = :u
                       OR application_id IN (
                           SELECT id FROM application WHERE applicant_id = :u
                       )""", u=u)
            _run("""DELETE FROM recruiter_notification
                    WHERE recruiter_id = :u
                       OR sender_id    = :u
                       OR application_id IN (
                           SELECT id FROM application WHERE applicant_id = :u
                       )""", u=u)
            _run("""DELETE FROM hr_notification
                    WHERE hr_id     = :u
                       OR sender_id = :u
                       OR application_id IN (
                           SELECT id FROM application WHERE applicant_id = :u
                       )""", u=u)
            _run("DELETE FROM admin_notifications WHERE user_id = :u", u=u)

            # 18. This user's own applications
            _run("DELETE FROM application WHERE applicant_id = :u", u=u)

            # 19. Applicant profile chain
            _run("""DELETE FROM work_experience_certificate
                    WHERE experience_id IN (
                        SELECT id FROM work_experience
                        WHERE profile_id IN (
                            SELECT id FROM applicant_profile WHERE user_id = :u
                        )
                    )""", u=u)
            _run("""DELETE FROM work_experience
                    WHERE profile_id IN (
                        SELECT id FROM applicant_profile WHERE user_id = :u
                    )""", u=u)
            _run("""DELETE FROM applicant_education
                    WHERE profile_id IN (
                        SELECT id FROM applicant_profile WHERE user_id = :u
                    )""", u=u)
            _run("""DELETE FROM skill
                    WHERE profile_id IN (
                        SELECT id FROM applicant_profile WHERE user_id = :u
                    )""", u=u)
            _run("""DELETE FROM project
                    WHERE profile_id IN (
                        SELECT id FROM applicant_profile WHERE user_id = :u
                    )""", u=u)
            _run("""DELETE FROM certification
                    WHERE profile_id IN (
                        SELECT id FROM applicant_profile WHERE user_id = :u
                    )""", u=u)
            _run("DELETE FROM applicant_profile WHERE user_id = :u", u=u)

            # 20. Recruiter profile chain
            _run("""DELETE FROM recruiter_education
                    WHERE profile_id IN (
                        SELECT id FROM recruiter_profile WHERE user_id = :u
                    )""", u=u)
            _run("DELETE FROM recruiter_profile WHERE user_id = :u", u=u)

            # 21. HR profile chain
            _run("""DELETE FROM hr_education
                    WHERE profile_id IN (
                        SELECT id FROM hr_profile WHERE user_id = :u
                    )""", u=u)
            _run("DELETE FROM hr_profile WHERE user_id = :u", u=u)

            # 22. User settings
            _run("DELETE FROM user_settings WHERE user_id = :u", u=u)

        # ══════════════════════════════════════════════
        # RECRUITER: delete all owned jobs + all HR accs
        # ══════════════════════════════════════════════
        if role == 'recruiter':

            # NULL FK cols that reference this recruiter before job deletes
            _run("UPDATE employee SET confirmed_by = NULL WHERE confirmed_by = :u", u=uid)
            _run("UPDATE resignation_request SET reviewed_by = NULL WHERE reviewed_by = :u", u=uid)

            # Collect HR accounts this recruiter created
            hr_rows = db.session.execute(
                text("SELECT id FROM user WHERE created_by = :u AND role = 'hr'"),
                {'u': uid}
            ).fetchall()
            hr_ids = [row[0] for row in hr_rows]

            # Delete each owned job and all its children
            job_rows = db.session.execute(
                text("SELECT id FROM job WHERE company_id = :u"), {'u': uid}
            ).fetchall()

            for (job_id,) in job_rows:
                # Mirrors admin._delete_job_rows()
                for sql in [
                    "DELETE FROM applicant_notification WHERE job_id = :jid OR application_id IN (SELECT id FROM application WHERE job_id = :jid)",
                    "DELETE FROM recruiter_notification WHERE job_id = :jid OR application_id IN (SELECT id FROM application WHERE job_id = :jid)",
                    "DELETE FROM hr_notification       WHERE job_id = :jid OR application_id IN (SELECT id FROM application WHERE job_id = :jid)",
                    """DELETE FROM resignation_request
                       WHERE job_id = :jid
                          OR employee_id IN (
                              SELECT id FROM employee
                              WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)
                          )""",
                    """DELETE FROM employee
                       WHERE job_id = :jid
                          OR application_id IN (SELECT id FROM application WHERE job_id = :jid)""",
                    "DELETE FROM employment_onboarding  WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)",
                    """DELETE FROM employment_submission
                       WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)
                          OR requirement_id IN (SELECT id FROM employment_requirement WHERE job_id = :jid)""",
                    "DELETE FROM hr_feedback            WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)",
                    "DELETE FROM employment_requirement WHERE job_id = :jid",
                    "DELETE FROM saved_job              WHERE job_id = :jid",
                    "DELETE FROM job_team_member        WHERE job_id = :jid",
                    "DELETE FROM application            WHERE job_id = :jid",
                    "DELETE FROM job_image              WHERE job_id = :jid",
                ]:
                    db.session.execute(text(sql), {'jid': job_id})
                    db.session.flush()

                db.session.execute(text("DELETE FROM job WHERE id = :jid"), {'jid': job_id})
                db.session.flush()

            # Delete all owned HR accounts (and their data)
            for hr_uid in hr_ids:
                _delete_user_data(hr_uid)
                _run("UPDATE user SET created_by = NULL WHERE created_by = :u", u=hr_uid)
                _run("UPDATE user SET deleted_by = NULL WHERE deleted_by = :u", u=hr_uid)
                _run("DELETE FROM user WHERE id = :u", u=hr_uid)

            # Delete recruiter's own notifications (owned + as sender)
            _run("DELETE FROM recruiter_notification WHERE recruiter_id = :u OR sender_id = :u", u=uid)

        # ══════════════════════════════════════════════
        # Delete the main user's own data
        # ══════════════════════════════════════════════
        _delete_user_data(uid)

        # NULL self-referential user FKs before deleting the row
        _run("UPDATE user SET created_by = NULL WHERE created_by = :u", u=uid)
        _run("UPDATE user SET deleted_by = NULL WHERE deleted_by = :u", u=uid)

        # Log out and delete the user row
        from flask_login import logout_user
        logout_user()

        _run("DELETE FROM user WHERE id = :u", u=uid)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Could not delete account: {str(e)}'}), 500

# ─────────────────────────────────────────────────────────────
#  POST /settings/logout-all
# ─────────────────────────────────────────────────────────────
@settings_bp.route('/logout-all', methods=['POST'])
@login_required
def logout_all_devices():
    return jsonify({'success': True})