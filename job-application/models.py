from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# =========================
# USER TABLE
# =========================
class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)  # nullable for Google users

    role = db.Column(db.String(50), nullable=False)

    # Google OAuth
    google_id = db.Column(db.String(200), unique=True, nullable=True)

    # Temporary password system
    must_change_password = db.Column(db.Boolean, default=False)

    # Verification system
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default="Pending")
    verification_remarks = db.Column(db.Text)

    # HR created by recruiter
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Forgot password
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    profile_picture = db.Column(db.String(200), nullable=True)

    # =========================
    # RELATIONSHIPS
    # =========================
    applications = db.relationship(
        "Application",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    recruiter_profile = db.relationship(
        "RecruiterProfile",
        backref="user",
        uselist=False
    )

    hr_profile = db.relationship(
        "HRProfile",
        backref="user",
        uselist=False
    )

    hr_feedbacks = db.relationship(
        "HRFeedback",
        backref="hr_user",
        lazy=True
    )


# =========================
# APPLICANT PROFILE
# =========================
class ApplicantProfile(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))

    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))

    phone_number = db.Column(db.String(50))

    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    home_address = db.Column(db.String(200))


# =========================
# RECRUITER PROFILE
# =========================
class RecruiterProfile(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    surname = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))

    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    home_address = db.Column(db.String(200))

    phone_number = db.Column(db.String(50))

    # COMPANY INFORMATION
    company_name = db.Column(db.String(200))
    company_industry = db.Column(db.String(200))
    company_description = db.Column(db.Text)

    company_address = db.Column(db.String(200))

    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    office_address = db.Column(db.String(200))

    company_email_domain = db.Column(db.String(100))

    # FILES
    company_logo = db.Column(db.String(200))
    company_proof = db.Column(db.String(200))


# =========================
# HR PROFILE
# =========================
class HRProfile(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))

    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))

    phone_number = db.Column(db.String(50))

    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    home_address = db.Column(db.String(200))


# =========================
# JOB TABLE
# =========================
class Job(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Recruiter who posted job
    company_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # =========================
    # JOB INFORMATION
    # =========================
    field = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    location = db.Column(db.String(200))
    salary = db.Column(db.String(100))

    # JOB MEDIA
    poster = db.Column(db.String(200))

    # JOB EXPIRATION
    expiration_date = db.Column(db.Date)

    # =========================
    # RELATIONSHIPS
    # =========================
    applications = db.relationship(
        "Application",
        backref="job",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================
# APPLICATION TABLE
# =========================
class Application(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    applicant_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))

    # =========================
    # APPLICANT SUBMISSION
    # =========================
    resume = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)

    # =========================
    # RECRUITER / HR REVIEW
    # =========================
    status = db.Column(db.String(50), default="Pending")

    recruiter_remarks = db.Column(db.Text)

    interview_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # =========================
    # RELATIONSHIPS
    # =========================
    hr_feedbacks = db.relationship(
        "HRFeedback",
        backref="application",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================
# HR FEEDBACK TABLE
# (one row per HR per application)
# =========================
class HRFeedback(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    hr_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    feedback = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =========================
# JOB IMAGE
# =========================
class JobImage(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    image_path = db.Column(db.String(200))
    job = db.relationship("Job", backref="images")  