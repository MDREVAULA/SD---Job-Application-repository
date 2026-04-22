# ================================================================
# EMPLOYMENT ROUTES  —  routes/employment.py
# ================================================================

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime, date as date_type
import os, uuid
from models import (
    db, Job, Application, User,
    ApplicantNotification, RecruiterNotification, HRNotification,
    EmploymentRequirement, EmploymentSubmission, Employee,
    ResignationRequest, get_ph_time
)

employment_bp = Blueprint('employment', __name__, url_prefix='/employment')

ALLOWED_DOC_EXTENSIONS    = {'.pdf', '.jpg', '.jpeg', '.png'}
ALLOWED_LETTER_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}


def _allowed_doc(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_DOC_EXTENSIONS


def _allowed_letter(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_LETTER_EXTENSIONS


# ================================================================
# ── RECRUITER: Manage employment requirements per job ──
# ================================================================

@employment_bp.route('/requirements/<int:job_id>', methods=['GET', 'POST'])
@login_required
def manage_requirements(job_id):
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    # Recruiters must own the job
    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    # HR: only assigned HR can POST, but any HR under that recruiter can GET
    if current_user.role == 'hr':
        from models import JobTeamMember
        is_assigned = JobTeamMember.query.filter_by(
            job_id=job.id, hr_id=current_user.id
        ).first()
        if request.method == 'POST' and not is_assigned:
            flash("You are not assigned to manage this job.", "warning")
            return redirect(url_for('hr.job_list'))

    if request.method == 'POST':
        # ... keep existing POST logic unchanged ...
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
                EmploymentSubmission.query.filter_by(requirement_id=req_id).delete()
                db.session.delete(req)
                db.session.commit()
                flash("Requirement removed.", "success")
            else:
                flash("Unauthorized!", "danger")

        return redirect(url_for('employment.manage_requirements', job_id=job_id))

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
        title=name,
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

    job_id = req.job_id  # save before delete
    # Delete related submissions first
    EmploymentSubmission.query.filter_by(requirement_id=req_id).delete()
    db.session.delete(req)
    db.session.commit()
    flash("Requirement removed.", "success")
    return redirect(url_for('employment.manage_requirements', job_id=job_id))


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
                sub.submitted_at = get_ph_time()
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
                if onboarding.status in ('pending_submission', 'needs_revision', 'submitted'):
                    onboarding.status = 'submitted'
                    onboarding.submitted_at = get_ph_time()
            else:
                onboarding = EmploymentOnboarding(
                    application_id=app_id,
                    status='submitted',
                    submitted_at=get_ph_time()
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
                onboarding.reviewed_at = get_ph_time()

                from models import ApplicantNotification
                db.session.add(ApplicantNotification(
                    applicant_id=application.applicant_id,
                    type='employment_confirmed',
                    message=(
                        f"Congratulations! You have been officially confirmed as an employee "
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
            onboarding.reviewed_at = get_ph_time()

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
    onboarding      = EmploymentOnboarding.query.filter_by(application_id=app_id).first()

    return render_template(
        'employment/review_documents.html',
        application=application,
        job=job,
        applicant=applicant,
        requirements=requirements,
        submissions_map=submissions_map,
        existing=submissions_map,
        existing_emp=existing_emp,
        onboarding=onboarding,
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
            if not sub or sub.notes != 'approved':
                flash(
                    f"Cannot confirm: required document '{r.title}' is not yet approved.",
                    "warning"
                )
                return redirect(url_for('employment.review_documents', app_id=app_id))

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
        employment_status='active',
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
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    # HR: allow all HR under the same recruiter to view, 
    # but only assigned HR can take actions
    if current_user.role == 'hr':
        if job.company_id != current_user.created_by:
            flash("You do not have access to this job.", "warning")
            return redirect(url_for('hr.job_list'))

    from models import JobTeamMember
    is_assigned = JobTeamMember.query.filter_by(
        job_id=job_id, hr_id=current_user.id
    ).first() if current_user.role == 'hr' else True

    employees = Employee.query.filter_by(job_id=job_id).all()

    from models import EmploymentOnboarding
    pending_onboardings = []
    no_onboarding_apps  = []

    _ACCEPTED_STATUSES = ('accepted', 'employed')
    accepted_apps = Application.query.filter(
        Application.job_id == job_id,
        Application.status.in_(_ACCEPTED_STATUSES)
    ).all()

    confirmed_app_ids = {e.application_id for e in employees}

    for app in accepted_apps:
        if app.id in confirmed_app_ids:
            continue
        ob = EmploymentOnboarding.query.filter_by(application_id=app.id).first()
        if ob:
            pending_onboardings.append((ob, app))
        else:
            no_onboarding_apps.append(app)

    return render_template(
        'employment/employee_list.html',
        job=job,
        employees=employees,
        pending_onboardings=pending_onboardings,
        no_onboarding_apps=no_onboarding_apps,
        is_assigned=is_assigned,  # pass this to template
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

    # Block firing someone who is in rendering period
    if emp.employment_status == 'rendering':
        flash("This employee is in their rendering period and cannot be terminated.", "warning")
        return redirect(url_for('employment.employee_list', job_id=job.id))

    if emp.employment_status not in ('active', 'resignation_pending'):
        flash("This employee is no longer active.", "warning")
        return redirect(url_for('employment.employee_list', job_id=job.id))

    reason = request.form.get('fire_reason', '').strip()

    emp.employment_status = 'fired'
    emp.ended_at          = get_ph_time()
    emp.end_reason        = reason

    application = Application.query.get(emp.application_id)
    if application:
        application.status = 'fired'

    # If there was a pending resignation, mark it rejected
    if emp.resignation_request:
        emp.resignation_request.status = 'rejected'
        emp.resignation_request.reviewer_note = 'Employment terminated by recruiter.'
        emp.resignation_request.reviewed_by   = current_user.id
        emp.resignation_request.reviewed_at   = get_ph_time()
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
# ── RECRUITER / HR: Review a resignation request ──
# ================================================================

@employment_bp.route('/resign/review/<int:resignation_id>', methods=['GET', 'POST'])
@login_required
def review_resignation(resignation_id):
    if current_user.role not in ('recruiter', 'hr'):
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    resignation = ResignationRequest.query.get_or_404(resignation_id)
    emp  = resignation.employee
    job  = resignation.job

    if current_user.role == 'recruiter' and job.company_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('recruiter.my_job_list'))

    if current_user.role == 'hr':
        # Must be under the same recruiter
        if job.company_id != current_user.created_by:
            flash("You do not have access to this job.", "warning")
            return redirect(url_for('hr.job_list'))
        
        from models import JobTeamMember
        is_assigned = JobTeamMember.query.filter_by(
            job_id=job.id, hr_id=current_user.id
        ).first()
        
        # Block POST actions for non-assigned HR
        if request.method == 'POST' and not is_assigned:
            flash("You are not assigned to take actions on this job.", "warning")
            return redirect(url_for('employment.review_resignation', resignation_id=resignation_id))

    # ... keep rest of POST logic unchanged ...
    if request.method == 'POST':
        from models import EmploymentOnboarding
        action = request.form.get('action')
        reviewer_note = request.form.get('reviewer_note', '').strip()

        if action == 'approve':
            resignation.status        = 'approved'
            resignation.reviewer_note = reviewer_note or None
            resignation.reviewed_by   = current_user.id
            resignation.reviewed_at   = get_ph_time()
            emp.employment_status = 'rendering'
            emp.end_reason        = resignation.reason
            db.session.add(ApplicantNotification(
                applicant_id = emp.user_id,
                type         = 'resignation_approved',
                message      = (
                    f"Your resignation from <strong>{job.title}</strong> has been approved. "
                    f"Your last day of work is <strong>{resignation.intended_last_day.strftime('%B %d, %Y')}</strong>."
                ),
                job_id = job.id,
            ))
            flash(f"Resignation approved.", "success")

        elif action == 'reject':
            if not reviewer_note:
                flash("Please provide a reason for rejecting the resignation.", "danger")
                return redirect(url_for('employment.review_resignation', resignation_id=resignation_id))
            resignation.status        = 'rejected'
            resignation.reviewer_note = reviewer_note
            resignation.reviewed_by   = current_user.id
            resignation.reviewed_at   = get_ph_time()
            emp.employment_status = 'active'
            db.session.add(ApplicantNotification(
                applicant_id = emp.user_id,
                type         = 'resignation_rejected',
                message      = f"Your resignation from <strong>{job.title}</strong> has been rejected." + (f" Reason: {reviewer_note}" if reviewer_note else ""),
                job_id = job.id,
            ))
            flash("Resignation rejected.", "warning")

        elif action == 'request_revision':
            if not reviewer_note:
                flash("Please provide a note explaining what needs to be changed.", "danger")
                return redirect(url_for('employment.review_resignation', resignation_id=resignation_id))
            resignation.status        = 'revision_requested'
            resignation.reviewer_note = reviewer_note
            resignation.reviewed_by   = current_user.id
            resignation.reviewed_at   = get_ph_time()
            emp.employment_status = 'active'
            db.session.add(ApplicantNotification(
                applicant_id = emp.user_id,
                type         = 'resignation_revision',
                message      = f"Your resignation request for <strong>{job.title}</strong> requires revision." + (f" Note: {reviewer_note}" if reviewer_note else ""),
                job_id = job.id,
            ))
            flash("Revision requested.", "info")

        db.session.commit()
        return redirect(url_for('employment.review_resignation', resignation_id=resignation_id))

    from models import JobTeamMember
    is_assigned = JobTeamMember.query.filter_by(
        job_id=job.id, hr_id=current_user.id
    ).first() if current_user.role == 'hr' else True

    applicant = User.query.get(emp.user_id)
    return render_template(
        'employment/review_resignation.html',
        resignation=resignation,
        emp=emp,
        job=job,
        applicant=applicant,
        today=date_type.today(),
        is_assigned=is_assigned,
    )


# ================================================================
# ── APPLICANT: Submit formal resignation request ──
# ================================================================

@employment_bp.route('/resign/submit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def submit_resignation(employee_id):
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    emp = Employee.query.filter_by(
        id=employee_id, user_id=current_user.id
    ).first_or_404()

    if emp.employment_status not in ('active', 'revision_requested'):
        if emp.employment_status == 'resignation_pending':
            flash("You already have a resignation request pending review.", "info")
        elif emp.employment_status == 'rendering':
            flash("Your resignation has already been approved. You are in your rendering period.", "info")
        else:
            flash("You are no longer active in this job.", "warning")
        return redirect(url_for('employment.my_employment'))

    existing = ResignationRequest.query.filter_by(employee_id=employee_id).first()

    # Block if an active pending/approved request already exists
    if existing and existing.status in ('pending', 'approved'):
        flash("You already have a resignation request in progress.", "info")
        return redirect(url_for('employment.my_employment'))

    job   = Job.query.get(emp.job_id)
    today = date_type.today()

    if request.method == 'POST':
        reason        = request.form.get('reason', '').strip()
        last_day_str  = request.form.get('intended_last_day', '').strip()
        letter_file_up = request.files.get('letter_file')

        # ── Validation ──
        if not reason:
            flash("Please provide a reason for your resignation.", "danger")
            return redirect(url_for('employment.submit_resignation', employee_id=employee_id))

        if not last_day_str:
            flash("Please provide your intended last day of work.", "danger")
            return redirect(url_for('employment.submit_resignation', employee_id=employee_id))

        try:
            last_day = datetime.strptime(last_day_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format for last day.", "danger")
            return redirect(url_for('employment.submit_resignation', employee_id=employee_id))

        if last_day <= today:
            flash(
                f"Your intended last day ({last_day.strftime('%B %d, %Y')}) must be a future date. "
                f"Today is {today.strftime('%B %d, %Y')}.",
                "danger"
            )
            return redirect(url_for('employment.submit_resignation', employee_id=employee_id))

        # ── Optional letter file upload ──
        letter_filename = None
        if letter_file_up and letter_file_up.filename != '':
            if not _allowed_letter(letter_file_up.filename):
                flash("Resignation letter must be PDF, JPG, PNG, DOC, or DOCX.", "danger")
                return redirect(url_for('employment.submit_resignation', employee_id=employee_id))

            letter_file_up.seek(0, 2); size = letter_file_up.tell(); letter_file_up.seek(0)
            if size > 10 * 1024 * 1024:
                flash("Resignation letter file exceeds 10MB.", "danger")
                return redirect(url_for('employment.submit_resignation', employee_id=employee_id))

            folder = os.path.join(
                current_app.root_path, 'static', 'uploads', 'resignation_letters'
            )
            os.makedirs(folder, exist_ok=True)
            ext = os.path.splitext(letter_file_up.filename.lower())[1]
            letter_filename = f"resign_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
            letter_file_up.save(os.path.join(folder, letter_filename))

        # ── Reuse existing rejected/revision_requested record or create new ──
        if existing and existing.status in ('rejected', 'revision_requested'):
            existing.reason            = reason
            existing.intended_last_day = last_day
            existing.status            = 'pending'
            existing.reviewer_note     = None
            existing.reviewed_by       = None
            existing.reviewed_at       = None
            existing.submitted_at      = get_ph_time()
            if letter_filename:
                existing.letter_file = letter_filename
            db.session.flush()
        else:
            new_res = ResignationRequest(
                employee_id       = employee_id,
                applicant_id      = current_user.id,
                job_id            = emp.job_id,
                reason            = reason,
                intended_last_day = last_day,
                letter_file       = letter_filename,
                status            = 'pending',
            )
            db.session.add(new_res)
            db.session.flush()

        emp.employment_status = 'resignation_pending'

        # Notify recruiter
        db.session.add(RecruiterNotification(
            recruiter_id = job.company_id,
            type         = 'resignation_submitted',
            message      = (
                f"<strong>{current_user.username}</strong> has submitted a resignation request "
                f"for <strong>{job.title}</strong>. Intended last day: "
                f"<strong>{last_day.strftime('%B %d, %Y')}</strong>."
            ),
            job_id = emp.job_id,
        ))

        # Notify assigned HR
        from models import JobTeamMember
        for tm in job.team_members:
            db.session.add(HRNotification(
                hr_id   = tm.hr_id,
                type    = 'resignation_submitted',
                message = (
                    f"<strong>{current_user.username}</strong> has submitted a resignation request "
                    f"for <strong>{job.title}</strong>. Intended last day: "
                    f"<strong>{last_day.strftime('%B %d, %Y')}</strong>."
                ),
                job_id = emp.job_id,
            ))

        # Confirm to applicant
        db.session.add(ApplicantNotification(
            applicant_id = current_user.id,
            type         = 'resignation_submitted',
            message      = (
                f"Your resignation request for <strong>{job.title}</strong> has been submitted. "
                f"Intended last day: <strong>{last_day.strftime('%B %d, %Y')}</strong>. "
                f"Awaiting review."
            ),
            job_id = emp.job_id,
        ))

        db.session.commit()
        flash("Resignation request submitted successfully. Awaiting review.", "success")
        return redirect(url_for('employment.my_employment'))

    # GET
    from datetime import timedelta
    
    return render_template(
        'employment/submit_resignation.html',
        emp=emp,
        job=job,
        today=today,
        existing=existing,
        min_last_day=(today + timedelta(days=1)).strftime('%Y-%m-%d'),  # ← add this
    )


# ================================================================
# ── BACKGROUND TASK: Process expired rendering periods ──
# Called from app.before_request in app.py on every request.
# ================================================================

def process_expired_rendering_periods():
    today = date_type.today()

    expired = (
        ResignationRequest.query
        .filter(
            ResignationRequest.status == 'approved',
            ResignationRequest.intended_last_day <= today,
        )
        .all()
    )

    for res in expired:
        emp = res.employee
        if emp and emp.employment_status == 'rendering':
            emp.employment_status = 'resigned'
            emp.ended_at          = get_ph_time()

            application = Application.query.get(emp.application_id)
            if application:
                application.status = 'resigned'

            job = res.job

            db.session.add(ApplicantNotification(
                applicant_id = emp.user_id,
                type         = 'employment_ended',
                message      = (
                    f"Your employment at <strong>{job.title if job else 'the company'}</strong> "
                    f"has officially ended. Thank you for your service."
                ),
                job_id = res.job_id,
            ))

            if job:
                db.session.add(RecruiterNotification(
                    recruiter_id = job.company_id,
                    type         = 'employment_ended',
                    message      = (
                        f"<strong>{emp.user.username}</strong>'s rendering period for "
                        f"<strong>{job.title}</strong> has ended. "
                        f"Employment has been officially concluded."
                    ),
                    job_id = job.id,
                ))

                for tm in job.team_members:
                    db.session.add(HRNotification(
                        hr_id   = tm.hr_id,
                        type    = 'employment_ended',
                        message = (
                            f"<strong>{emp.user.username}</strong>'s rendering period for "
                            f"<strong>{job.title}</strong> has ended. "
                            f"Employment has been officially concluded."
                        ),
                        job_id = job.id,
                    ))

    if expired:
        db.session.commit()


# ================================================================
# ── APPLICANT: View employment status (my-employment per app) ──
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
    onboarding        = EmploymentOnboarding.query.filter_by(application_id=app_id).first()
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
        today=date_type.today(), 
    )


# ================================================================
# ── APPLICANT: View all employment records ──
# ================================================================

@employment_bp.route('/my-employment')
@login_required
def my_employment():
    if current_user.role != 'applicant':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    records = Employee.query.filter_by(
        user_id=current_user.id
    ).order_by(Employee.confirmed_at.desc()).all()

    return render_template(
        'employment/my_employment.html',
        records=records,
    )