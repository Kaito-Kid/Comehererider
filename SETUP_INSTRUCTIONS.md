# ComeHere Rider (CHR) - Setup & Deployment Instructions

This document provides a comprehensive guide for setting up the ComeHere Rider application in both development and production environments. It also outlines potential issues and troubleshooting steps.

## 1. Development Environment Setup

### Prerequisites
- **Python 3.8+**: Ensure Python is installed (`python3 --version`).
- **MySQL Server**: Required for the database (or use SQLite for simple testing).
- **Git**: For version control.

### Step-by-Step Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd chr
    ```

2.  **Create Virtual Environment**
    It is recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate   # Windows
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    - Copy the example environment file:
      ```bash
      cp .env.example .env
      ```
    - **Edit `.env`**:
      - Set `FLASK_ENV=development`.
      - Configure `DATABASE_URI` (e.g., `mysql+pymysql://user:pass@localhost/db_name`).
      - *Note*: If `DATABASE_URI` is not set, the app may default to a local configuration or fail if strict.

5.  **Database Initialization**
    The application is configured to **automatically** check for and create tables on startup. However, you can manually initialize it:
    ```bash
    # Option A: Using Flask-Migrate (Recommended)
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade


    ```

6.  **Run the Server**
    ```bash
    python dev.py
    ```
    - Access the app at `http://localhost:5000`.
    - The server will auto-reload on code changes.

---

## 2. Production Deployment

### Method A: Docker Compose (Recommended)

This is the easiest and most robust way to deploy, as it containerizes both the application and the database.

1.  **Prepare Environment**
    - Ensure `.env` is configured for production:
      - `FLASK_ENV=production`
      - `SECRET_KEY`: **Must** be a long, random string.
      - `MYSQL_PASSWORD`: Use a strong password.
      - `MYSQL_HOST`: Set to the IP/hostname of your external MySQL service.

2.  **Build and Run**
    ```bash
    docker-compose up -d --build
    ```
    - The build is optimized to be fast (no heavy system dependencies).
    - The app will wait for the database to be ready (up to 5 minutes) before starting.

3.  **Manage Containers**
    - **Logs**: `docker-compose logs -f chr`
    - **Stop**: `docker-compose down`
    - **Restart**: `docker-compose restart chr`

### Method B: Manual Deployment (VPS/Server)

1.  **Install System Packages**
    ```bash
    sudo apt-get update
    sudo apt-get install python3-venv python3-dev
    # Note: libmysqlclient-dev is NOT required as we use PyMySQL.
    ```

2.  **Setup Application**
    - Follow the **Development** steps 1-3.
    - Set `FLASK_ENV=production` in `.env`.

3.  **Run with Gunicorn**
    ```bash
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
    ```
    - **Important**: Use a process manager like `systemd` or `supervisor` to keep the application running.

---

## 3. Potential Issues & Troubleshooting

### A. Database Connection
- **Symptom**: Application fails to start, logs show "Database connection failed".
- **Cause**: The database container/service is not running or credentials are wrong.
- **Solution**:
    - The app has built-in **retry logic** (15s interval, 5m timeout). Check logs to see retry attempts.
    - Verify `DATABASE_URI` in `.env`.
    - Ensure the MySQL service is healthy (`docker-compose ps`).

### B. Static Files Not Loading
- **Symptom**: CSS/JS/Images are missing in production.
- **Cause**: Gunicorn is an application server, not a web server. It is not optimized to serve static files.
- **Solution**:
    - **Recommended**: Put **Nginx** in front of Gunicorn to serve `/static` directly.
    - **Alternative**: Use `WhiteNoise` middleware (easier setup, slightly less performant than Nginx).

### C. Permission Errors
- **Symptom**: "Permission denied" errors in logs, or file uploads fail.
- **Cause**: The user running the application (e.g., `www-data` or `app` user) does not have write access to `logs/` or `app/static/uploads/`.
- **Solution**:
    ```bash
    chmod -R 755 mounted/logs mounted/app/static/uploads
    chown -R <user>:<group> .
    ```

### D. Session Issues
- **Symptom**: Users cannot log in or are logged out immediately.
- **Cause**:
    - `SECRET_KEY` changed (invalidates all sessions).
    - `SESSION_COOKIE_SECURE=True` is set, but you are accessing via HTTP (not HTTPS).
- **Solution**:
    - If testing production locally without HTTPS, set `SESSION_COOKIE_SECURE=False` in `.env`.
    - **Always** use HTTPS in real production.

### E. Admin Account Missing
- **Symptom**: Cannot log in as admin.
- **Solution**:
    - The app **automatically** creates/updates the admin account on startup based on `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`.
    - Check logs for "Admin account created successfully" or "Admin account updated".
