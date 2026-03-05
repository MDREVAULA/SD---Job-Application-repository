from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database
db.init_app(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


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
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin account created successfully!")
            print("Username: admin")
            print("Password: admin123")

    app.run(debug=True)
