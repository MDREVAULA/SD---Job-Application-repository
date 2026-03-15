from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Application, Job
from werkzeug.security import generate_password_hash

hr_bp = Blueprint('hr', __name__, url_prefix="/hr")


# =========================
# HR PROFILE (DEFAULT PAGE)
# =========================
@hr_bp.route('/profile')
@login_required
def profile():

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    return render_template("hr/profile.html")


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

        return redirect(url_for("hr.profile"))

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

    jobs = Job.query.filter_by(company_id=current_user.created_by).all()

    return render_template(
        "hr/job_list.html",
        jobs=jobs
    )


# ===============================
# HR VIEW JOB APPLICATIONS
# ===============================
@hr_bp.route('/job-applications/<int:job_id>')
@login_required
def job_applications(job_id):

    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    job = Job.query.get_or_404(job_id)

    applications = Application.query.filter_by(
        job_id=job_id
    ).all()

    return render_template(
        "hr/job_applications.html",
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

    new_status = request.form.get('status')
    new_remarks = request.form.get('remarks')

    if new_status:
        application.status = new_status

    if new_remarks is not None:
        application.remarks = new_remarks

    db.session.commit()

    flash("Application updated successfully!", "success")

    return redirect(
        url_for('hr.job_applications', job_id=application.job_id)
    )