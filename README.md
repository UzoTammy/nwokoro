# Nwokoro — Personal Portfolio Website

A personal portfolio and productivity web application built with Django.

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript
- **Deployment:** Procfile-ready (Heroku/Railway compatible)
- **Package Manager:** uv

## Features

- User account management
- Achievement tracking
- Financial net worth calculator
- Task/chore management
- Profile management with JSON configuration

## Getting Started

```bash
# Clone the repository
git clone https://github.com/UzoTammy/nwokoro.git
cd nwokoro

# Create VE using uv: Creates a .venv folder for VE
uv venv

# Activate the VE
source .venv/Scripts/activate

# Install dependent packages from pyproject.toml
uv sync

# Run the development server
python manage.py runserver
```

## Author

**Uzo Tammy Nwokoro** — Software Developer & AI Practitioner
[LinkedIn](https://linkedin.com/in/uzonwokoro)

## Installing postgress

#### Step A: Capture a backup on heroku's service

`heroku pg:backups:capture --app your-app-name`

#### Step B: Download the file

This creates a `latest.dump` file in your current folder.

```
heroku pg:backups:download --app your-app-name
```

#### Step C: Restore it locally

Since the file is now on your hard drive, the "pull" can't get stuck anymore.

```
# 0. Terminate active connections (Optional, but prevents "database is being accessed by other users" errors):
psql postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'my_local_db_name';"

# 1. Drop and recreate your local DB to ensure it's empty
dropdb my_local_db_name
createdb my_local_db_name

# 2. Use the native Postgres tool to restore the file
pg_restore --verbose --clean --no-acl --no-owner -h localhost -U your_username -d my_local_db_name latest.dump
```
