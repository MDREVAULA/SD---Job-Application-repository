# ================================================================
# EMPLOYMENT ROUTES  —  routes/employment.py
# ================================================================
# Register in app.py:
#   from routes.employment import employment_bp
#   app.register_blueprint(employment_bp)
# ================================================================

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime
import os, uuid, json
from werkzeug.utils import secure_filename

from models import (
    db, Job, Application, User,
    ApplicantNotification, RecruiterNotification, HRNotification,
)

# ── Import the new models (they live in models.py after you paste them) ──
from models import EmploymentRequirement, EmploymentSubmission, Employee

employment_bp = Blueprint('employment', __name__, url_prefix='/employment')

ALLOWED_DOC_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}


def _allowed_doc(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_DOC_EXTENSIONS


# ================================================================
# ── RECRUITER: Manage employment requirements per job ──
# ================================================================

@employment_bp.route('/requirements/<int:job_id>', methods=['GET'])
@login_required
def manage_requirements(job_id):
    """Page where recruiter sets up required documents for a job."""
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    requirements = EmploymentRequirement.query.filter_by(job_id=job_id).all()

    return render_template(
        'employment/manage_requirements.html',
        job=job,
        requirements=requirements,
    )


@employment_bp.route('/requirements/<int:job_id>/add', methods=['POST'])
@login_required
def add_requirement(job_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_required = request.form.get('is_required', '1') == '1'

    if not name:
        flash("Requirement name is required.", "danger")
        return redirect(url_for('employment.manage_requirements', job_id=job_id))

    req = EmploymentRequirement(
        job_id=job_id,
        name=name,
        description=description,
        is_required=is_required,
    )
    db.session.add(req)
    db.session.commit()
    flash("Requirement added.", "success")
    return redirect(url_for('employment.manage_requirements', job_id=job_id))


@employment_bp.route('/requirements/delete/<int:req_id>', methods=['POST'])
@login_required
def delete_requirement(req_id):
    if current_user.role != 'recruiter':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    req = EmploymentRequirement.query.get_or_404(req_id)
    job = Job.query.get_or_404(req.job_id)
    if job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(req)
    db.session.commit()
    flash("Requirement removed.", "success")
    return redirect(url_for('employment.manage_requirements', job_id=req.job_id))


# ================================================================
# ── APPLICANT: Submit employment documents ──
# ================================================================

@employment_bp.route('/submit/<int:app_id>', methods=['GET', 'POST'])
@login_required
def submit_documents(app_id):
    """Applicant uploads their employment requirement documents."""
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.filter_by(
        id=app_id, applicant_id=current_user.id
    ).first_or_404()

    if application.status != 'accepted':
        flash("You can only submit documents for accepted applications.", "warning")
        return redirect(url_for('applicant.dashboard'))

    # Check already an employee
    existing_emp = Employee.query.filter_by(application_id=app_id).first()
    if existing_emp and existing_emp.status == 'active':
        flash("You are already confirmed as an employee for this job.", "info")
        return redirect(url_for('applicant.dashboard'))

    job          = application.job
    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).all()

    # Build existing submissions map  req_id → submission
    submissions_map = {
        s.requirement_id: s
        for s in EmploymentSubmission.query.filter_by(application_id=app_id).all()
    }

    if request.method == 'POST':
        folder = os.path.join(
            current_app.root_path, 'static', 'uploads', 'employment_docs'
        )
        os.makedirs(folder, exist_ok=True)

        uploaded_any = False
        for req in requirements:
            file = request.files.get(f'doc_{req.id}')
            if not file or file.filename == '':
                continue
            if not _allowed_doc(file.filename):
                flash(f"Invalid file type for {req.name}. Use PDF, JPG, or PNG.", "danger")
                continue

            file.seek(0, 2); size = file.tell(); file.seek(0)
            if size > 10 * 1024 * 1024:
                flash(f"{req.name} exceeds 10 MB limit.", "danger")
                continue

            ext      = os.path.splitext(file.filename.lower())[1]
            filename = f"emp_{current_user.id}_{req.id}_{uuid.uuid4().hex[:8]}{ext}"
            file.save(os.path.join(folder, filename))

            # Upsert submission
            sub = submissions_map.get(req.id)
            if sub:
                # Remove old file
                old = os.path.join(folder, sub.file_path) if sub.file_path else None
                if old and os.path.exists(old):
                    os.remove(old)
                sub.file_path    = filename
                sub.uploaded_at  = datetime.utcnow()
                sub.review_status = 'pending'
                sub.review_note  = None
                sub.reviewed_by  = None
                sub.reviewed_at  = None
            else:
                sub = EmploymentSubmission(
                    application_id=app_id,
                    requirement_id=req.id,
                    file_path=filename,
                    uploaded_at=datetime.utcnow(),
                )
                db.session.add(sub)
                submissions_map[req.id] = sub

            uploaded_any = True

        if uploaded_any:
            db.session.commit()

            # Notify recruiter + assigned HR
            job_owner = User.query.get(job.company_id)
            notif = RecruiterNotification(
                recruiter_id=job.company_id,
                type='employment_docs',
                message=(
                    f"<strong>{current_user.username}</strong> submitted employment "
                    f"documents for <strong>{job.title}</strong>."
                ),
                application_id=app_id,
                job_id=job.id,
            )
            db.session.add(notif)

            from models import JobTeamMember, HRNotification as HRN
            for tm in job.team_members:
                db.session.add(HRN(
                    hr_id=tm.hr_id,
                    type='employment_docs',
                    message=(
                        f"<strong>{current_user.username}</strong> submitted employment "
                        f"documents for <strong>{job.title}</strong>."
                    ),
                    application_id=app_id,
                    job_id=job.id,
                ))

            db.session.commit()
            flash("Documents submitted successfully! Awaiting review.", "success")

        return redirect(url_for('employment.submit_documents', app_id=app_id))

    return render_template(
        'employment/submit_documents.html',
        application=application,
        job=job,
        requirements=requirements,
        submissions_map=submissions_map,
    )


# ================================================================
# ── RECRUITER / HR: Review submitted documents ──
# ================================================================

@employment_bp.route('/review/<int:app_id>', methods=['GET'])
@login_required
def review_documents(app_id):
    """Recruiter or assigned HR reviews applicant's submitted employment docs."""
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job = application.job

    # Permission check
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

    requirements   = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    submissions    = EmploymentSubmission.query.filter_by(application_id=app_id).all()
    submissions_map = {s.requirement_id: s for s in submissions}
    existing_emp   = Employee.query.filter_by(application_id=app_id).first()
    applicant      = User.query.get(application.applicant_id)

    # Is employment confirmable?
    all_required_approved = all(
        submissions_map.get(r.id) and submissions_map[r.id].review_status == 'approved'
        for r in requirements if r.is_required
    )

    return render_template(
        'employment/review_documents.html',
        application=application,
        job=job,
        applicant=applicant,
        requirements=requirements,
        submissions_map=submissions_map,
        existing_emp=existing_emp,
        all_required_approved=all_required_approved,
    )


@employment_bp.route('/review/doc/<int:sub_id>', methods=['POST'])
@login_required
def review_single_doc(sub_id):
    """Approve or reject a single submitted document."""
    if current_user.role not in ('recruiter', 'hr'):
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    sub = EmploymentSubmission.query.get_or_404(sub_id)
    app = Application.query.get_or_404(sub.application_id)
    job = app.job

    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    if current_user.role == 'hr':
        from models import JobTeamMember
        if not JobTeamMember.query.filter_by(job_id=job.id, hr_id=current_user.id).first():
            return jsonify({'success': False, 'error': 'Not assigned'}), 403

    action = request.form.get('action')   # 'approve' | 'reject'
    note   = request.form.get('note', '').strip()

    if action == 'approve':
        sub.review_status = 'approved'
    elif action == 'reject':
        sub.review_status = 'rejected'
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for('employment.review_documents', app_id=sub.application_id))

    sub.review_note = note
    sub.reviewed_by = current_user.id
    sub.reviewed_at = datetime.utcnow()
    db.session.commit()

    # Notify applicant
    req  = EmploymentRequirement.query.get(sub.requirement_id)
    verb = "approved" if action == 'approve' else "rejected"
    db.session.add(ApplicantNotification(
        applicant_id=app.applicant_id,
        type='employment_docs',
        message=(
            f"Your document <strong>{req.name}</strong> for "
            f"<strong>{job.title}</strong> has been <strong>{verb}</strong>."
            + (f" Note: {note}" if note else "")
        ),
        application_id=app.id,
        job_id=job.id,
    ))
    db.session.commit()

    flash(f"Document {verb}.", "success")
    return redirect(url_for('employment.review_documents', app_id=sub.application_id))


# ================================================================
# ── RECRUITER / HR: Confirm Employment ──
# ================================================================

@employment_bp.route('/confirm/<int:app_id>', methods=['POST'])
@login_required
def confirm_employment(app_id):
    """
    Recruiter or assigned HR confirms the applicant as an employee.
    After this, the application status is locked — no further edits.
    """
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job = application.job

    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if current_user.role == 'hr':
        from models import JobTeamMember
        if not JobTeamMember.query.filter_by(job_id=job.id, hr_id=current_user.id).first():
            flash("You are not assigned to this job.", "warning")
            return redirect(url_for('hr.job_list'))

    # Guard: already an employee
    existing = Employee.query.filter_by(application_id=app_id).first()
    if existing:
        flash("This applicant is already confirmed as an employee.", "info")
        return redirect(url_for('employment.review_documents', app_id=app_id))

    # Guard: all required docs must be approved
    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    submissions_map = {
        s.requirement_id: s
        for s in EmploymentSubmission.query.filter_by(application_id=app_id).all()
    }
    for r in requirements:
        if r.is_required:
            sub = submissions_map.get(r.id)
            if not sub or sub.review_status != 'approved':
                flash(
                    f"Cannot confirm: required document '{r.name}' is not yet approved.",
                    "warning"
                )
                return redirect(url_for('employment.review_documents', app_id=app_id))

    # Create Employee record
    employee = Employee(
        user_id=application.applicant_id,
        job_id=job.id,
        application_id=app_id,
        recruiter_id=job.company_id,
        confirmed_by=current_user.id,
        confirmed_at=datetime.utcnow(),
        status='active',
    )
    db.session.add(employee)

    # Lock the application — no further status edits allowed
    application.status = 'employed'
    db.session.flush()

    # Notify applicant
    db.session.add(ApplicantNotification(
        applicant_id=application.applicant_id,
        type='employment_confirmed',
        message=(
            f"🎉 Congratulations! You have been officially confirmed as an employee "
            f"for <strong>{job.title}</strong>."
        ),
        application_id=app_id,
        job_id=job.id,
    ))

    db.session.commit()
    flash("Employment confirmed! The applicant is now an employee.", "success")
    return redirect(url_for('employment.review_documents', app_id=app_id))


# ================================================================
# ── RECRUITER: Employee list per job ──
# ================================================================

@employment_bp.route('/employees/<int:job_id>')
@login_required
def employee_list(job_id):
    """Recruiter views all employees for a specific job."""
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    employees = Employee.query.filter_by(job_id=job_id).all()

    return render_template(
        'employment/employee_list.html',
        job=job,
        employees=employees,
    )


@employment_bp.route('/employees/all')
@login_required
def all_employees():
    """Recruiter views all employees across all their jobs."""
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    jobs      = Job.query.filter_by(company_id=current_user.id).all()
    job_ids   = [j.id for j in jobs]
    employees = Employee.query.filter(Employee.job_id.in_(job_ids)).all() if job_ids else []

    return render_template(
        'employment/all_employees.html',
        jobs=jobs,
        employees=employees,
    )


# ================================================================
# ── RECRUITER: Fire (terminate) an employee ──
# ================================================================

@employment_bp.route('/terminate/<int:employee_id>', methods=['POST'])
@login_required
def terminate_employee(employee_id):
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    emp = Employee.query.get_or_404(employee_id)
    job = Job.query.get_or_404(emp.job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('employment.all_employees'))

    if emp.status != 'active':
        flash("This employee is no longer active.", "warning")
        return redirect(url_for('employment.all_employees'))

    reason = request.form.get('reason', '').strip()

    emp.status     = 'terminated'
    emp.ended_at   = datetime.utcnow()
    emp.end_reason = reason

    db.session.add(ApplicantNotification(
        applicant_id=emp.user_id,
        type='employment_ended',
        message=(
            f"Your employment for <strong>{job.title}</strong> has been terminated."
            + (f" Reason: {reason}" if reason else "")
        ),
        job_id=job.id,
    ))
    db.session.commit()

    flash("Employee has been terminated.", "success")
    return redirect(url_for('employment.employee_list', job_id=job.id))


# ================================================================
# ── APPLICANT: Resign from a job ──
# ================================================================

@employment_bp.route('/resign/<int:employee_id>', methods=['POST'])
@login_required
def resign(employee_id):
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    emp = Employee.query.filter_by(
        id=employee_id, user_id=current_user.id
    ).first_or_404()

    if emp.status != 'active':
        flash("You are no longer active in this job.", "warning")
        return redirect(url_for('applicant.dashboard'))

    reason = request.form.get('reason', '').strip()

    emp.status     = 'resigned'
    emp.ended_at   = datetime.utcnow()
    emp.end_reason = reason

    job = Job.query.get(emp.job_id)

    # Notify recruiter
    db.session.add(RecruiterNotification(
        recruiter_id=emp.recruiter_id,
        type='employment_ended',
        message=(
            f"<strong>{current_user.username}</strong> has resigned from "
            f"<strong>{job.title if job else 'the job'}</strong>."
            + (f" Reason: {reason}" if reason else "")
        ),
        job_id=emp.job_id,
    ))

    db.session.commit()
    flash("You have successfully resigned from the job.", "success")
    return redirect(url_for('applicant.dashboard'))


# ================================================================
# ── APPLICANT: View employment status / profile badge ──
# ================================================================

@employment_bp.route('/my-employment')
@login_required
def my_employment():
    """Applicant views their current and past employment records."""
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    records = Employee.query.filter_by(user_id=current_user.id).order_by(Employee.created_at.desc()).all()

    return render_template(
        'employment/my_employment.html',
        records=records,
    )