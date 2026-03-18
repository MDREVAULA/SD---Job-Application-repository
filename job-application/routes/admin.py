from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, login_user
from models import db, User, ApplicantProfile
from routes.auth import send_verification_email

admin_bp = Blueprint('admin', __name__, url_prefix="/admin")


# ==============================
# Secret Admin Login
# ==============================
@admin_bp.route('/login/<token>', endpoint='admin_login')
def admin_login(token):

    # Check token matches
    if token != current_app.config.get("ADMIN_TOKEN"):
        flash("Invalid or expired admin link.", "danger")
        return redirect(url_for('auth.login'))

    # Find admin user
    admin = User.query.filter_by(role="admin").first()

    if not admin:
        flash("Admin account not found.", "danger")
        return redirect(url_for('auth.login'))

    login_user(admin)
    flash("Logged in as admin.", "success")
    return redirect(url_for('admin.dashboard'))


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