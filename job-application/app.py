from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager
from routes.recruiter import recruiter_bp
from werkzeug.security import generate_password_hash
import os
import pymysql

# ✅ CREATE DATABASE IF NOT EXISTS
connection = pymysql.connect(
    host="localhost",
    user="root",
    password=""
)

cursor = connection.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS job_portal")
connection.close()

app = Flask(__name__)
app.config.from_object(Config)
# ✅ Upload folder configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# Make sure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Database
db.init_app(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Register Blueprints
from routes.auth import auth_bp
from routes.applicant import applicant_bp
from routes.recruiter import recruiter_bp
from routes.hr import hr_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(applicant_bp)
app.register_blueprint(recruiter_bp)
app.register_blueprint(hr_bp)
app.register_blueprint(admin_bp)


# Run App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # ✅ AUTO-CREATE ADMIN ACCOUNT IF NOT EXISTS
        existing_admin = User.query.filter_by(role="admin").first()

        if not existing_admin:
            admin = User(
                username="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin",
                is_verified=True
            )

            db.session.add(admin)
            db.session.commit()

            print("Admin account created successfully!")
            print("Username: admin")
            print("Password: admin123")

    app.run(debug=True)