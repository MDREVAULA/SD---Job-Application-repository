from flask import Flask
from config import Config
from models import db, User, RecruiterProfile
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash
from datetime import datetime
from flask_migrate import Migrate
import os
import pymysql
import secrets
import logging
import json

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
log.setLevel(logging.INFO)
log.addFilter(NoStaticFilter())

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Initialize Database
db.init_app(app)
migrate = Migrate(app, db)

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

# ============================================================
# JINJA2 FILTER — resolve RecruiterProfile from a user ID
# Usage in templates: {{ job.company_id | get_recruiter_profile }}
# ============================================================
@app.template_filter('get_recruiter_profile')
def get_recruiter_profile(user_id):
    if not user_id:
        return None
    return RecruiterProfile.query.filter_by(user_id=user_id).first()

# ============================================================
# CONTEXT PROCESSOR — make now() available in all templates
# Usage in templates: {{ now() }}
# ============================================================
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# Register Blueprints
from routes.auth import auth_bp
from routes.applicant import applicant_bp
from routes.recruiter import recruiter_bp
from routes.hr import hr_bp
from routes.admin import admin_bp
from routes.chat import chat_bp
from routes.profile_view import profile_view_bp
from routes.settings import settings_bp

app.register_blueprint(auth_bp)
app.register_blueprint(applicant_bp)
app.register_blueprint(recruiter_bp)
app.register_blueprint(hr_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(profile_view_bp)
app.register_blueprint(settings_bp)


@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value) if value else []
    except:
        return []

# Run App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # ONLY run once (avoid duplicate execution from reloader)
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":

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

            # GENERATE ADMIN TOKEN LINK (per session)
            admin_token = secrets.token_urlsafe(32)
            app.config["ADMIN_TOKEN"] = admin_token

            # CLEAN OUTPUT ORDER
            print("\n" + "=" * 50)
            print("Flask App URL:")
            print("http://127.0.0.1:5000/")
            print("\nADMIN LOGIN URL (this session only):")
            print(f"http://127.0.0.1:5000/admin/login/{admin_token}")
            print("=" * 50 + "\n")

    app.run(debug=True)