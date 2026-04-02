# HireBon – Setup Guide

## 1. Requirements

### Install all dependencies:
```bash
pip install flask flask-sqlalchemy flask-login flask-mail flask-migrate authlib pymysql requests werkzeug python-dotenv
```

### Or using requirements.txt:
```bash
pip install -r requirements.txt
```

```
flask
flask-sqlalchemy
flask-login
flask-mail
flask-migrate
authlib
pymysql
requests
werkzeug
python-dotenv
```

---

## 2. Database Setup

1. Make sure **XAMPP** is running with **MySQL** started
2. Open **phpMyAdmin** at `http://localhost/phpmyadmin`
3. The database `job_portal` will be created automatically when you run the app
4. To add the new columns needed for Google login and forgot password, go to the **SQL tab** in phpMyAdmin and run:

```sql
ALTER TABLE user ADD COLUMN google_id VARCHAR(200) UNIQUE NULL;
ALTER TABLE user ADD COLUMN reset_token VARCHAR(100) NULL;
ALTER TABLE user ADD COLUMN reset_token_expiry DATETIME NULL;
ALTER TABLE user MODIFY COLUMN password VARCHAR(200) NULL;
```

---

## 3. Environment Variables Setup

1. Create a `.env` file in the project root (same folder as `app.py`)
2. Paste the following and fill in your own values:

```
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-password
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

3. Create a `.gitignore` file in the project root and paste:

```
.env
__pycache__/
*.pyc
instance/
```

---

## 4. Gmail App Password Setup (for Forgot Password)

This allows the app to automatically send password reset emails.

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Go to **Security** → enable **2-Step Verification** if not yet enabled
3. Search **App Passwords** at the top
4. Type any name (e.g. `Job Portal`) → click **Create**
5. Copy the 16-character password shown
6. Paste it as `MAIL_PASSWORD` in your `.env` file

---

## 5. Google OAuth Setup (Sign in with Google)

### Step 1 — Go to Google Cloud Console
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Sign in with your Google account

### Step 2 — Create a Project
1. Click the project dropdown at the top
2. Click **New Project**
3. Enter any project name (e.g. `Job Portal`) → click **Create**

### Step 3 — Set Up OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** → click **Create**
3. Fill in:
   - App name: anything (e.g. `Job Portal`)
   - User support email: your Gmail
   - Developer contact email: your Gmail
4. Click **Save and Continue** through the remaining steps
5. On the last step click **Back to Dashboard**

### Step 4 — Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. 
