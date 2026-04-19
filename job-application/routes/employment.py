# ================================================================
# EMPLOYMENT ROUTES  —  routes/employment.py
# ================================================================

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime
import os, uuid
from models import (
    db, Job, Application, User,
    ApplicantNotification, RecruiterNotification, HRNotification,
    EmploymentRequirement, EmploymentSubmission, Employee
)

employment_bp = Blueprint('employment', __name__, url_prefix='/employment')

ALLOWED_DOC_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}


def _allowed_doc(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_DOC_EXTENSIONS


# ================================================================
# ── RECRUITER: Manage employment requirements per job ──
# ================================================================

@employment_bp.route('/requirements/<int:job_id>', methods=['GET', 'POST'])
@login_required
def manage_requirements(job_id):
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
            title       = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            is_required = request.form.get('is_required') == '1'

            if not title:
                flash("Document title is required.", "danger")
                return redirect(url_for('employment.manage_requirements', job_id=job_id))

            req = EmploymentRequirement(
                job_id=job_id,
                title=title,
                description=description,
                is_required=is_required,
            )
            db.session.add(req)
            db.session.commit()
            flash("Requirement added.", "success")

        elif action == 'delete':
            req_id = request.form.get('req_id', type=int)
            req = EmploymentRequirement.query.get_or_404(req_id)
            if req.job_id == job_id:
                db.session.delete(req)
                db.session.commit()
                flash("Requirement removed.", "success")
            else:
                flash("Unauthorized!", "danger")

        return redirect(url_for('employment.manage_requirements', job_id=job_id))

    # GET
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
        title=name,          # FIXED: model column is 'title', not 'name'
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
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.filter_by(
        id=app_id, applicant_id=current_user.id
    ).first_or_404()

    if application.status not in ('accepted', 'employed'):
        flash("You can only submit documents for accepted applications.", "warning")
        return redirect(url_for('applicant.status'))

    existing_emp = Employee.query.filter_by(application_id=app_id).first()
    if existing_emp and existing_emp.employment_status == 'active':
        flash("You are already confirmed as an employee for this job.", "info")
        return redirect(url_for('employment.employment_status', app_id=app_id))

    job          = application.job
    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).all()

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
            file = request.files.get(f'req_{req.id}')
            if not file or file.filename == '':
                continue
            if not _allowed_doc(file.filename):
                flash(f"Invalid file type for {req.title}. Use PDF, JPG, or PNG.", "danger")
                continue

            file.seek(0, 2); size = file.tell(); file.seek(0)
            if size > 10 * 1024 * 1024:
                flash(f"{req.title} exceeds 10 MB limit.", "danger")
                continue

            ext      = os.path.splitext(file.filename.lower())[1]
            filename = f"emp_{current_user.id}_{req.id}_{uuid.uuid4().hex[:8]}{ext}"
            file.save(os.path.join(folder, filename))

            sub = submissions_map.get(req.id)
            if sub:
                old = os.path.join(folder, sub.file_path) if sub.file_path else None
                if old and os.path.exists(old):
                    os.remove(old)
                sub.file_path    = filename
                sub.submitted_at = datetime.utcnow()
                sub.notes        = None
            else:
                sub = EmploymentSubmission(
                    application_id=app_id,
                    requirement_id=req.id,
                    file_path=filename,
                )
                db.session.add(sub)
                submissions_map[req.id] = sub

            uploaded_any = True

        if uploaded_any:
            db.session.commit()

            from models import EmploymentOnboarding
            onboarding = EmploymentOnboarding.query.filter_by(application_id=app_id).first()
            if onboarding:
                # Allow re-submission from needs_revision OR already submitted
                if onboarding.status in ('pending_submission', 'needs_revision', 'submitted'):
                    onboarding.status = 'submitted'
                    onboarding.submitted_at = datetime.utcnow()
            else:
                onboarding = EmploymentOnboarding(
                    application_id=app_id,
                    status='submitted',
                    submitted_at=datetime.utcnow()
                )
                db.session.add(onboarding)

            db.session.add(RecruiterNotification(
                recruiter_id=job.company_id,
                type='employment_docs',
                message=(
                    f"<strong>{current_user.username}</strong> submitted employment "
                    f"documents for <strong>{job.title}</strong>."
                ),
                application_id=app_id,
                job_id=job.id,
            ))

            from models import JobTeamMember
            for tm in job.team_members:
                db.session.add(HRNotification(
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

    # ── GET ──
    from models import EmploymentOnboarding, RecruiterProfile

    onboarding = EmploymentOnboarding.query.filter_by(application_id=app_id).first()

    if not onboarding:
        onboarding = EmploymentOnboarding(
            application_id=app_id,
            status='pending_submission'
        )
        db.session.add(onboarding)
        db.session.commit()

    recruiter_profile = RecruiterProfile.query.filter_by(
        user_id=job.company_id
    ).first()

    return render_template(
        'employment/submit_documents.html',
        application=application,
        job=job,
        requirements=requirements,
        submissions_map=submissions_map,
        existing=submissions_map,
        onboarding=onboarding,
        recruiter_profile=recruiter_profile,
    )


# ================================================================
# ── RECRUITER / HR: Review submitted documents ──
# ================================================================

@employment_bp.route('/review/<int:app_id>', methods=['GET', 'POST'])
@login_required
def review_documents(app_id):
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
        assigned = JobTeamMember.query.filter_by(
            job_id=job.id, hr_id=current_user.id
        ).first()
        if not assigned:
            flash("You are not assigned to this job.", "warning")
            return redirect(url_for('hr.job_list'))

    # ── Handle POST actions (confirm / request_revision) ──
    if request.method == 'POST':
        from models import EmploymentOnboarding
        action = request.form.get('action')
        onboarding = EmploymentOnboarding.query.filter_by(application_id=app_id).first()

        if action == 'confirm' and onboarding:
            existing_emp = Employee.query.filter_by(application_id=app_id).first()
            if not existing_emp:
                recruiter_user = User.query.get(job.company_id)
                company_name = None
                if recruiter_user and recruiter_user.recruiter_profile:
                    company_name = recruiter_user.recruiter_profile.company_name

                employee = Employee(
                    user_id=application.applicant_id,
                    job_id=job.id,
                    application_id=app_id,
                    confirmed_by=current_user.id,
                    job_title=job.title,
                    company_name=company_name,
                    employment_status='active',
                )
                db.session.add(employee)
                application.status = 'employed'
                onboarding.status = 'confirmed'
                onboarding.reviewed_at = datetime.utcnow()

                from models import ApplicantNotification
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
            else:
                flash("Already confirmed.", "info")

        elif action == 'request_revision' and onboarding:
            note = request.form.get('reviewer_note', '').strip()
            onboarding.status = 'needs_revision'
            onboarding.reviewer_note = note
            onboarding.reviewed_at = datetime.utcnow()

            from models import ApplicantNotification
            db.session.add(ApplicantNotification(
                applicant_id=application.applicant_id,
                type='employment_docs',
                message=(
                    f"Your employment documents for <strong>{job.title}</strong> require revision."
                    + (f" Note: {note}" if note else "")
                ),
                application_id=app_id,
                job_id=job.id,
            ))
            db.session.commit()
            flash("Revision requested.", "warning")

        return redirect(url_for('employment.review_documents', app_id=app_id))

    # ── GET ──
    from models import EmploymentOnboarding

    requirements    = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    submissions     = EmploymentSubmission.query.filter_by(application_id=app_id).all()
    submissions_map = {s.requirement_id: s for s in submissions}
    existing_emp    = Employee.query.filter_by(application_id=app_id).first()
    applicant       = User.query.get(application.applicant_id)

    # ── Fetch onboarding so the sidebar shows correct status ──
    onboarding = EmploymentOnboarding.query.filter_by(application_id=app_id).first()

    return render_template(
        'employment/review_documents.html',
        application=application,
        job=job,
        applicant=applicant,
        requirements=requirements,
        submissions_map=submissions_map,
        existing=submissions_map,
        existing_emp=existing_emp,
        onboarding=onboarding,      # ← this was missing
    )


# ================================================================
# ── RECRUITER / HR: Confirm Employment ──
# ================================================================

@employment_bp.route('/confirm/<int:app_id>', methods=['POST'])
@login_required
def confirm_employment(app_id):
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)
    job         = application.job

    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if current_user.role == 'hr':
        from models import JobTeamMember
        if not JobTeamMember.query.filter_by(job_id=job.id, hr_id=current_user.id).first():
            flash("You are not assigned to this job.", "warning")
            return redirect(url_for('hr.job_list'))

    existing = Employee.query.filter_by(application_id=app_id).first()
    if existing:
        flash("This applicant is already confirmed as an employee.", "info")
        return redirect(url_for('employment.review_documents', app_id=app_id))

    requirements    = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    submissions_map = {
        s.requirement_id: s
        for s in EmploymentSubmission.query.filter_by(application_id=app_id).all()
    }

    for r in requirements:
        if r.is_required:
            sub = submissions_map.get(r.id)
            if not sub or sub.notes != 'approved':  # FIXED: sub.notes
                flash(
                    f"Cannot confirm: required document '{r.title}' is not yet approved.",  # FIXED: r.title
                    "warning"
                )
                return redirect(url_for('employment.review_documents', app_id=app_id))

    # Resolve company name safely
    recruiter_user = User.query.get(job.company_id)
    company_name   = None
    if recruiter_user and recruiter_user.recruiter_profile:
        company_name = recruiter_user.recruiter_profile.company_name

    employee = Employee(
        user_id=application.applicant_id,
        job_id=job.id,
        application_id=app_id,
        confirmed_by=current_user.id,
        job_title=job.title,
        company_name=company_name,
        employment_status='active',  # FIXED
    )
    db.session.add(employee)

    application.status = 'employed'
    db.session.flush()

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
# ── RECRUITER: Terminate an employee ──
# ================================================================

@employment_bp.route('/terminate/<int:employee_id>', methods=['POST'])
@login_required
def fire_employee(employee_id):
    if current_user.role != 'recruiter':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    emp = Employee.query.get_or_404(employee_id)
    job = Job.query.get_or_404(emp.job_id)

    if job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('employment.all_employees'))

    if emp.employment_status != 'active':
        flash("This employee is no longer active.", "warning")
        return redirect(url_for('employment.all_employees'))

    reason = request.form.get('reason', '').strip()

    emp.employment_status = 'fired'
    emp.ended_at          = datetime.utcnow()
    emp.end_reason        = reason

    # ── FIX: reset application status so slot is freed
    application = Application.query.get(emp.application_id)
    if application:
        application.status = 'fired'

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
# ── APPLICANT: View employment status & resign ──
# ================================================================

@employment_bp.route('/my-employment/<int:app_id>')
@login_required
def employment_status(app_id):
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.filter_by(
        id=app_id, applicant_id=current_user.id
    ).first_or_404()

    emp = Employee.query.filter_by(application_id=app_id).first_or_404()
    job = application.job

    from models import EmploymentOnboarding, RecruiterProfile
    onboarding = EmploymentOnboarding.query.filter_by(application_id=app_id).first()
    recruiter_profile = RecruiterProfile.query.filter_by(user_id=job.company_id).first()

    requirements = EmploymentRequirement.query.filter_by(job_id=job.id).all()
    submissions_map = {
        s.requirement_id: s
        for s in EmploymentSubmission.query.filter_by(application_id=app_id).all()
    }

    return render_template(
        'employment/employment_status.html',
        application=application,
        emp=emp,
        job=job,
        onboarding=onboarding,
        recruiter_profile=recruiter_profile,
        requirements=requirements,
        submissions_map=submissions_map,
    )

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
 
    if emp.employment_status != 'active':
        flash("You are no longer active in this job.", "warning")
        return redirect(url_for('applicant.status'))
 
    reason = request.form.get('reason', '').strip()
    job    = Job.query.get(emp.job_id)
 
    # Update Employee record
    emp.employment_status = 'resigned'
    emp.ended_at          = datetime.utcnow()
    emp.end_reason        = reason
 
    # ── CRITICAL FIX: sync Application.status so the applicant side
    #    stops showing "Employed" and the slot is freed for quota counting
    application = Application.query.get(emp.application_id)
    if application:
        application.status = 'resigned'
 
    db.session.add(RecruiterNotification(
        recruiter_id=job.company_id,
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
    return redirect(url_for('applicant.status'))

# ================================================================
# ── APPLICANT: View employment records ──
# ================================================================

@employment_bp.route('/my-employment')
@login_required
def my_employment():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    records = Employee.query.filter_by(
        user_id=current_user.id
    ).order_by(Employee.confirmed_at.desc()).all()  # FIXED: confirmed_at not created_at

    return render_template(
        'employment/my_employment.html',
        records=records,
    )