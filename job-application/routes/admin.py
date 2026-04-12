from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user, login_user
from werkzeug.security import check_password_hash
from models import db, User, ApplicantProfile
from routes.auth import send_verification_email
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix="/admin")


# ==============================
# Secret Admin Login Page
# ==============================
@admin_bp.route('/login/<token>', methods=['GET', 'POST'], endpoint='admin_login')
def admin_login(token):

    if token != current_app.config.get("ADMIN_TOKEN"):
        flash("Invalid or expired admin link.", "danger")
        return redirect(url_for('auth.login'))

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

    return render_template("admin/login.html", token=token)


# ==============================
# Admin Dashboard
# FIX 1: Show recruiters who submitted for review OR completed profile
# FIX 4: Pass total_recruiters instead of pending count for stat card
# ==============================
@admin_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile

    # FIX 1: Show all pending recruiters who have submitted for review
    # (submitted_for_review=True ensures only those who explicitly submitted appear)
    pending_recruiter_ids = db.session.query(RecruiterProfile.user_id).filter_by(
        submitted_for_review=True
    ).subquery()

    pending_recruiters = User.query.filter(
        User.role == 'recruiter',
        User.verification_status == 'Pending',
        User.id.in_(pending_recruiter_ids)
    ).all()

    # Banned users (all roles)
    banned_users = User.query.filter_by(is_banned=True).all()

    # Count all applicants for info panel
    total_applicants = User.query.filter_by(role='applicant').count()

    # FIX 4: Count all recruiters instead of just pending
    total_recruiters = User.query.filter_by(role='recruiter').count()

    return render_template(
        'admin/dashboard.html',
        pending_recruiters=pending_recruiters,
        banned_users=banned_users,
        total_applicants=total_applicants,
        total_recruiters=total_recruiters,
    )


# ==============================
# All Users Page
# FIX 3: Exclude banned users from this view
# ==============================
@admin_bp.route('/users')
@login_required
def all_users():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    role_filter = request.args.get('role', 'all')

    # FIX 3: Exclude banned users — they belong in the banned_users tab only
    query = User.query.filter(
        User.role != 'admin',
        User.is_banned == False
    )
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)

    users = query.order_by(User.id.desc()).all()

    return render_template(
        'admin/all_users.html',
        users=users,
        role_filter=role_filter,
    )


# ==============================
# Banned Users Page
# ==============================
@admin_bp.route('/banned')
@login_required
def banned_users():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    banned = User.query.filter_by(is_banned=True).all()

    return render_template(
        'admin/banned_users.html',
        banned_users=banned,
    )


# ==============================
# Rejected Recruiters Page
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
# Verify Recruiter
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

    if user.role != 'recruiter':
        flash("Only recruiter accounts require verification!", "danger")
        return redirect(url_for('admin.dashboard'))

    user.verification_status = "Approved"
    user.verification_remarks = None
    user.is_verified = True
    db.session.commit()

    send_verification_email(user)

    flash(f"{user.username} has been verified successfully!", "success")
    return redirect(url_for('admin.dashboard'))


# ==============================
# Reject Recruiter
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

    if user.role != 'recruiter':
        flash("Only recruiter accounts can be rejected!", "danger")
        return redirect(url_for('admin.dashboard'))

    remarks = request.form.get("remarks") or "Account rejected due to suspicious or invalid information."

    user.verification_status = "Rejected"
    user.verification_remarks = remarks
    user.is_verified = False
    db.session.commit()

    flash(f"{user.username} has been rejected.", "warning")
    return redirect(url_for('admin.dashboard'))


# ==============================
# BAN User (any role)
# ==============================
@admin_bp.route('/ban/<int:user_id>', methods=['POST'])
@login_required
def ban_user(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user or user.role == 'admin':
        flash("User not found or cannot ban admin!", "danger")
        return redirect(url_for('admin.dashboard'))

    reason = request.form.get("ban_reason") or "Banned due to suspicious activity."

    user.is_banned = True
    user.ban_reason = reason
    user.banned_at = datetime.utcnow()
    db.session.commit()

    flash(f"{user.username} has been banned.", "warning")

    next_url = request.form.get("next") or url_for('admin.dashboard')
    return redirect(next_url)


# ==============================
# UNBAN User
# ==============================
@admin_bp.route('/unban/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('admin.banned_users'))

    user.is_banned = False
    user.ban_reason = None
    user.banned_at = None
    db.session.commit()

    flash(f"{user.username} has been unbanned.", "success")
    return redirect(url_for('admin.banned_users'))


# ==============================
# FIX 5: DELETE Banned User permanently
# ==============================
@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    user = db.session.get(User, user_id)

    if not user or user.role == 'admin':
        flash("User not found or cannot delete admin!", "danger")
        return redirect(url_for('admin.banned_users'))

    db.session.delete(user)
    db.session.commit()

    flash(f"User has been permanently deleted.", "warning")
    return redirect(url_for('admin.banned_users'))


# ==============================
# Restore Rejected Recruiter → back to Pending
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