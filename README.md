# 💼 Welcome to HireBon – Where OPPORTUNITY Meets the Right JOB

---

## Setup Guide
A Flask-based job portal web application with Google OAuth, email verification, and role-based access (Applicant, Recruiter, HR, Admin).

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install Visual Studio Code](#1-install-visual-studio-code)
3. [Install Python](#2-install-python)
4. [Install XAMPP](#3-install-xampp)
5. [Clone / Download the Project](#4-clone--download-the-project)
6. [Install Python Dependencies](#5-install-python-dependencies)
7. [Set Up the Database](#6-set-up-the-database)
8. [Configure Google OAuth](#7-configure-google-oauth)
9. [Configure Gmail SMTP](#8-configure-gmail-smtp)
10. [Create the `.env` File](#9-create-the-env-file)
11. [Run the Application](#10-run-the-application)
12. [Default Admin Credentials](#default-admin-credentials)

---

## Prerequisites

Make sure you have the following before starting:

- A Windows PC (this guide is written for Windows)
- An internet connection
- A Google account (for OAuth and Gmail SMTP)

---

## 1. Install Visual Studio Code

1. Go to [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. Click **Download for Windows**
3. Run the installer and follow the prompts
4. During installation, check **"Add to PATH"** and **"Open with Code"** options
5. Once installed, open **VS Code**
6. Install the **Python extension**:
   - Click the Extensions icon on the left sidebar (or press `Ctrl+Shift+X`)
   - Search for `Python` (by Microsoft)
   - Click **Install**

---

## 2. Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.11** or later
3. Run the installer
4. ⚠️ **Important:** Check the box that says **"Add Python to PATH"** before clicking Install
5. Click **Install Now**
6. Verify installation by opening a terminal (`Ctrl+`` in VS Code) and running:

```bash
python --version
```

You should see something like `Python 3.11.x`.

---

## 3. Install XAMPP

XAMPP provides the MySQL database server the app uses.

1. Go to [https://www.apachefriends.org/](https://www.apachefriends.org/)
2. Download the **Windows** version
3. Run the installer and follow the prompts (default settings are fine)
4. Once installed, open **XAMPP Control Panel**
5. Click **Start** next to **MySQL** (you don't need Apache for this project)
6. Make sure the MySQL status turns **green**

> The app connects to MySQL using the default credentials: `root` with no password. If you've changed your MySQL root password, update `SQLALCHEMY_DATABASE_URI` in `config.py` accordingly.

---

## 4. Clone / Download the Project

**Option A — Using Git:**

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**Option B — Download ZIP:**

1. Download the project ZIP file
2. Extract it to a folder of your choice
3. Open that folder in VS Code: **File → Open Folder**

---

## 5. Install Python Dependencies

Open the integrated terminal in VS Code (`Ctrl+`` ) and run the following commands one by one:

```bash
pip install flask
pip install flask-sqlalchemy
pip install flask-login
pip install flask-mail
pip install flask-migrate
pip install pymysql
pip install python-dotenv
pip install authlib
pip install werkzeug
pip install requests
```

Or install everything at once if a `requirements.txt` is provided:

```bash
pip install -r requirements.txt
```

---

## 6. Set Up the Database

The app **automatically creates** the `job_portal` database when it runs. You don't need to create it manually.

However, you can verify it in XAMPP:

1. Open your browser and go to [http://localhost/phpmyadmin](http://localhost/phpmyadmin)
2. After running the app for the first time, you should see `job_portal` listed on the left

---

## 7. Configure Google OAuth

Google OAuth allows users to log in with their Google account.

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Create a **New Project** (or select an existing one)
3. In the left menu, go to **APIs & Services → OAuth consent screen**
   - Choose **External**
   - Fill in App name, support email, and developer email
   - Click **Save and Continue** through the rest (defaults are fine for testing)
4. Go to **APIs & Services → Credentials**
5. Click **+ Create Credentials → OAuth 2.0 Client IDs**
6. Set Application type to **Web application**
7. Under **Authorized redirect URIs**, add:
   ```
   http://127.0.0.1:5000/auth/google/callback
   ```
8. Click **Create**
9. Copy your **Client ID** and **Client Secret** — you'll need these in the next step

---

## 8. Configure Gmail SMTP

The app sends verification emails via Gmail.

1. Go to your Google Account: [https://myaccount.google.com/](https://myaccount.google.com/)
2. Navigate to **Security**
3. Enable **2-Step Verification** if not already on
4. Search for **"App Passwords"** in the search bar at the top
5. Select **Mail** as the app and **Windows Computer** as the device
6. Click **Generate**
7. Copy the **16-character app password** — this is your `MAIL_PASSWORD`

> Use your full Gmail address (e.g. `yourname@gmail.com`) as `MAIL_USERNAME`.

---

## 9. Create the `.env` File

In the **root folder** of your project (same level as `app.py`), create a file named `.env`:

1. In VS Code, right-click the project root in the Explorer panel
2. Click **New File** and name it `.env`
3. Paste the following and fill in your values:

```env
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_char_app_password

GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

ADMIN_TOKEN=admintoken123
```

> ⚠️ Never share your `.env` file or push it to GitHub. Add `.env` to your `.gitignore`.

---

## 10. Run the Application

Make sure **XAMPP MySQL is running**, then in the VS Code terminal:

```bash
python app.py
```

You should see output like:

```
==================================================
Flask App URL:
http://127.0.0.1:5000/

ADMIN LOGIN URL (this session only):
http://127.0.0.1:5000/admin/login/<token>
==================================================
```

Open your browser and go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## Default Admin Credentials

On the first run, an admin account is automatically created:

| Field    | Value           |
|----------|-----------------|
| Username | `admin`         |
| Email    | `admin@gmail.com` |
| Password | `admin123`      |

Use the **Admin Login URL** printed in the terminal to access the admin panel.

> 🔒 Change the default admin password after your first login.

---

## Troubleshooting

**MySQL connection error**
- Make sure XAMPP MySQL is running before starting the app

**Google OAuth not working**
- Double-check the redirect URI in Google Console matches exactly: `http://127.0.0.1:5000/auth/google/callback`

**Emails not sending**
- Make sure you used an **App Password**, not your regular Gmail password
- Ensure 2-Step Verification is enabled on your Google account

**`ModuleNotFoundError`**
- Run `pip install <module-name>` for the missing package

---

*Built with Flask, SQLAlchemy, Flask-Mail, Authlib, and ❤️*
