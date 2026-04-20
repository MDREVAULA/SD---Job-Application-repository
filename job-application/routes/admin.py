from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, make_response
from flask_login import login_required, current_user, login_user
from werkzeug.security import check_password_hash
from models import AdminNotification, db, User, ApplicantProfile
from routes.auth import send_verification_email
from flask import jsonify
from datetime import datetime, timedelta

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
        email    = request.form.get("email")
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
# ==============================
@admin_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import RecruiterProfile, Application, Job
    from collections import defaultdict

    pending_recruiter_ids = db.session.query(RecruiterProfile.user_id).filter_by(
        submitted_for_review=True
    ).subquery()

    pending_recruiters = User.query.filter(
        User.role == 'recruiter',
        User.verification_status == 'Pending',
        User.id.in_(pending_recruiter_ids)
    ).all()

    banned_users     = User.query.filter_by(is_banned=True).all()
    total_applicants = User.query.filter_by(role='applicant').count()
    total_recruiters = User.query.filter_by(role='recruiter').count()

    # ==============================
    # Chart Data: Last 7 Days
    # ==============================
    today = datetime.now().date()
    days_data = {}

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_key = day.strftime('%b %d')
        days_data[day_key] = {
            'applications': 0,
            'signups': 0,
            'jobs': 0
        }

    applications = Application.query.filter(
        Application.created_at >= datetime.combine(today - timedelta(days=7), datetime.min.time())
    ).all()

    for app in applications:
        day_key = app.created_at.strftime('%b %d')
        if day_key in days_data:
            days_data[day_key]['applications'] += 1

    users = User.query.filter(
        User.role.in_(['applicant', 'recruiter', 'hr']),
        User.created_at >= datetime.combine(today - timedelta(days=7), datetime.min.time())
    ).all()

    for user in users:
        if user.created_at:
            day_key = user.created_at.strftime('%b %d')
            if day_key in days_data:
                days_data[day_key]['signups'] += 1

    jobs = Job.query.filter(
        Job.created_at >= datetime.combine(today - timedelta(days=7), datetime.min.time())
    ).all()

    for job in jobs:
        day_key = job.created_at.strftime('%b %d')
        if day_key in days_data:
            days_data[day_key]['jobs'] += 1

    chart_labels       = list(days_data.keys())
    chart_applications = [days_data[label]['applications'] for label in chart_labels]
    chart_signups      = [days_data[label]['signups'] for label in chart_labels]
    chart_jobs         = [days_data[label]['jobs'] for label in chart_labels]

    response = make_response(render_template(
        'admin/dashboard.html',
        pending_recruiters=pending_recruiters,
        banned_users=banned_users,
        total_applicants=total_applicants,
        total_recruiters=total_recruiters,
        chart_labels=chart_labels,
        chart_applications=chart_applications,
        chart_signups=chart_signups,
        chart_jobs=chart_jobs,
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response


# ==============================
# All Users Page
# ==============================
@admin_bp.route('/users')
@login_required
def all_users():

    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    role_filter = request.args.get('role', 'all')

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
        return redirect(url_for('admin.dashboard'))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    if user.role != 'recruiter':
        flash("Only recruiter accounts require verification!", "danger")
        return redirect(url_for('admin.dashboard'))

    user.verification_status  = "Approved"
    user.verification_remarks = None
    user.is_verified          = True

    from models import RecruiterNotification
    notif = RecruiterNotification(
        recruiter_id=user.id,
        type='account_verified',
        message='🎉 Your recruiter account has been <strong>verified and approved</strong> by the admin. You can now post jobs and manage HR accounts.',
    )
    db.session.add(notif)
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

    user.verification_status  = "Rejected"
    user.verification_remarks = remarks
    user.is_verified          = False
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

    reason   = request.form.get("ban_reason") or "Banned due to suspicious activity."
    duration = request.form.get("ban_duration", "permanent")

    if duration == 'permanent':
        ban_until = None
    else:
        try:
            ban_until = datetime.utcnow() + timedelta(days=int(duration))
        except ValueError:
            ban_until = None

    user.is_banned  = True
    user.ban_reason = reason
    user.banned_at  = datetime.utcnow()
    user.ban_until  = ban_until
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

    user.is_banned  = False
    user.ban_reason = None
    user.banned_at  = None
    user.ban_until  = None
    db.session.commit()

    flash(f"{user.username} has been unbanned.", "success")
    return redirect(url_for('admin.banned_users'))


# ==============================
# DELETE Banned User permanently
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

    flash("User has been permanently deleted.", "warning")
    return redirect(url_for('admin.banned_users'))


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

    user.verification_status  = "Pending"
    user.verification_remarks = None
    user.is_verified          = False
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

    user.verification_status  = "Pending"
    user.verification_remarks = None
    user.is_verified          = False
    db.session.commit()

    flash(f"{user.username} has been restored to pending verification.", "success")
    return redirect(url_for('admin.rejected_applicants'))


# ==============================
# Reports Tab
# ==============================
@admin_bp.route('/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import UserReport
    status_filter = request.args.get('status', 'pending')

    query = UserReport.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    all_reports     = query.order_by(UserReport.created_at.desc()).all()
    pending_count   = UserReport.query.filter_by(status='pending').count()
    reviewed_count  = UserReport.query.filter_by(status='reviewed').count()
    dismissed_count = UserReport.query.filter_by(status='dismissed').count()

    return render_template(
        'admin/reports.html',
        reports=all_reports,
        status_filter=status_filter,
        pending_count=pending_count,
        reviewed_count=reviewed_count,
        dismissed_count=dismissed_count,
    )


# ==============================
# Dismiss a Report
# ==============================
@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@login_required
def dismiss_report(report_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    from models import UserReport
    report = db.session.get(UserReport, report_id)
    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for('admin.reports'))

    admin_notes        = request.form.get('admin_notes', '')
    report.status      = 'dismissed'
    report.admin_notes = admin_notes
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.utcnow()
    db.session.commit()

    flash("Report dismissed.", "success")
    return redirect(url_for('admin.reports'))


# ==============================
# Ban User FROM a Report (with duration)
# ==============================
@admin_bp.route('/reports/<int:report_id>/ban', methods=['POST'])
@login_required
def ban_from_report(report_id):
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import UserReport

    report = db.session.get(UserReport, report_id)
    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for('admin.reports'))

    user = db.session.get(User, report.reported_id)
    if not user or user.role == 'admin':
        flash("Cannot ban this user.", "danger")
        return redirect(url_for('admin.reports'))

    reason      = request.form.get('ban_reason') or f'Banned following a report: {report.reason}'
    admin_notes = request.form.get('admin_notes', '')
    duration    = request.form.get('ban_duration', 'permanent')

    if duration == 'permanent':
        ban_until = None
    else:
        try:
            days      = int(duration)
            ban_until = datetime.utcnow() + timedelta(days=days)
        except ValueError:
            ban_until = None

    user.is_banned  = True
    user.ban_reason = reason
    user.banned_at  = datetime.utcnow()
    user.ban_until  = ban_until

    report.status      = 'reviewed'
    report.admin_notes = admin_notes
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.utcnow()

    db.session.commit()

    push_admin_notif(
        'account_banned',
        f'User <strong>{user.username}</strong> was banned'
        + (f' for {duration} days' if duration != 'permanent' else ' permanently')
        + f' following report #{report_id}',
        user_id=user.id
    )

    duration_str = 'permanently' if duration == 'permanent' else f'for {duration} days'
    flash(f"{user.username} has been banned {duration_str}.", "warning")
    return redirect(url_for('admin.reports'))


# ==============================
# Helper: push admin notification
# ==============================
def push_admin_notif(notif_type, message, user_id=None):
    notif = AdminNotification(type=notif_type, message=message, user_id=user_id)
    db.session.add(notif)
    db.session.commit()


# ==============================
# API: Get all admin notifications
# ==============================
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


# ==============================
# API: Mark all notifications as read
# ==============================
@admin_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def admin_notifications_mark_read():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    AdminNotification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


# ==============================
# API: Clear all notifications
# ==============================
@admin_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def admin_notifications_clear():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    AdminNotification.query.delete()
    db.session.commit()
    return jsonify({'ok': True})


# ==============================
# Page: Notification History
# ==============================
@admin_bp.route('/notification-history')
@login_required
def admin_notification_history():
    if current_user.role != 'admin':
        return redirect(url_for('admin.dashboard'))
    notifs = AdminNotification.query.order_by(
        AdminNotification.created_at.desc()
    ).all()
    return render_template('admin/notification_history.html', notifications=notifs)


# ==============================
# API: Pending reports count
# ==============================
@admin_bp.route('/reports/pending-count')
@login_required
def reports_pending_count():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    from models import UserReport
    count = UserReport.query.filter_by(status='pending').count()
    return jsonify({'count': count})


# ==============================
# All Jobs Page
# ==============================
@admin_bp.route('/jobs')
@login_required
def all_jobs():
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    from models import Job
    status_filter = request.args.get('status', 'all')

    query = Job.query
    if status_filter == 'active':
        query = query.filter_by(is_taken_down=False)
    elif status_filter == 'takendown':
        query = query.filter_by(is_taken_down=True)

    jobs            = query.order_by(Job.created_at.desc()).all()
    total_jobs      = Job.query.count()
    active_count    = Job.query.filter_by(is_taken_down=False).count()
    takendown_count = Job.query.filter_by(is_taken_down=True).count()

    return render_template(
        'admin/all_jobs.html',
        jobs=jobs,
        status_filter=status_filter,
        total_jobs=total_jobs,
        active_count=active_count,
        takendown_count=takendown_count,
    )


# ==============================
# API: Taken-down jobs count (for dashboard badge)
# ==============================
@admin_bp.route('/jobs/takendown-count')
@login_required
def jobs_takendown_count():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    from models import Job
    count = Job.query.filter_by(is_taken_down=True).count()
    return jsonify({'count': count})


# ==============================
# Job Moderation: Takedown
# ==============================
@admin_bp.route('/job/<int:job_id>/takedown', methods=['POST'])
@login_required
def takedown_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    from models import Job, RecruiterNotification
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    data   = request.get_json() or {}
    reason = (data.get('reason') or '').strip() or 'Violated platform guidelines.'
    days   = data.get('days')

    # ── Fixed column names ──
    job.is_taken_down   = True
    job.takedown_reason = reason
    job.taken_down_at   = datetime.utcnow()

    if days and str(days).isdigit() and int(days) > 0:
        job.takedown_until = datetime.utcnow() + timedelta(days=int(days))
    else:
        job.takedown_until = None

    notif = RecruiterNotification(
        recruiter_id = job.company_id,
        type         = 'job_takedown',
        message      = (
            f'Your job posting <strong>"{job.title}"</strong> has been temporarily taken down by an admin. '
            f'Reason: {reason}. '
            + (f'It will be restored after {days} day(s) if resolved.'
               if days else 'Please contact support to resolve this.')
        ),
        job_id = job.id,
    )
    db.session.add(notif)
    db.session.commit()

    push_admin_notif(
        'job_takedown',
        f'Job <strong>"{job.title}"</strong> taken down by admin.',
        user_id=job.company_id,
    )

    return jsonify({'ok': True, 'message': f'Job "{job.title}" has been taken down.'})


# ==============================
# Job Moderation: Restore
# ==============================
@admin_bp.route('/job/<int:job_id>/restore', methods=['POST'])
@login_required
def restore_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    from models import Job, RecruiterNotification
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # ── Fixed column names ──
    job.is_taken_down   = False
    job.takedown_reason = None
    job.takedown_until  = None
    job.taken_down_at   = None

    notif = RecruiterNotification(
        recruiter_id = job.company_id,
        type         = 'job_restored',
        message      = f'Your job posting <strong>"{job.title}"</strong> has been restored and is now visible again.',
        job_id       = job.id,
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({'ok': True, 'message': f'Job "{job.title}" has been restored.'})


# ==============================
# Job Moderation: Permanent Delete
# ==============================
@admin_bp.route('/job/<int:job_id>/admin-delete', methods=['POST'])
@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    from models import Job, RecruiterNotification
    import os
    from sqlalchemy import text

    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    title      = job.title
    company_id = job.company_id

    try:
        notif = RecruiterNotification(
            recruiter_id = company_id,
            type         = 'job_deleted',
            message      = f'Your job posting <strong>"{title}"</strong> has been permanently removed by an admin for violating platform guidelines.',
        )
        db.session.add(notif)
        db.session.flush()

        db.session.execute(text("""
            DELETE FROM applicant_notification
            WHERE application_id IN (SELECT id FROM application WHERE job_id = :job_id)
        """), {"job_id": job_id})

        db.session.execute(text("""
            DELETE FROM recruiter_notification
            WHERE job_id = :job_id
            OR application_id IN (SELECT id FROM application WHERE job_id = :job_id)
        """), {"job_id": job_id})

        db.session.execute(text("""
            DELETE FROM hr_notification
            WHERE job_id = :job_id
            OR application_id IN (SELECT id FROM application WHERE job_id = :job_id)
        """), {"job_id": job_id})

        db.session.flush()

        for image in job.images:
            path = os.path.join(
                'static', 'uploads', 'job_posters', image.image_path
            )
            if os.path.exists(path):
                os.remove(path)
            db.session.delete(image)

        if job.cover_photo:
            cover_path = os.path.join('static', 'uploads', 'job_covers', job.cover_photo)
            if os.path.exists(cover_path):
                os.remove(cover_path)

        db.session.delete(job)
        db.session.commit()

        push_admin_notif(
            'job_deleted',
            f'Job <strong>"{title}"</strong> permanently deleted by admin.',
            user_id=company_id,
        )

        return jsonify({'ok': True, 'message': f'Job "{title}" permanently deleted.'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500