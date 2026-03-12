from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Application

hr_bp = Blueprint('hr', __name__, url_prefix="/hr")

@hr_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    applications = Application.query.join(Application.job).filter_by(company_id=current_user.created_by).all()
    return render_template('hr/hr_dashboard.html', applications=applications)

@hr_bp.route('/review/<int:app_id>', methods=['POST'])
@login_required
def review(app_id):
    if current_user.role != 'hr':
        flash("Access denied!", "danger")
        return redirect(url_for('auth.index'))

    application = Application.query.get(app_id)
    status = request.form['status']
    remarks = request.form['remarks']

    application.status = status
    application.remarks = remarks
    db.session.commit()
    flash("Application reviewed successfully!", "success")
    return redirect(url_for('hr.dashboard'))

from werkzeug.security import generate_password_hash

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