from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User

admin_bp = Blueprint('admin', __name__, url_prefix="/admin")


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    # Get all pending recruiters
    pending_recruiters = User.query.filter_by(role='recruiter', is_verified=False).all()
    return render_template('admin_dashboard.html', pending_recruiters=pending_recruiters)


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

    profile = recruiter.recruiter_profile  # Link to RecruiterProfile
    return render_template('admin_review_recruiter.html', recruiter=recruiter, profile=profile)


@admin_bp.route('/verify/<int:user_id>', methods=['POST'])
@login_required
def verify(user_id):
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    recruiter = db.session.get(User, user_id)
    if not recruiter or recruiter.role != 'recruiter':
        flash("Recruiter not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    recruiter.is_verified = True
    db.session.commit()
    flash(f"{recruiter.username} has been verified!", "success")
    return redirect(url_for('admin.dashboard'))
