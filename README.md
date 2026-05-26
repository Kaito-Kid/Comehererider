# ComeHere Rider (CHR)

A web application and PWA for delivery riders to deliver goods to consumers in remote locations, empowering tricycle drivers under Tricycle Driver Organizations to increase their earnings.

## Project Overview
**Target Audience**: Tricycle Drivers and Regular Consumers
**Payment System**: Cash-based with commission structure

## Key Features
- Real-time order updates and tracking
- Live geolocation of riders (OpenStreetMap)
- Role-based access (Admin, Managers, Riders, Users)
- Responsive, mobile-first design
- Trust-based payment system
- Comprehensive reporting system

## Tech Stack
- **Frontend**: Flask Templates (Jinja), Bootstrap 5, JavaScript
- **Backend**: Python Flask with SQLAlchemy, Flask-Login, Bcrypt
- **Database**: MySQL
- **Deployment**: Docker, Gunicorn

### Setup & Deployment
For detailed setup, installation, and deployment instructions (including Docker and manual setup), please refer to [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md).

Quick Start (Docker):
```bash
docker-compose up -d
```

## Project Structure
```
chr/
├── project/             # Application source code
│   ├── app/
│   │   ├── models/      # Database models
│   │   ├── routes/      # Application routes
│   │   ├── templates/   # Jinja templates
│   │   └── static/      # CSS, JS, images
│   ├── migrations/      # Database migrations
│   ├── .env             # Environment variables
│   ├── requirements.txt # Python dependencies
│   ├── Dockerfile       # Docker configuration
│   └── wsgi.py          # Entry point
├── mounted/             # Persisted data (logs, uploads, db)
│   ├── logs/
│   ├── app/static/uploads/
│   └── instance/
├── docker-compose.yml   # Docker Compose configuration
├── SETUP_INSTRUCTIONS.md # Setup guide
└── README.md            # This file
```
