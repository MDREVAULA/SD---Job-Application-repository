from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user, login_user
from werkzeug.security import check_password_hash
from models import AdminNotification, db, User, ApplicantProfile
from flask import jsonify
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix="/admin")


# ==============================
# Secret Admin Login Page
# ==============================
@admin_bp.route('/login/<token>', methods=['GET', 'POST'], endpoint='admin_login')
def admin_login(token):

    # Validate the token first
    if token != current_app.config.get("ADMIN_TOKEN"):
        flash("Invalid or expired admin link.", "danger")
        return redirect(url_for('auth.login'))

    # On POST — verify credentials
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        admin = User.query.filter_by(email=email, role="admin").first()

        if not admin or not check_password_hash(admin.password, password):
            flash("Invalid admin credentials.", "danger")
            return render_template("admin/login.html", token=token)

        login_user(admin)
        flash("Logged in as admin.", "success")
        return redirect(url_for('admin.dashboard'))

    # On GET — show the admin login form
    return render_template("admin/login.html", token=token)


# ==============================
# Admin Dashboard
# ==============================
@admin_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    pending_recruiters = User.query.filter_by(
        role='recruiter',
        verification_status="Pending"
    ).all()

    pending_applicants = User.query.filter_by(
        role='applicant',
        verification_status="Pending"
    ).all()

    return render_template(
        'admin/dashboard.html',
        pending_recruiters=pending_recruiters,
        pending_applicants=pending_applicants
    )


# ==============================
# Scammer Recruiters Page
# ==============================
@admin_bp.route('/scammers')
@login_required
def scammers():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    rejected_recruiters = User.query.filter_by(
        role="recruiter",
        verification_status="Rejected"
    ).all()

    return render_template(
        "admin/rejected_recruiters.html",
        recruiters=rejected_recruiters
    )


# ==============================
# Recruiter Review Page
# ==============================
@admin_bp.route('/review/<int:user_id>')
@login_required
def review_recruiter(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    recruiter = db.session.get(User, user_id)

    if not recruiter or recruiter.role != 'recruiter':
        flash("Recruiter not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    profile = recruiter.recruiter_profile

    return render_template(
        'admin/review_recruiter.html',
        recruiter=recruiter,
        profile=profile
    )


# ==============================
# Applicant Review Page
# ==============================
@admin_bp.route('/review-applicant/<int:user_id>')
@login_required
def review_applicant(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    applicant = db.session.get(User, user_id)

    if not applicant or applicant.role != 'applicant':
        flash("Applicant not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    profile = ApplicantProfile.query.filter_by(
        user_id=user_id
    ).first()

    return render_template(
        'admin/review_applicant.html',
        applicant=applicant,
        profile=profile
    )


# ==============================
# Verify User
# ==============================
@admin_bp.route('/verify/<int:user_id>', methods=['POST'])
@login_required
def verify(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    if user.role not in ['recruiter', 'applicant']:
        flash("Invalid user role for verification!", "danger")
        return redirect(url_for('admin.dashboard'))

    user.verification_status = "Approved"
    user.verification_remarks = None
    user.is_verified = True
    db.session.commit()

    user.verification_status = "Approved"
    user.verification_remarks = None
    user.is_verified = True
    db.session.commit()

   
    push_admin_notif(
        'account_approved',
        f'{user.role.capitalize()} account <strong>{user.username}</strong> was approved',
        user_id=user.id
    )

    send_verification_email(user)

    flash(f"{user.username} has been verified successfully!", "success")
    return redirect(url_for('admin.dashboard'))


# ==============================
# Reject User
# ==============================
@admin_bp.route('/reject/<int:user_id>', methods=['POST'])
@login_required
def reject(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    remarks = request.form.get("remarks")

    if not remarks:
        remarks = "Account rejected due to suspicious or invalid information."

    user.verification_status = "Rejected"
    user.verification_remarks = remarks
    user.is_verified = False
    db.session.commit()

    user.verification_status = "Rejected"
    user.verification_remarks = remarks
    user.is_verified = False
    db.session.commit()

    from routes.auth import send_verification_email
    push_admin_notif(
        'account_rejected',
        f'{user.role.capitalize()} account <strong>{user.username}</strong> was rejected',
        user_id=user.id
    )

    flash(f"{user.username} has been rejected.", "warning")
    return redirect(url_for('admin.dashboard'))


# ==============================
# Rejected Applicants Page
# ==============================
@admin_bp.route('/rejected-applicants')
@login_required
def rejected_applicants():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    rejected_applicants = User.query.filter_by(
        role="applicant",
        verification_status="Rejected"
    ).all()

    return render_template(
        "admin/rejected_applicants.html",
        applicants=rejected_applicants
    )


# ==============================
# Restore Rejected Recruiter
# ==============================
@admin_bp.route('/restore/<int:user_id>', methods=['POST'])
@login_required
def restore(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user or user.role != "recruiter":
        flash("Recruiter not found!", "danger")
        return redirect(url_for('admin.scammers'))

    user.verification_status = "Pending"
    user.verification_remarks = None
    user.is_verified = False
    db.session.commit()

    flash(f"{user.username} has been restored to pending verification.", "success")
    return redirect(url_for('admin.scammers'))


# ==============================
# Restore Rejected Applicant
# ==============================
@admin_bp.route('/restore-applicant/<int:user_id>', methods=['POST'])
@login_required
def restore_applicant(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user or user.role != "applicant":
        flash("Applicant not found!", "danger")
        return redirect(url_for('admin.rejected_applicants'))

    user.verification_status = "Pending"
    user.verification_remarks = None
    user.is_verified = False
    db.session.commit()

    flash(f"{user.username} has been restored to pending verification.", "success")
    return redirect(url_for('admin.rejected_applicants'))


# ── Helper: create an admin notification (call this from other routes) ──
def push_admin_notif(notif_type, message, user_id=None):
    """
    notif_type options:
      'new_message'      – new chat message sent on the platform
      'account_request'  – new user registration awaiting approval
      'account_approved' – admin approved a user
      'account_rejected' – admin rejected a user
    """
    notif = AdminNotification(type=notif_type, message=message, user_id=user_id)
    db.session.add(notif)
    db.session.commit()


# ── API: Get all admin notifications ──
@admin_bp.route('/notifications')
@login_required
def admin_notifications():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    notifs = AdminNotification.query.order_by(
        AdminNotification.created_at.desc()
    ).limit(60).all()
    unread = AdminNotification.query.filter_by(is_read=False).count()
    return jsonify({
        'notifications': [n.to_dict() for n in notifs],
        'unread_count':  unread,
    })


# ── API: Mark all as read ──
@admin_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def admin_notifications_mark_read():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    AdminNotification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


# ── API: Clear all ──
@admin_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def admin_notifications_clear():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    AdminNotification.query.delete()
    db.session.commit()
    return jsonify({'ok': True})


# ── Page: Notification History ──
@admin_bp.route('/notification-history')
@login_required
def admin_notification_history():
    if current_user.role != 'admin':
        return redirect(url_for('admin.dashboard'))
    notifs = AdminNotification.query.order_by(
        AdminNotification.created_at.desc()
    ).all()
    return render_template('admin/notification_history.html', notifications=notifs)