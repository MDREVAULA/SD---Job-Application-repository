from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash
import os
import pymysql
import secrets
import logging

# CREATE DATABASE IF NOT EXISTS
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

# ── Filter out static file requests from logs ──
class NoStaticFilter(logging.Filter):
    def filter(self, record):
        return '/static/' not in record.getMessage()

log = logging.getLogger('werkzeug')
log.addFilter(NoStaticFilter())

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Initialize Database
db.init_app(app)

# Initialize Mail
mail = Mail(app)

# Initialize OAuth
oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

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

        # AUTO-CREATE ADMIN ACCOUNT IF NOT EXISTS
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
            print("=" * 50)
            print("Admin account created!")
            print("Username: admin")
            print("Password: admin123")
            print("=" * 50)

        # Only print admin URL on the reloader process (the real one)
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            admin_token = secrets.token_urlsafe(32)
            app.config["ADMIN_TOKEN"] = admin_token

            print("\n" + "=" * 50)
            print("ADMIN LOGIN URL (this session only):")
            print(f"http://127.0.0.1:5000/admin/login/{admin_token}")
            print("=" * 50 + "\n")

    app.run(debug=True)