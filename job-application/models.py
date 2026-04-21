from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import pytz

ph_tz = pytz.timezone("Asia/Manila")

def get_ph_time():
    return datetime.now(ph_tz)
db = SQLAlchemy()


# =========================
# USER TABLE
# =========================
class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)  # nullable for Google users

    profile_completed = db.Column(db.Boolean, default=False, nullable=False, server_default='0')

    role = db.Column(db.String(50), nullable=False)

    # Google OAuth
    google_id = db.Column(db.String(200), unique=True, nullable=True)

    # Temporary password system
    must_change_password = db.Column(db.Boolean, default=False)

    # Verification system (recruiters only after profile completion)
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default="Pending")
    verification_remarks = db.Column(db.Text)

    # Ban system (replaces applicant rejection)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text, nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)
    ban_until = db.Column(db.DateTime, nullable=True)

    # HR created by recruiter
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Forgot password
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    profile_picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    # Soft-delete support (for undo on HR accounts)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

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

    headline = db.Column(db.String(200))
    bio = db.Column(db.Text)
    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))
    portfolio = db.Column(db.String(200))

    # DOCUMENT UPLOADS
    resume_file      = db.Column(db.String(200))
    portfolio_file   = db.Column(db.String(200))
    certificate_files = db.Column(db.Text)  # JSON array

    # RELATIONSHIPS
    work_experiences = db.relationship(
        "WorkExperience", backref="profile",
        lazy=True, cascade="all, delete-orphan"
    )
    educations = db.relationship(
        "ApplicantEducation", backref="profile",
        lazy=True, cascade="all, delete-orphan"
    )
    skills = db.relationship(
        "Skill", backref="profile",
        lazy=True, cascade="all, delete-orphan"
    )
    projects = db.relationship(
        "Project", backref="profile",
        lazy=True, cascade="all, delete-orphan"
    )
    certifications = db.relationship(
        "Certification", backref="profile",
        lazy=True, cascade="all, delete-orphan"
    )


# =========================
# WORK EXPERIENCE  (applicant only)
# =========================
class WorkExperience(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("applicant_profile.id"), nullable=False
    )

    job_title = db.Column(db.String(200))
    company = db.Column(db.String(200))
    location = db.Column(db.String(200))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

# =========================
# APPLICANT EDUCATION  (applicant-only)
# =========================
class ApplicantEducation(db.Model):
    """Education entries that belong exclusively to an ApplicantProfile."""

    __tablename__ = "applicant_education"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("applicant_profile.id"), nullable=False
    )

    school = db.Column(db.String(200))
    degree = db.Column(db.String(200))
    field_of_study = db.Column(db.String(200))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

# Keep the old name as an alias so existing import statements still work
Education = ApplicantEducation


# =========================
# RECRUITER EDUCATION  (recruiter-only)
# =========================
class RecruiterEducation(db.Model):
    """Education entries that belong exclusively to a RecruiterProfile."""

    __tablename__ = "recruiter_education"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("recruiter_profile.id"), nullable=False
    )

    school = db.Column(db.String(200))
    degree = db.Column(db.String(200))
    field_of_study = db.Column(db.String(200))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

# =========================
# HR EDUCATION  (hr-only)
# =========================
class HREducation(db.Model):
    """Education entries that belong exclusively to an HRProfile."""

    __tablename__ = "hr_education"

    id             = db.Column(db.Integer, primary_key=True)
    profile_id     = db.Column(db.Integer, db.ForeignKey("hr_profile.id"), nullable=False)
    school         = db.Column(db.String(200))
    degree         = db.Column(db.String(200))
    field_of_study = db.Column(db.String(200))
    start_date     = db.Column(db.String(50))
    end_date       = db.Column(db.String(50))
    is_current     = db.Column(db.Boolean, default=False)
    description    = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=get_ph_time)


# =========================
# SKILL  (applicant only)
# =========================
class Skill(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("applicant_profile.id"), nullable=False
    )

    name = db.Column(db.String(100))
    level = db.Column(db.String(50))  # Beginner, Intermediate, Advanced, Expert
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

# =========================
# PROJECT  (applicant only)
# =========================
class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("applicant_profile.id"), nullable=False
    )

    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    url = db.Column(db.String(200))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

# =========================
# CERTIFICATION  (applicant only)
# =========================
class Certification(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("applicant_profile.id"), nullable=False
    )

    name = db.Column(db.String(200))
    issuer = db.Column(db.String(200))
    issue_date = db.Column(db.String(50))
    expiry_date = db.Column(db.String(50))
    credential_url = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

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

    headline = db.Column(db.String(200))
    bio      = db.Column(db.Text)

    linkedin  = db.Column(db.String(200))
    github    = db.Column(db.String(200))
    portfolio = db.Column(db.String(200))

    company_name = db.Column(db.String(200))
    company_industry = db.Column(db.String(200))
    company_description = db.Column(db.Text)

    company_address = db.Column(db.String(200))

    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    office_address = db.Column(db.String(200))

    company_email_domain = db.Column(db.String(100))

    company_logo = db.Column(db.String(200))
    company_proof = db.Column(db.String(200))

    # Track whether profile has been submitted for verification
    submitted_for_review = db.Column(db.Boolean, default=False)

    # RELATIONSHIP — recruiter-specific education entries
    educations = db.relationship(
        "RecruiterEducation", backref="recruiter_profile",
        lazy=True, cascade="all, delete-orphan"
    )


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

    headline = db.Column(db.String(200))
    bio = db.Column(db.Text)

    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))
    portfolio = db.Column(db.String(200))

    educations = db.relationship(
        "HREducation", backref="hr_profile",
        lazy=True, cascade="all, delete-orphan"
    )


# =========================
# JOB TABLE
# =========================
class Job(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Recruiter who posted job
    company_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    arrangement = db.Column(db.String(200))

    experience_level  = db.Column(db.String(100))
    years_exp         = db.Column(db.String(100))
    education         = db.Column(db.String(200))
    required_skills   = db.Column(db.Text)
    preferred_skills  = db.Column(db.Text)
    languages         = db.Column(db.String(200))
    requirements_notes = db.Column(db.Text)
    field = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    location = db.Column(db.String(200))
    salary = db.Column(db.String(100))
    currency = db.Column(db.String(10), default='PHP')
    is_taken_down   = db.Column(db.Boolean, default=False)
    takedown_reason = db.Column(db.Text, nullable=True)
    takedown_until  = db.Column(db.DateTime, nullable=True)  # None = permanent
    taken_down_at   = db.Column(db.DateTime, nullable=True)

    poster = db.Column(db.String(200))

    expiration_date = db.Column(db.Date)

    created_at         = db.Column(db.DateTime, default=get_ph_time)
    updated_at         = db.Column(db.DateTime, default=get_ph_time, onupdate=get_ph_time)
    max_applications   = db.Column(db.Integer,  nullable=True)
    allow_applications = db.Column(db.Boolean,  default=True)
    cover_photo        = db.Column(db.String(200), nullable=True)

    # Company-level override text (per job)
    about_company  = db.Column(db.Text, nullable=True)
    why_join_us    = db.Column(db.Text, nullable=True)   # JSON array of bullet strings
    company_values = db.Column(db.Text, nullable=True)   # JSON array of {title, description}

    applications = db.relationship(
        "Application",
        backref="job",
        lazy=True,
        cascade="all, delete-orphan"
    )

    saved_by_users = db.relationship(
        "SavedJob",
        lazy=True,
        cascade="all, delete-orphan",
        overlaps="job,saved_by"
    )

    # FIX: use back_populates to properly link with JobTeamMember.job
    team_members = db.relationship(
        'JobTeamMember',
        lazy=True,
        cascade='all, delete-orphan',
        back_populates='job'
    )


# =========================
# APPLICATION TABLE
# =========================
class Application(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    applicant_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))

    resume = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)

    status = db.Column(db.String(50), default="Pending")

    recruiter_remarks = db.Column(db.Text)

    interview_date = db.Column(db.DateTime, nullable=True)
    meeting_type   = db.Column(db.String(50),  nullable=True)
    meeting_link   = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

    hr_feedbacks = db.relationship(
        "HRFeedback",
        backref="application",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================
# EMPLOYMENT REQUIREMENT TABLE
# Recruiter defines which documents the applicant must submit
# =========================
class EmploymentRequirement(db.Model):
    """Documents/requirements the recruiter defines per job for onboarding."""
    __tablename__ = 'employment_requirement'

    id          = db.Column(db.Integer, primary_key=True)
    job_id      = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)   # e.g. "Government-issued ID"
    description = db.Column(db.Text, nullable=True)           # optional instructions
    is_required = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=get_ph_time)
 
    job = db.relationship('Job', backref=db.backref('employment_requirements', cascade='all, delete-orphan', lazy=True))


# =========================
# EMPLOYMENT SUBMISSION TABLE
# Applicant submits one file per requirement
# =========================
class EmploymentSubmission(db.Model):
    """One submitted file from the applicant for an EmploymentRequirement."""
    __tablename__ = 'employment_submission'

    id             = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id', ondelete='CASCADE'), nullable=False)
    requirement_id = db.Column(db.Integer, db.ForeignKey('employment_requirement.id', ondelete='CASCADE'), nullable=False)
    file_path      = db.Column(db.String(300), nullable=True)   # uploaded file path
    notes          = db.Column(db.Text, nullable=True)           # optional note from applicant
    submitted_at   = db.Column(db.DateTime, default=get_ph_time)
    updated_at     = db.Column(db.DateTime, default=get_ph_time, onupdate=get_ph_time)
 
    application = db.relationship('Application', backref=db.backref('employment_submissions', cascade='all, delete-orphan', lazy=True))
    requirement = db.relationship('EmploymentRequirement', backref=db.backref('submissions', lazy=True))


# =========================
# EMPLOYEE TABLE
# Created when recruiter/HR confirms employment after reviewing submissions
# =========================
class Employee(db.Model):
    """
    Marks an applicant as a confirmed employee for a specific job.
    Created only after recruiter/HR reviews and confirms all submissions.
    Once created, application status can no longer be changed.
    """
    __tablename__ = 'employee'

    id             = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id', ondelete='CASCADE'), nullable=False, unique=True)
    job_id         = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='SET NULL'), nullable=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # the applicant
    confirmed_by   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # recruiter or HR who confirmed
    start_date     = db.Column(db.Date, nullable=True)
    job_title      = db.Column(db.String(200), nullable=True)  # snapshot of the job title at confirmation
    company_name   = db.Column(db.String(200), nullable=True)  # snapshot of company name

    # Employment status: active | resigned | fired
    employment_status = db.Column(db.String(20), default='active', nullable=False)
    ended_at          = db.Column(db.DateTime, nullable=True)
    end_reason        = db.Column(db.Text, nullable=True)  # reason for firing or resignation note
 
    confirmed_at = db.Column(db.DateTime, default=get_ph_time)
 
    # Relationships
    application  = db.relationship('Application', backref=db.backref('employee_record', uselist=False))
    job          = db.relationship('Job', foreign_keys=[job_id], backref=db.backref('employees', lazy=True))
    user         = db.relationship('User', foreign_keys=[user_id], backref=db.backref('employment_records', lazy=True))
    confirmer    = db.relationship('User', foreign_keys=[confirmed_by])


# =========================
# EMPLOYMENT SUBMISSION STATUS (per-application onboarding state)
# Tracks the overall onboarding review state for an application
# =========================
class EmploymentOnboarding(db.Model):
    """
    Tracks the overall onboarding state for an accepted application.
    States:
      pending_submission  – applicant hasn't submitted requirements yet
      submitted           – applicant submitted, waiting for review
      needs_revision      – reviewer sent back for corrections
      confirmed           – recruiter/HR confirmed, Employee record created
    """
    __tablename__ = 'employment_onboarding'

    id             = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id', ondelete='CASCADE'), nullable=False, unique=True)
    status         = db.Column(db.String(30), default='pending_submission', nullable=False)
    reviewer_note  = db.Column(db.Text, nullable=True)   # note when sending back for revision
    submitted_at   = db.Column(db.DateTime, nullable=True)
    reviewed_at    = db.Column(db.DateTime, nullable=True)
    created_at     = db.Column(db.DateTime, default=get_ph_time)
 
    application = db.relationship('Application', backref=db.backref('onboarding', uselist=False))


# =========================
# HR TEAM MEMBERS
# =========================
class JobTeamMember(db.Model):
    __tablename__ = 'job_team_member'

    id     = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    hr_id  = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    added_at = db.Column(db.DateTime, default=get_ph_time)

    __table_args__ = (
        db.UniqueConstraint('job_id', 'hr_id', name='unique_job_team_member'),
    )

    hr  = db.relationship('User', foreign_keys=[hr_id])
    # FIX: use back_populates to properly link with Job.team_members
    job = db.relationship('Job', foreign_keys=[job_id], back_populates='team_members')


# =========================
# SAVED JOBS TABLE
# =========================
class SavedJob(db.Model):
    __tablename__ = 'saved_job'

    id           = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    job_id       = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    created_at   = db.Column(db.DateTime, default=get_ph_time)

    __table_args__ = (
        db.UniqueConstraint('applicant_id', 'job_id', name='unique_saved_job'),
    )

    applicant = db.relationship('User', foreign_keys=[applicant_id], backref='saved_jobs')
    job       = db.relationship('Job', foreign_keys=[job_id], backref='saved_by', overlaps="saved_by_users")


# =========================
# FOLLOW TABLE
# =========================
class Follow(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

    __table_args__ = (
        db.UniqueConstraint("follower_id", "followed_id", name="unique_follow"),
    )

    follower = db.relationship("User", foreign_keys=[follower_id], backref="following")
    followed = db.relationship("User", foreign_keys=[followed_id], backref="followers")


# =========================
# MESSAGE TABLE
# =========================
class Message(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    sender_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    body = db.Column(db.Text, nullable=False)

    is_read = db.Column(db.Boolean, default=False)
    edited  = db.Column(db.Boolean, default=False)

    reply_to_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=True)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)

    sender   = db.relationship("User", foreign_keys=[sender_id],   backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")

    reply_to = db.relationship(
        "Message",
        foreign_keys=[reply_to_id],
        remote_side="Message.id",
        backref="replies"
    )


# =========================
# MESSAGE REACTION TABLE
# =========================
class MessageReaction(db.Model):
    __tablename__ = "message_reaction"

    id         = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id", ondelete="CASCADE"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reaction   = db.Column(db.String(20), nullable=False)  # like | heart | haha | wow | sad | angry
    created_at = db.Column(db.DateTime, default=get_ph_time)
    __table_args__ = (
        db.UniqueConstraint("message_id", "user_id", name="unique_message_reaction"),
    )

    message = db.relationship("Message", backref=db.backref("reactions", cascade="all, delete-orphan"))
    user    = db.relationship("User", backref="message_reactions")


# =========================
# HR FEEDBACK TABLE
# =========================
class HRFeedback(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    hr_id          = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    feedback = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=get_ph_time)
    updated_at = db.Column(db.DateTime, default=get_ph_time, onupdate=get_ph_time)


# =========================
# RECRUITER NOTIFICATION TABLE
# =========================
class RecruiterNotification(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type         = db.Column(db.String(50), nullable=False)
    message      = db.Column(db.Text, nullable=False)
    is_read      = db.Column(db.Boolean, default=False)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=True)
    job_id       = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    created_at   = db.Column(db.DateTime, default=get_ph_time)

    recruiter   = db.relationship("User", foreign_keys=[recruiter_id], backref="notifications")
    application = db.relationship("Application", foreign_keys=[application_id])


# =========================
# HR NOTIFICATION TABLE
# =========================
class HRNotification(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    hr_id          = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type           = db.Column(db.String(50), nullable=False)
    message        = db.Column(db.Text, nullable=False)
    is_read        = db.Column(db.Boolean, default=False)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=True)
    job_id         = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    created_at     = db.Column(db.DateTime, default=get_ph_time)

    hr          = db.relationship("User", foreign_keys=[hr_id], backref="hr_notifications")
    application = db.relationship("Application", foreign_keys=[application_id])


# =========================
# APPLICANT NOTIFICATION TABLE
# =========================
class ApplicantNotification(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    applicant_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type           = db.Column(db.String(50), nullable=False)
    message        = db.Column(db.Text, nullable=False)
    is_read        = db.Column(db.Boolean, default=False)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=True)
    job_id         = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    created_at     = db.Column(db.DateTime, default=get_ph_time)

    applicant   = db.relationship("User", foreign_keys=[applicant_id], backref="applicant_notifications")
    application = db.relationship("Application", foreign_keys=[application_id])


# =========================
# ADMIN NOTIFICATION TABLE
# =========================
class AdminNotification(db.Model):
    __tablename__ = 'admin_notifications'

    id         = db.Column(db.Integer, primary_key=True)
    type       = db.Column(db.String(50), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=get_ph_time)
    def to_dict(self):
        now = get_ph_time()
        diff = now - self.created_at
        if diff.seconds < 60:
            time_str = "just now"
        elif diff.seconds < 3600:
            time_str = f"{diff.seconds // 60}m ago"
        elif diff.days == 0:
            time_str = f"{diff.seconds // 3600}h ago"
        else:
            time_str = self.created_at.strftime("%b %d, %Y")
        return {
            'id':         self.id,
            'type':       self.type,
            'message':    self.message,
            'is_read':    self.is_read,
            'user_id':    self.user_id,
            'created_at': time_str,
        }


# =========================
# JOB IMAGE
# =========================
class JobImage(db.Model):

    id         = db.Column(db.Integer, primary_key=True)
    job_id     = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    image_path = db.Column(db.String(200))
    job        = db.relationship("Job", backref="images")


# =========================
# USER SETTINGS TABLE
# =========================
class UserSettings(db.Model):
    """Stores per-user settings (privacy, notifications, appearance, etc.)"""
    __tablename__ = 'user_settings'

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    # Privacy
    show_name             = db.Column(db.String(20), default='everyone')
    show_profile          = db.Column(db.String(20), default='everyone')
    profile_audience_json = db.Column(db.Text, default='["recruiter","hr","mutual"]')

    show_follow_list  = db.Column(db.String(10), default='yes')
    show_follow_count = db.Column(db.String(10), default='yes')

    who_can_message = db.Column(db.String(20), default='all')

    # Notifications
    notif_app_status = db.Column(db.Boolean, default=True)
    notif_messages   = db.Column(db.Boolean, default=True)
    notif_followers  = db.Column(db.Boolean, default=True)
    notif_jobs       = db.Column(db.Boolean, default=False)

    # Appearance
    theme   = db.Column(db.String(10),  default='light')
    density = db.Column(db.String(15),  default='comfortable')

    # Language
    language = db.Column(db.String(10),  default='en')
    timezone = db.Column(db.String(50),  default='Asia/Manila')

    # Two-factor (security section)
    two_factor = db.Column(db.Boolean, default=False)
    two_factor_code   = db.Column(db.String(6),  nullable=True)
    two_factor_expiry = db.Column(db.DateTime,   nullable=True)

    user = db.relationship('User', backref=db.backref('settings', uselist=False))

    def __repr__(self):
        return f'<UserSettings user_id={self.user_id}>'


# =========================
# USER BLOCK TABLE
# =========================
class UserBlock(db.Model):
    __tablename__ = 'user_block'

    id         = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_ph_time)
    __table_args__ = (
        db.UniqueConstraint('blocker_id', 'blocked_id', name='unique_user_block'),
    )

    blocker = db.relationship('User', foreign_keys=[blocker_id], backref='blocked_users')
    blocked = db.relationship('User', foreign_keys=[blocked_id], backref='blocked_by_users')


# =========================
# USER REPORT TABLE
# =========================
class UserReport(db.Model):
    __tablename__ = 'user_report'

    id          = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    reason      = db.Column(db.String(100), nullable=False)   # e.g. "Spam", "Harassment", etc.
    description = db.Column(db.Text, nullable=True)
    evidence_files = db.Column(db.Text, nullable=True)

    # Admin handling
    status      = db.Column(db.String(20), default='pending')  # pending | reviewed | dismissed
    admin_notes = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    created_at  = db.Column(db.DateTime, default=get_ph_time)

    __table_args__ = (
        db.UniqueConstraint('reporter_id', 'reported_id', name='unique_user_report'),
    )

    reporter          = db.relationship('User', foreign_keys=[reporter_id], backref='reports_made')
    reported          = db.relationship('User', foreign_keys=[reported_id], backref='reports_received')
    reviewed_by_admin = db.relationship('User', foreign_keys=[reviewed_by])

    def to_dict(self):
        return {
            'id':          self.id,
            'reporter':    self.reporter.username if self.reporter else '—',
            'reported':    self.reported.username if self.reported else '—',
            'reported_id': self.reported_id,
            'reason':      self.reason,
            'description': self.description or '',
            'status':      self.status,
            'created_at':  self.created_at.strftime('%b %d, %Y %H:%M') if self.created_at else '',
        }


# =========================
# RESIGNATION REQUEST TABLE
# =========================
class ResignationRequest(db.Model):
    __tablename__ = 'resignation_request'

    id                = db.Column(db.Integer, primary_key=True)
    employee_id       = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, unique=True)
    applicant_id      = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    job_id            = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='SET NULL'), nullable=True)

    reason            = db.Column(db.Text, nullable=False)
    intended_last_day = db.Column(db.Date, nullable=False)
    letter_file       = db.Column(db.String(300), nullable=True)

    # pending | revision_requested | approved | rejected
    status            = db.Column(db.String(30), default='pending', nullable=False)

    reviewer_note     = db.Column(db.Text, nullable=True)
    reviewed_by       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at       = db.Column(db.DateTime, nullable=True)
 
    submitted_at      = db.Column(db.DateTime, default=get_ph_time)
    updated_at        = db.Column(db.DateTime, default=get_ph_time, onupdate=get_ph_time)
 
    employee  = db.relationship('Employee', backref=db.backref('resignation_request', uselist=False))
    applicant = db.relationship('User', foreign_keys=[applicant_id])
    reviewer  = db.relationship('User', foreign_keys=[reviewed_by])
    job       = db.relationship('Job', foreign_keys=[job_id])


def is_blocked_between(user_a_id, user_b_id):
    """True if either user has blocked the other."""
    from sqlalchemy import or_, and_
    return bool(UserBlock.query.filter(
        or_(
            and_(UserBlock.blocker_id == user_a_id, UserBlock.blocked_id == user_b_id),
            and_(UserBlock.blocker_id == user_b_id, UserBlock.blocked_id == user_a_id),
        )
    ).first())