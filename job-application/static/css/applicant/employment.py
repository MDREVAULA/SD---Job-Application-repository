# ================================================================
# routes/employment.py
# Employment flow routes — all three roles
# ================================================================

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, jsonify
)
from flask_login import login_required, current_user
from models import (
    db, Job, Application, User, RecruiterProfile,
    ApplicantNotification, RecruiterNotification, HRNotification
)
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import uuid

# Import new models (add these to models.py first)
from models import (
    EmploymentRequirement,
    EmploymentSubmission,
    EmploymentOnboarding,
    Employee,
)

employment_bp = Blueprint('employment', __name__, url_prefix='/employment')

ALLOWED_DOC_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}


def _allowed_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS


def _upload_folder():
    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'employment_docs')
    os.makedirs(folder, exist_ok=True)
    return folder


# ─────────────────────────────────────────────────────────────────
# APPLICANT — Submit employment requirements
# ─────────────────────────────────────────────────────────────────

@employment_bp.route('/submit/<int:app_id>', methods=['GET', 'POST'])
@login_required
def submit_requirements(app_id):
    """Applicant submits their onboarding documents."""
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.filter_by(
        id=app_id, applicant_id=current_user.id
    ).first_or_404()

    if application.status != 'accepted':
        flash("You can only submit employment requirements for accepted applications.", "warning")
        return redirect(url_for('applicant.status'))

    # Guard: already confirmed as employee
    if application.employee_record:
        flash("Your employment has already been confirmed!", "info")
        return redirect(url_for('employment.applicant_onboarding_status', app_id=app_id))

    job = application.job
    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).order_by(
        EmploymentRequirement.id
    ).all()

    # Get or create onboarding record
    onboarding = application.onboarding
    if not onboarding:
        onboarding = EmploymentOnboarding(application_id=app_id, status='pending_submission')
        db.session.add(onboarding)
        db.session.commit()

    # Build existing submissions map {requirement_id: submission}
    existing = {s.requirement_id: s for s in application.employment_submissions}

    if request.method == 'POST':
        folder = _upload_folder()
        any_change = False

        for req in requirements:
            file = request.files.get(f'req_{req.id}')
            note = request.form.get(f'note_{req.id}', '').strip()

            submission = existing.get(req.id)

            if file and file.filename:
                if not _allowed_doc(file.filename):
                    flash(f"Invalid file type for '{req.title}'. Allowed: PDF, JPG, PNG, DOC, DOCX.", "danger")
                    return redirect(request.url)

                # Save new file
                ext = os.path.splitext(secure_filename(file.filename))[1].lower()
                filename = f"emp_{app_id}_{req.id}_{uuid.uuid4().hex[:8]}{ext}"
                file.save(os.path.join(folder, filename))

                if submission:
                    # Remove old file
                    if submission.file_path:
                        old_path = os.path.join(folder, submission.file_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    submission.file_path = filename
                    submission.notes = note
                    submission.updated_at = datetime.get_ph_time()
                else:
                    submission = EmploymentSubmission(
                        application_id=app_id,
                        requirement_id=req.id,
                        file_path=filename,
                        notes=note,
                    )
                    db.session.add(submission)
                any_change = True
            elif note and submission:
                # Update note only
                submission.notes = note
                submission.updated_at = datetime.get_ph_time()
                any_change = True

        if any_change:
            # Check if all required items have files
            all_required_met = True
            for req in requirements:
                if req.is_required:
                    sub = existing.get(req.id) or EmploymentSubmission.query.filter_by(
                        application_id=app_id, requirement_id=req.id
                    ).first()
                    if not sub or not sub.file_path:
                        all_required_met = False
                        break

            if all_required_met:
                onboarding.status = 'submitted'
                onboarding.submitted_at = datetime.get_ph_time()

                # Notify recruiter
                job_owner = User.query.get(job.company_id)
                rec_notif = RecruiterNotification(
                    recruiter_id=job.company_id,
                    type='employment_submission',
                    message=(
                        f"<strong>{current_user.username}</strong> has submitted their employment "
                        f"requirements for <strong>{job.title}</strong>. Please review."
                    ),
                    application_id=app_id,
                    job_id=job.id,
                )
                db.session.add(rec_notif)

                # Notify assigned HR
                from models import JobTeamMember
                for tm in JobTeamMember.query.filter_by(job_id=job.id).all():
                    hr_notif = HRNotification(
                        hr_id=tm.hr_id,
                        type='employment_submission',
                        message=(
                            f"<strong>{current_user.username}</strong> submitted employment docs "
                            f"for <strong>{job.title}</strong>."
                        ),
                        application_id=app_id,
                        job_id=job.id,
                    )
                    db.session.add(hr_notif)

                flash("All required documents submitted! Waiting for review.", "success")
            else:
                flash("Progress saved. Please upload all required documents before submission.", "info")

            db.session.commit()
            return redirect(request.url)

    # Re-fetch existing after potential changes
    existing = {s.requirement_id: s for s in application.employment_submissions}

    recruiter_profile = RecruiterProfile.query.filter_by(user_id=job.company_id).first()

    return render_template(
        'employment/submit_requirements.html',
        application=application,
        job=job,
        requirements=requirements,
        existing=existing,
        onboarding=onboarding,
        recruiter_profile=recruiter_profile,
    )


@employment_bp.route('/applicant/status/<int:app_id>')
@login_required
def applicant_onboarding_status(app_id):
    """Applicant views onboarding status."""
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.filter_by(
        id=app_id, applicant_id=current_user.id
    ).first_or_404()

    job = application.job
    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    existing = {s.requirement_id: s for s in application.employment_submissions}
    onboarding = application.onboarding
    employee_record = application.employee_record
    recruiter_profile = RecruiterProfile.query.filter_by(user_id=job.company_id).first()

    return render_template(
        'employment/applicant_status.html',
        application=application,
        job=job,
        requirements=requirements,
        existing=existing,
        onboarding=onboarding,
        employee_record=employee_record,
        recruiter_profile=recruiter_profile,
    )


@employment_bp.route('/applicant/resign/<int:employee_id>', methods=['POST'])
@login_required
def resign(employee_id):
    """Applicant/employee resigns from their job."""
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    emp = Employee.query.filter_by(id=employee_id, user_id=current_user.id).first_or_404()

    if emp.employment_status != 'active':
        flash("This employment record is no longer active.", "warning")
        return redirect(url_for('applicant.profile'))

    note = request.form.get('resignation_note', '').strip()
    emp.employment_status = 'resigned'
    emp.ended_at = datetime.get_ph_time()
    emp.end_reason = note or 'Resigned'

    # Notify recruiter
    app_rec = emp.application
    rec_notif = RecruiterNotification(
        recruiter_id=emp.job.company_id,
        type='employee_resigned',
        message=(
            f"<strong>{current_user.username}</strong> has resigned from "
            f"<strong>{emp.job_title}</strong>."
        ),
        application_id=app_rec.id,
        job_id=emp.job_id,
    )
    db.session.add(rec_notif)
    db.session.commit()

    flash("Your resignation has been submitted.", "success")
    return redirect(url_for('applicant.profile'))


# ─────────────────────────────────────────────────────────────────
# RECRUITER — Manage employment requirements + review submissions
# ─────────────────────────────────────────────────────────────────

@employment_bp.route('/recruiter/requirements/<int:job_id>', methods=['GET', 'POST'])
@login_required
def manage_requirements(job_id):
    """Recruiter sets the employment requirements for a job."""
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            is_required = request.form.get('is_required') == '1'
            if title:
                req = EmploymentRequirement(
                    job_id=job_id,
                    title=title,
                    description=description or None,
                    is_required=is_required,
                )
                db.session.add(req)
                db.session.commit()
                flash("Requirement added.", "success")
            else:
                flash("Title is required.", "danger")

        elif action == 'delete':
            req_id = request.form.get('req_id')
            req = EmploymentRequirement.query.filter_by(id=req_id, job_id=job_id).first()
            if req:
                db.session.delete(req)
                db.session.commit()
                flash("Requirement removed.", "success")

        return redirect(request.url)

    requirements = EmploymentRequirement.query.filter_by(job_id=job_id).order_by(
        EmploymentRequirement.id
    ).all()

    return render_template(
        'employment/manage_requirements.html',
        job=job,
        requirements=requirements,
    )


@employment_bp.route('/recruiter/review/<int:app_id>', methods=['GET', 'POST'])
@login_required
def review_submission(app_id):
    """Recruiter reviews submitted employment documents."""
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job = application.job

    # Access check
    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if current_user.role == 'hr':
        from models import JobTeamMember
        assigned = JobTeamMember.query.filter_by(
            job_id=job.id, hr_id=current_user.id
        ).first()
        if not assigned:
            flash("You are not assigned to this job.", "warning")
            return redirect(url_for('hr.job_list'))

    # Guard: already employee — no editing
    if application.employee_record:
        flash("Employment already confirmed for this applicant.", "info")
        return redirect(url_for('employment.employee_list', job_id=job.id))

    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    existing = {s.requirement_id: s for s in application.employment_submissions}
    onboarding = application.onboarding
    applicant = User.query.get(application.applicant_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if not onboarding:
            flash("No submission found.", "warning")
            return redirect(request.url)

        if action == 'confirm':
            # Create Employee record
            rec_profile = RecruiterProfile.query.filter_by(user_id=job.company_id).first()
            employee = Employee(
                application_id=app_id,
                job_id=job.id,
                user_id=application.applicant_id,
                confirmed_by=current_user.id,
                start_date=date.today(),
                job_title=job.title,
                company_name=rec_profile.company_name if rec_profile else '',
                employment_status='active',
            )
            db.session.add(employee)

            onboarding.status = 'confirmed'
            onboarding.reviewed_at = datetime.get_ph_time()

            # Notify applicant
            app_notif = ApplicantNotification(
                applicant_id=application.applicant_id,
                type='employment_confirmed',
                message=(
                    f"🎉 Congratulations! Your employment at <strong>{employee.company_name}</strong> "
                    f"as <strong>{employee.job_title}</strong> has been confirmed!"
                ),
                application_id=app_id,
                job_id=job.id,
            )
            db.session.add(app_notif)
            db.session.commit()

            flash(f"{applicant.username} is now confirmed as an employee!", "success")
            return redirect(url_for('employment.employee_list', job_id=job.id))

        elif action == 'request_revision':
            note = request.form.get('reviewer_note', '').strip()
            onboarding.status = 'needs_revision'
            onboarding.reviewer_note = note
            onboarding.reviewed_at = datetime.get_ph_time()

            app_notif = ApplicantNotification(
                applicant_id=application.applicant_id,
                type='employment_revision',
                message=(
                    f"Your employment documents for <strong>{job.title}</strong> need revision. "
                    f"{('Reason: ' + note) if note else ''}"
                ),
                application_id=app_id,
                job_id=job.id,
            )
            db.session.add(app_notif)
            db.session.commit()

            flash("Revision requested. Applicant has been notified.", "info")
            return redirect(request.url)

    return render_template(
        'employment/review_submission.html',
        application=application,
        job=job,
        applicant=applicant,
        requirements=requirements,
        existing=existing,
        onboarding=onboarding,
    )


@employment_bp.route('/recruiter/employees/<int:job_id>')
@login_required
def employee_list(job_id):
    """Recruiter views all employees for a job."""
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if current_user.role == 'hr':
        from models import JobTeamMember
        assigned = JobTeamMember.query.filter_by(
            job_id=job.id, hr_id=current_user.id
        ).first()
        if not assigned:
            flash("You are not assigned to this job.", "warning")
            return redirect(url_for('hr.job_list'))

    employees = Employee.query.filter_by(job_id=job_id).order_by(
        Employee.confirmed_at.desc()
    ).all()

    # Pending submissions (accepted but not yet confirmed employees)
    pending_onboardings = (
        db.session.query(EmploymentOnboarding, Application)
        .join(Application, EmploymentOnboarding.application_id == Application.id)
        .filter(
            Application.job_id == job_id,
            Application.status == 'accepted',
            EmploymentOnboarding.status.in_(['submitted', 'needs_revision', 'pending_submission']),
        )
        .all()
    )

    # Also accepted applications with no onboarding record yet
    accepted_apps = Application.query.filter_by(job_id=job_id, status='accepted').all()
    no_onboarding_apps = [
        a for a in accepted_apps
        if not a.onboarding and not a.employee_record
    ]

    return render_template(
        'employment/employee_list.html',
        job=job,
        employees=employees,
        pending_onboardings=pending_onboardings,
        no_onboarding_apps=no_onboarding_apps,
    )


@employment_bp.route('/recruiter/fire/<int:employee_id>', methods=['POST'])
@login_required
def fire_employee(employee_id):
    """Recruiter fires an employee."""
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    emp = Employee.query.get_or_404(employee_id)
    job = Job.query.get(emp.job_id)

    if not job or job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if emp.employment_status != 'active':
        flash("This employment record is no longer active.", "warning")
        return redirect(url_for('employment.employee_list', job_id=emp.job_id))

    reason = request.form.get('fire_reason', '').strip()
    emp.employment_status = 'fired'
    emp.ended_at = datetime.get_ph_time()
    emp.end_reason = reason or 'Terminated by recruiter'

    # Notify applicant
    app_notif = ApplicantNotification(
        applicant_id=emp.user_id,
        type='employment_ended',
        message=(
            f"Your employment at <strong>{emp.company_name}</strong> as "
            f"<strong>{emp.job_title}</strong> has been terminated."
            f"{(' Reason: ' + reason) if reason else ''}"
        ),
        application_id=emp.application_id,
        job_id=emp.job_id,
    )
    db.session.add(app_notif)
    db.session.commit()

    flash(f"{emp.user.username} has been removed from employment.", "success")
    return redirect(url_for('employment.employee_list', job_id=emp.job_id))


# ─────────────────────────────────────────────────────────────────
# HR — Review submissions (same route, different role handling above)
# HR-specific employee list view
# ─────────────────────────────────────────────────────────────────

@employment_bp.route('/hr/employees/<int:job_id>')
@login_required
def hr_employee_list(job_id):
    """HR views employees for assigned job — redirects to shared route."""
    return redirect(url_for('employment.employee_list', job_id=job_id))


# ─────────────────────────────────────────────────────────────────
# AJAX — pending submission count badge
# ─────────────────────────────────────────────────────────────────

@employment_bp.route('/recruiter/pending-count/<int:job_id>')
@login_required
def pending_count(job_id):
    if current_user.role not in ('recruiter', 'hr'):
        return jsonify({'count': 0})
    count = (
        db.session.query(EmploymentOnboarding)
        .join(Application, EmploymentOnboarding.application_id == Application.id)
        .filter(
            Application.job_id == job_id,
            EmploymentOnboarding.status == 'submitted',
        )
        .count()
    )
    return jsonify({'count': count})