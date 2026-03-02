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
    return render_template('hr_dashboard.html', applications=applications)

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