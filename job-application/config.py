class Config:
    SECRET_KEY = "supersecretkey"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/job_portal"
    SQLALCHEMY_TRACK_MODIFICATIONS = False