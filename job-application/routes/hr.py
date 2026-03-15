from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Application, Job
from werkzeug.security import generate_password_hash

hr_bp = Blueprint('hr', __name__, url_prefix="/hr")


# =========================
# HR DASHBOARD
# =========================
@hr_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    applications = Application.query.join(Application.job).filter_by(
        company_id=current_user.created_by
    ).all()

    return render_template(
        'hr/dashboard.html',
        applications=applications
    )


# =========================
# REVIEW APPLICATION
# =========================
@hr_bp.route('/review/<int:app_id>', methods=['POST'])
@login_required
def review(app_id):

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get_or_404(app_id)

    status = request.form['status']
    remarks = request.form['remarks']

    application.status = status
    application.remarks = remarks

    db.session.commit()

    flash("Application reviewed successfully!", "success")

    return redirect(url_for('hr.dashboard'))


# =========================
# CHANGE PASSWORD
# =========================
@hr_bp.route('/change-password', methods=['GET','POST'])
@login_required
def change_password():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    if request.method == "POST":

        new_password = request.form.get("password")

        current_user.password = generate_password_hash(new_password)
        current_user.must_change_password = False

        db.session.commit()

        flash("Password changed successfully!", "success")

        return redirect(url_for("hr.dashboard"))

    return render_template("hr/change_password.html")

# ===============================
# HR JOB LIST (VIEW ALL JOBS)
# ===============================
@hr_bp.route('/job-list')
@login_required
def job_list():
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
    
    jobs = Job.query.all()
    return render_template("hr/hr_job_list.html", jobs=jobs)


# ===============================
# HR VIEW JOB APPLICATIONS (SPECIFIC JOB)
# ===============================
@hr_bp.route('/job-applications/<int:job_id>')
@login_required
def view_job_applications(job_id):
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
    
    job = Job.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).all()
    
    return render_template(
        "hr/hr_job_applications.html",
        job=job,
        applications=applications
    )


# ===============================
# HR UPDATE APPLICATION STATUS
# ===============================
@hr_bp.route('/update-application-status/<int:app_id>', methods=['POST'])
@login_required
def update_application_status(app_id):
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))
    
    application = Application.query.get_or_404(app_id)
    job = Job.query.get_or_404(application.job_id)
    
    new_status = request.form.get('status')
    if new_status and new_status in ['pending', 'Interview', 'accepted', 'rejected']:
        application.status = new_status
        flash(f"Application status updated to {new_status}!", "success")
    
    new_remarks = request.form.get('remarks')
    if new_remarks is not None:
        application.remarks = new_remarks
        flash("Remarks updated successfully!", "success")
    
    db.session.commit()
    
    return redirect(url_for('hr.view_job_applications', job_id=job.id))