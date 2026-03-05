class Config:
    SECRET_KEY = "supersecretkey"

    DB_NAME = "job_portal"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/job_portal"
    SQLALCHEMY_TRACK_MODIFICATIONS = False