from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, make_response
from flask_login import login_required, current_user, login_user
from werkzeug.security import check_password_hash
from models import AdminNotification, db, User, ApplicantProfile
from routes.auth import send_verification_email
from flask import jsonify
from datetime import datetime, timedelta
from models import AdminNotification, db, User, ApplicantProfile, get_ph_time

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
            ban_until = get_ph_time() + timedelta(days=int(duration))
        except ValueError:
            ban_until = None

    user.is_banned  = True
    user.ban_reason = reason
    user.banned_at  = get_ph_time()
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
# Helper: delete job image files from disk
# ==============================
def _delete_job_image_files(job, app_root):
    import os

    def _del(subfolder, filename):
        if not filename or filename.startswith('http'):
            return
        path = os.path.join(app_root, 'static', 'uploads', subfolder, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f'[DELETE FILE] {path}: {e}')

    for img in job.images:
        _del('job_posters', img.image_path)
    _del('job_covers', job.cover_photo)

    # Employment submission files for this job's requirements
    from sqlalchemy import text
    sub_rows = db.session.execute(text("""
        SELECT es.file_path FROM employment_submission es
        JOIN employment_requirement er ON er.id = es.requirement_id
        WHERE er.job_id = :jid
    """), {"jid": job.id}).fetchall()
    for row in sub_rows:
        _del('employment_submissions', row[0])

    # Resignation letter files for this job
    resign_rows = db.session.execute(text("""
        SELECT letter_file FROM resignation_request
        WHERE applicant_id = :uid
        OR employee_id IN (SELECT id FROM employee WHERE user_id = :uid)
    """), {"uid": target_uid}).fetchall()
    for row in resign_rows:
        _del('resignation_letters', row[0])


# ==============================
# Helper: delete all child DB rows for a job_id
#
# FK dependency order (leaves deleted first):
#   resignation_request.employee_id  → employee.id
#   employee.application_id          → application.id
#   employment_onboarding.application_id → application.id
#   employment_submission.application_id → application.id
#   employment_submission.requirement_id → employment_requirement.id
#   hr_feedback.application_id       → application.id
#   *_notification.application_id / job_id
#   employment_requirement.job_id    → job.id
#   saved_job.job_id                 → job.id
#   job_team_member.job_id           → job.id
#   application.job_id               → job.id
#   job_image.job_id                 → job.id
#
# Does NOT delete the job row itself — caller handles that.
# ==============================
def _delete_job_rows(job_id):
    from sqlalchemy import text

    steps = [
        # 1. All notifications that reference this job's applications or job_id directly
        """DELETE FROM applicant_notification
           WHERE job_id = :jid
              OR application_id IN (SELECT id FROM application WHERE job_id = :jid)""",
        """DELETE FROM recruiter_notification
           WHERE job_id = :jid
              OR application_id IN (SELECT id FROM application WHERE job_id = :jid)""",
        """DELETE FROM hr_notification
           WHERE job_id = :jid
              OR application_id IN (SELECT id FROM application WHERE job_id = :jid)""",

        # 2. Resignation requests (FK → employee.id) — must precede employee delete
        """DELETE FROM resignation_request
           WHERE job_id = :jid
              OR employee_id IN (
                  SELECT id FROM employee
                  WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)
              )""",

        # 3. Employee rows (FK → application.id and job.id)
        """DELETE FROM employee
           WHERE job_id = :jid
              OR application_id IN (SELECT id FROM application WHERE job_id = :jid)""",

        # 4. Employment onboarding (FK → application.id)
        """DELETE FROM employment_onboarding
           WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)""",

        # 5. Employment submissions — covers both application_id and requirement_id FKs
        """DELETE FROM employment_submission
           WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)
              OR requirement_id IN (
                  SELECT id FROM employment_requirement WHERE job_id = :jid
              )""",

        # 6. HR feedback (FK → application.id)
        """DELETE FROM hr_feedback
           WHERE application_id IN (SELECT id FROM application WHERE job_id = :jid)""",

        # 7. Employment requirements (FK → job.id)
        "DELETE FROM employment_requirement WHERE job_id = :jid",

        # 8. Saved jobs (FK → job.id)
        "DELETE FROM saved_job WHERE job_id = :jid",

        # 9. Job team members (FK → job.id)
        "DELETE FROM job_team_member WHERE job_id = :jid",

        # 10. Applications (FK → job.id)
        "DELETE FROM application WHERE job_id = :jid",

        # 11. Job images (FK → job.id) — disk files deleted before calling this
        "DELETE FROM job_image WHERE job_id = :jid",
    ]

    for sql in steps:
        db.session.execute(text(sql), {"jid": job_id})
        db.session.flush()


# ==============================
# DELETE Banned User permanently
#
# Complete FK map — every table that references user.id:
#   applicant_profile, recruiter_profile, hr_profile
#   job (company_id)
#   application (applicant_id)
#   employee (user_id, confirmed_by)
#   resignation_request (applicant_id, reviewed_by, job_id)
#   follow / follow_request
#   message (sender_id, receiver_id, reply_to_id self-ref)
#   message_reaction (user_id, message_id → message)
#   saved_job (applicant_id)
#   job_team_member (hr_id)
#   hr_feedback (hr_id, application_id)
#   user_block / user_report (reporter, reported, reviewed_by)
#   *_notification (owner_id, sender_id, application_id, job_id)
#   admin_notifications (user_id)
#   user_settings (user_id)
#   user (created_by, deleted_by — self-ref)
#
# Strategy:
#   Recruiter → delete all jobs first → delete HR accounts → delete recruiter data
#   HR / Applicant → delete own data only
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

    try:
        from sqlalchemy import text
        import os

        uid = user_id

        # ══════════════════════════════════════════════════════════════════
        # Helper: safely delete a file from disk given a relative path
        # and a subfolder under static/uploads/
        # ══════════════════════════════════════════════════════════════════
        def _delete_upload(subfolder, filename):
            if not filename:
                return
            if filename.startswith('http'):
                return
            path = os.path.join(current_app.root_path, 'static', 'uploads', subfolder, filename)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f'[DELETE FILE] Failed to remove {path}: {e}')

        # ══════════════════════════════════════════════════════════════════
        # Helper: delete all disk files belonging to a user_id
        # Covers: profile_picture, resume, portfolio, company assets,
        #         work experience certificates, evidence files from reports
        # ══════════════════════════════════════════════════════════════════
        def _delete_user_files(target_uid):

            # ── Profile picture ────────────────────────────────────────────
            u = db.session.get(User, target_uid)
            if u:
                _delete_upload('profile_pictures', u.profile_picture)

            # ── Applicant profile files ────────────────────────────────────
            row = db.session.execute(
                text("SELECT resume_file, portfolio_file FROM applicant_profile WHERE user_id = :uid"),
                {"uid": target_uid}
            ).fetchone()
            if row:
                _delete_upload('resumes',    row[0])
                _delete_upload('portfolios', row[1])

            # ── Work experience certificates ───────────────────────────────
            cert_rows = db.session.execute(text("""
                SELECT wec.file_path
                FROM work_experience_certificate wec
                JOIN work_experience we ON we.id = wec.experience_id
                JOIN applicant_profile ap ON ap.id = we.profile_id
                WHERE ap.user_id = :uid
            """), {"uid": target_uid}).fetchall()
            for cert in cert_rows:
                _delete_upload('work_certificates', cert[0])

            # ── Recruiter profile files ────────────────────────────────────
            rec_row = db.session.execute(
                text("SELECT company_logo, company_proof, portfolio_file FROM recruiter_profile WHERE user_id = :uid"),
                {"uid": target_uid}
            ).fetchone()
            if rec_row:
                _delete_upload('company_logos',  rec_row[0])
                _delete_upload('company_proofs', rec_row[1])
                _delete_upload('portfolios',     rec_row[2])

            # ── HR profile files ───────────────────────────────────────────
            hr_row = db.session.execute(
                text("SELECT portfolio_file FROM hr_profile WHERE user_id = :uid"),
                {"uid": target_uid}
            ).fetchone()
            if hr_row:
                _delete_upload('portfolios', hr_row[0])

            # ── User report evidence files ─────────────────────────────────
            # evidence_files is stored as a JSON/comma-separated list of filenames
            report_rows = db.session.execute(
                text("SELECT evidence_files FROM user_report WHERE reporter_id = :uid OR reported_id = :uid"),
                {"uid": target_uid}
            ).fetchall()
            for r in report_rows:
                if r[0]:
                    import json
                    try:
                        files = json.loads(r[0])
                        if isinstance(files, list):
                            for f in files:
                                _delete_upload('report_evidence', f)
                        else:
                            _delete_upload('report_evidence', r[0])
                    except (json.JSONDecodeError, TypeError):
                        # fallback: treat as single filename
                        _delete_upload('report_evidence', r[0])

            # Employment submission files (applicant-uploaded onboarding docs)
            sub_rows = db.session.execute(text("""
                SELECT es.file_path
                FROM employment_submission es
                JOIN application a ON a.id = es.application_id
                WHERE a.applicant_id = :uid
            """), {"uid": target_uid}).fetchall()
            for row in sub_rows:
                if row[0]:
                    _delete_upload('employment_submissions', row[0])
            
            # Resignation letter files
            resign_rows = db.session.execute(text("""
                SELECT letter_file FROM resignation_request WHERE applicant_id = :uid
            """), {"uid": target_uid}).fetchall()
            for row in resign_rows:
                if row[0]:
                    _delete_upload('resignation_letters', row[0])

        # ══════════════════════════════════════════════════════════════════
        # Collect HR accounts created by this recruiter before any deletes
        # ══════════════════════════════════════════════════════════════════
        hr_ids = []
        if user.role == 'recruiter':
            hr_rows = db.session.execute(
                text("SELECT id FROM user WHERE created_by = :uid AND role = 'hr'"),
                {"uid": uid}
            ).fetchall()
            hr_ids = [row[0] for row in hr_rows]

        # ══════════════════════════════════════════════════════════════════
        # _delete_user_data(target_uid)
        #
        # Deletes every row referencing target_uid in strict FK order.
        # Does NOT handle job rows owned by this user — those must be
        # deleted via _delete_job_rows() before calling this for a recruiter.
        # ══════════════════════════════════════════════════════════════════
        def _delete_user_data(target_uid):

            # ── 1. Break self-referential message reply chain ──────────────
            db.session.execute(text("""
                UPDATE message SET reply_to_id = NULL
                WHERE reply_to_id IN (
                    SELECT id FROM (
                        SELECT id FROM message
                        WHERE sender_id = :uid OR receiver_id = :uid
                    ) AS _m
                )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 2. Message reactions ───────────────────────────────────────
            db.session.execute(text("""
                DELETE FROM message_reaction
                WHERE user_id = :uid
                   OR message_id IN (
                       SELECT id FROM (
                           SELECT id FROM message
                           WHERE sender_id = :uid OR receiver_id = :uid
                       ) AS _m2
                   )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 3. Messages ────────────────────────────────────────────────
            db.session.execute(text("""
                DELETE FROM message
                WHERE sender_id = :uid OR receiver_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 4. Follows ─────────────────────────────────────────────────
            db.session.execute(text("""
                DELETE FROM follow_request
                WHERE sender_id = :uid OR receiver_id = :uid
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM follow
                WHERE follower_id = :uid OR followed_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 5. User blocks ─────────────────────────────────────────────
            db.session.execute(text("""
                DELETE FROM user_block
                WHERE blocker_id = :uid OR blocked_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 6. User reports ────────────────────────────────────────────
            db.session.execute(text("""
                UPDATE user_report SET reviewed_by = NULL WHERE reviewed_by = :uid
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM user_report
                WHERE reporter_id = :uid OR reported_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 7. Saved jobs (as applicant) ───────────────────────────────
            db.session.execute(text("""
                DELETE FROM saved_job WHERE applicant_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 8. Job team memberships (as HR) ───────────────────────────
            db.session.execute(text("""
                DELETE FROM job_team_member WHERE hr_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 9. HR feedback written by this user ────────────────────────
            db.session.execute(text("""
                DELETE FROM hr_feedback WHERE hr_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 10. NULL employee.confirmed_by ─────────────────────────────
            db.session.execute(text("""
                UPDATE employee SET confirmed_by = NULL WHERE confirmed_by = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 11. NULL resignation_request.reviewed_by ───────────────────
            db.session.execute(text("""
                UPDATE resignation_request
                SET reviewed_by = NULL WHERE reviewed_by = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 12. Resignation requests where this user IS the applicant ──
            db.session.execute(text("""
                DELETE FROM resignation_request
                WHERE applicant_id = :uid
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM resignation_request
                WHERE employee_id IN (
                    SELECT id FROM employee
                    WHERE user_id = :uid
                       OR application_id IN (
                           SELECT id FROM application WHERE applicant_id = :uid
                       )
                )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 13. Employee records ───────────────────────────────────────
            db.session.execute(text("""
                DELETE FROM employee
                WHERE user_id = :uid
                   OR application_id IN (
                       SELECT id FROM application WHERE applicant_id = :uid
                   )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 14. Employment onboarding ──────────────────────────────────
            db.session.execute(text("""
                DELETE FROM employment_onboarding
                WHERE application_id IN (
                    SELECT id FROM application WHERE applicant_id = :uid
                )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 15. Employment submissions ─────────────────────────────────
            db.session.execute(text("""
                DELETE FROM employment_submission
                WHERE application_id IN (
                    SELECT id FROM application WHERE applicant_id = :uid
                )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 16. HR feedback on this user's applications ────────────────
            db.session.execute(text("""
                DELETE FROM hr_feedback
                WHERE application_id IN (
                    SELECT id FROM application WHERE applicant_id = :uid
                )
            """), {"uid": target_uid})
            db.session.flush()

            # ── 17. All notifications referencing this user ────────────────
            db.session.execute(text("""
                DELETE FROM applicant_notification
                WHERE applicant_id = :uid
                   OR sender_id    = :uid
                   OR application_id IN (
                       SELECT id FROM application WHERE applicant_id = :uid
                   )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM recruiter_notification
                WHERE recruiter_id = :uid
                   OR sender_id    = :uid
                   OR application_id IN (
                       SELECT id FROM application WHERE applicant_id = :uid
                   )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM hr_notification
                WHERE hr_id     = :uid
                   OR sender_id = :uid
                   OR application_id IN (
                       SELECT id FROM application WHERE applicant_id = :uid
                   )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM admin_notifications WHERE user_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 18. This user's own applications ──────────────────────────
            db.session.execute(text("""
                DELETE FROM application WHERE applicant_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 19. Applicant profile sub-rows ────────────────────────────
            db.session.execute(text("""
                DELETE FROM work_experience_certificate
                WHERE experience_id IN (
                    SELECT id FROM work_experience
                    WHERE profile_id IN (
                        SELECT id FROM applicant_profile WHERE user_id = :uid
                    )
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM work_experience
                WHERE profile_id IN (
                    SELECT id FROM applicant_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM applicant_education
                WHERE profile_id IN (
                    SELECT id FROM applicant_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM skill
                WHERE profile_id IN (
                    SELECT id FROM applicant_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM project
                WHERE profile_id IN (
                    SELECT id FROM applicant_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM certification
                WHERE profile_id IN (
                    SELECT id FROM applicant_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM applicant_profile WHERE user_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 20. Recruiter profile sub-rows ────────────────────────────
            db.session.execute(text("""
                DELETE FROM recruiter_education
                WHERE profile_id IN (
                    SELECT id FROM recruiter_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM recruiter_profile WHERE user_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 21. HR profile sub-rows ───────────────────────────────────
            db.session.execute(text("""
                DELETE FROM hr_education
                WHERE profile_id IN (
                    SELECT id FROM hr_profile WHERE user_id = :uid
                )
            """), {"uid": target_uid})
            db.session.execute(text("""
                DELETE FROM hr_profile WHERE user_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

            # ── 22. User settings ─────────────────────────────────────────
            db.session.execute(text("""
                DELETE FROM user_settings WHERE user_id = :uid
            """), {"uid": target_uid})
            db.session.flush()

        # ══════════════════════════════════════════════════════════════════
        # STEP 1 — Recruiter: NULL FK columns, delete jobs + their files
        # ══════════════════════════════════════════════════════════════════
        if user.role == 'recruiter':
            from models import Job as JobModel

            db.session.execute(text("""
                UPDATE employee SET confirmed_by = NULL WHERE confirmed_by = :uid
            """), {"uid": uid})
            db.session.execute(text("""
                UPDATE resignation_request
                SET reviewed_by = NULL WHERE reviewed_by = :uid
            """), {"uid": uid})
            db.session.flush()

            recruiter_jobs = JobModel.query.filter_by(company_id=uid).all()
            for job in recruiter_jobs:
                _delete_job_image_files(job, current_app.root_path)
                _delete_job_rows(job.id)
                db.session.execute(
                    text("DELETE FROM job WHERE id = :jid"), {"jid": job.id}
                )
                db.session.flush()

            db.session.execute(text("""
                DELETE FROM recruiter_notification
                WHERE recruiter_id = :uid OR sender_id = :uid
            """), {"uid": uid})
            db.session.flush()

        # ══════════════════════════════════════════════════════════════════
        # STEP 2 — Delete each HR account created by this recruiter
        # ══════════════════════════════════════════════════════════════════
        for hr_uid in hr_ids:
            _delete_user_files(hr_uid)
            _delete_user_data(hr_uid)
            db.session.execute(text(
                "UPDATE user SET created_by = NULL WHERE created_by = :uid"
            ), {"uid": hr_uid})
            db.session.execute(text(
                "UPDATE user SET deleted_by = NULL WHERE deleted_by = :uid"
            ), {"uid": hr_uid})
            db.session.flush()
            db.session.execute(text(
                "DELETE FROM user WHERE id = :uid"
            ), {"uid": hr_uid})
            db.session.flush()

        # ══════════════════════════════════════════════════════════════════
        # STEP 3 — Delete all disk files for the main user
        # Must happen BEFORE _delete_user_data wipes the profile rows
        # that contain the file path columns we need to read
        # ══════════════════════════════════════════════════════════════════
        _delete_user_files(uid)

        # ══════════════════════════════════════════════════════════════════
        # STEP 4 — Delete the main user's own DB data
        # ══════════════════════════════════════════════════════════════════
        _delete_user_data(uid)

        # ══════════════════════════════════════════════════════════════════
        # STEP 5 — NULL self-referential FKs on remaining user rows
        # ══════════════════════════════════════════════════════════════════
        db.session.execute(text(
            "UPDATE user SET created_by = NULL WHERE created_by = :uid"
        ), {"uid": uid})
        db.session.execute(text(
            "UPDATE user SET deleted_by = NULL WHERE deleted_by = :uid"
        ), {"uid": uid})
        db.session.flush()

        # ══════════════════════════════════════════════════════════════════
        # STEP 6 — Delete the user row itself
        # ══════════════════════════════════════════════════════════════════
        db.session.execute(text("DELETE FROM user WHERE id = :uid"), {"uid": uid})
        db.session.commit()

        push_admin_notif('user_deleted', 'User account permanently deleted by admin.')

        flash("User and all associated data have been permanently deleted.", "warning")
        return redirect(url_for('admin.all_users'))

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        flash(f"Deletion failed: {str(e)}", "danger")
        return redirect(url_for('admin.all_users'))

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
    report.reviewed_at = get_ph_time()
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
            ban_until = get_ph_time() + timedelta(days=days)
        except ValueError:
            ban_until = None

    user.is_banned  = True
    user.ban_reason = reason
    user.banned_at  = get_ph_time()
    user.ban_until  = ban_until

    report.status      = 'reviewed'
    report.admin_notes = admin_notes
    report.reviewed_by = current_user.id
    report.reviewed_at = get_ph_time()

    UserReport.query.filter_by(
        reported_id=user.id,
        status='pending'
    ).filter(UserReport.id != report_id).update({
        'status':      'reviewed',
        'admin_notes': f'Auto-closed: admin took action on report #{report_id}',
        'reviewed_by': current_user.id,
        'reviewed_at': get_ph_time(),
    })

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

    def serialize(n):
        d = n.to_dict()
        if n.user_id:
            u = db.session.get(User, n.user_id)
            d['sender_role'] = u.role if u else None
        else:
            d['sender_role'] = None
        return d

    return jsonify({
        'notifications': [serialize(n) for n in notifs],
        'unread_count':  unread,
    })


# ==============================
# API: Mark notifications as read
# ==============================
@admin_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def admin_notifications_mark_read():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json(silent=True) or {}
    notif_id = data.get('id')
    if notif_id:
        AdminNotification.query.filter_by(id=notif_id).update({'is_read': True})
    else:
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
    AdminNotification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    user_roles = {}
    for n in notifs:
        if n.user_id and n.user_id not in user_roles:
            u = db.session.get(User, n.user_id)
            user_roles[n.user_id] = u.role if u else None
    return render_template('admin/notification_history.html',
                           notifications=notifs,
                           user_roles=user_roles)


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

    from models import (Job, RecruiterNotification, ApplicantNotification,
                        HRNotification, Application, get_ph_time)

    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    data   = request.get_json() or {}
    reason = (data.get('reason') or '').strip() or 'Violated platform guidelines.'
    days   = data.get('days')

    try:
        job.is_taken_down   = True
        job.takedown_reason = reason
        job.taken_down_at   = get_ph_time()
        job.takedown_until  = (
            get_ph_time() + timedelta(days=int(days))
            if days and str(days).isdigit() and int(days) > 0
            else None
        )

        # ── 1. Notify recruiter ──
        db.session.add(RecruiterNotification(
            recruiter_id = job.company_id,
            type         = 'job_takedown',
            message      = (
                f'Your job posting <strong>"{job.title}"</strong> has been taken down by an admin. '
                f'Reason: {reason}. '
                + (f'It will be restored after {days} day(s) if resolved.'
                   if days else 'Contact support to resolve this.')
            ),
            job_id = job.id,
        ))

        # ── 2. Active applicants ──
        try:
            active_apps = Application.query.filter(
                Application.job_id == job_id,
                Application.status.in_(['Pending', 'Interview', 'Waitlisted', 'Under Review',
                                        'pending', 'interview', 'waitlisted', 'under review'])
            ).all()
            for app in active_apps:
                app.status = 'Job Removed'
                db.session.add(ApplicantNotification(
                    applicant_id = app.applicant_id,
                    type         = 'job_update',
                    job_id       = job.id,
                    message      = (
                        f'⚠️ The job <strong>"{job.title}"</strong> you applied to has been '
                        f'removed by an admin for policy violations. '
                        f'Your application is now marked <strong>Job Removed</strong>. '
                        f'We recommend caution if you have been in contact with this employer outside the platform.'
                    ),
                ))

            # ── Employed applicants — special warning ──
            employed_apps = Application.query.filter(
                Application.job_id == job_id,
                Application.status.in_(['employed', 'Employed'])
            ).all()
            for app in employed_apps:
                db.session.add(ApplicantNotification(
                    applicant_id = app.applicant_id,
                    type         = 'job_update',
                    job_id       = job.id,
                    message      = (
                        f'⚠️ The job posting <strong>"{job.title}"</strong> you are currently employed under '
                        f'has been taken down from our platform for policy violations. '
                        f'<strong>Your employment contract is between you and the recruiter directly — '
                        f'please consult with your recruiter regarding your employment status.</strong> '
                        f'We are a job matching platform and taking down a posting does not automatically terminate your employment.'
                    ),
                ))
        except Exception as e:
            print(f'[TAKEDOWN] applicant notify error: {e}')

        # ── 3. Saved jobs ──
        try:
            from models import SavedJob
            saved = SavedJob.query.filter_by(job_id=job_id).all()
            for s in saved:
                db.session.add(ApplicantNotification(
                    applicant_id = s.applicant_id,
                    type         = 'job_update',
                    job_id       = job.id,
                    message      = (
                        f'A job you saved — <strong>"{job.title}"</strong> — '
                        f'has been removed from the platform and is no longer available.'
                    ),
                ))
                db.session.delete(s)
        except Exception as e:
            print(f'[TAKEDOWN] saved job error: {e}')

        # ── 4. HR team members ──
        try:
            from models import JobTeamMember
            hr_members = JobTeamMember.query.filter_by(job_id=job_id).all()
            for member in hr_members:
                db.session.add(HRNotification(
                    hr_id   = member.hr_id,
                    type    = 'job_update',
                    job_id  = job.id,
                    message = (
                        f'⚠️ The job <strong>"{job.title}"</strong> you were assigned to '
                        f'has been taken down by an admin. Reason: {reason}.'
                    ),
                ))
        except Exception as e:
            print(f'[TAKEDOWN] HR notify error: {e}')

        db.session.commit()

        push_admin_notif(
            'job_takedown',
            f'Job <strong>"{job.title}"</strong> taken down by admin.',
            user_id=job.company_id,
        )

        return jsonify({'ok': True, 'message': f'Job "{job.title}" taken down successfully.'})

    except Exception as e:
        db.session.rollback()
        print(f'[TAKEDOWN ERROR] {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==============================
# Job Moderation: Restore
# ==============================
@admin_bp.route('/job/<int:job_id>/restore', methods=['POST'])
@login_required
def restore_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    from models import Job, RecruiterNotification, ApplicantNotification, Application

    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    job.is_taken_down   = False
    job.takedown_reason = None
    job.takedown_until  = None
    job.taken_down_at   = None

    db.session.add(RecruiterNotification(
        recruiter_id = job.company_id,
        type         = 'job_restored',
        message      = f'Your job posting <strong>"{job.title}"</strong> has been restored and is now visible again.',
        job_id       = job.id,
    ))

    removed_apps = Application.query.filter_by(
        job_id=job_id, status='Job Removed'
    ).all()

    for app in removed_apps:
        app.status = 'Pending'
        db.session.add(ApplicantNotification(
            applicant_id = app.applicant_id,
            type         = 'job_update',
            job_id       = job.id,
            message      = (
                f'Good news! The job posting <strong>"{job.title}"</strong> '
                f'has been restored. Your application status has been reset to '
                f'<strong>Pending</strong>.'
            ),
        ))

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
    from sqlalchemy import text
    import os

    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    title      = job.title
    company_id = job.company_id

    try:
        # Delete disk files while ORM object still has .images loaded
        _delete_job_image_files(job, current_app.root_path)

        # Delete all child rows in FK order, then the job row itself
        _delete_job_rows(job_id)
        db.session.execute(text("DELETE FROM job WHERE id = :jid"), {"jid": job_id})

        # Add notification AFTER all job rows are gone, with job_id=None
        # (previously this was added before _delete_job_rows, which caused
        # _delete_job_rows to wipe the notification before commit)
        db.session.add(RecruiterNotification(
            recruiter_id = company_id,
            type         = 'job_deleted',
            job_id       = None,  # job no longer exists, avoid FK reference
            message      = (
                f'Your job posting <strong>"{title}"</strong> has been permanently '
                f'removed by an admin for violating platform guidelines.'
            ),
        ))

        db.session.commit()

        push_admin_notif(
            'job_deleted',
            f'Job <strong>"{title}"</strong> permanently deleted by admin.',
            user_id=company_id,
        )

        return jsonify({'ok': True, 'message': f'Job "{title}" permanently deleted.'})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500