import os

class Config:
    SECRET_KEY = "supersecretkey"

    DB_NAME = "job_portal"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/job_portal"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')