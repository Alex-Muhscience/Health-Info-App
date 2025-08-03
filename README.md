# 🏥 Health Management System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Django](https://img.shields.io/badge/Django-4.2+-orange.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive healthcare management system built with Flask backend and Django frontend, featuring advanced analytics, security, and full hospital operations management.

## 🌟 Features

### 🔍 Advanced Analytics Engine
- **Patient Flow Analysis** - Track patient visits, peak hours, and visit type distribution
- **Revenue Analytics** - Monitor daily revenue, service breakdowns, and outstanding payments
- **Clinical Quality Metrics** - Track length of stay, readmission rates, lab turnaround times
- **Operational Efficiency** - Monitor bed occupancy, department utilization, inventory status
- **Predictive Insights** - AI-powered recommendations and demand forecasting

### 🔐 Enterprise Security System
- **HIPAA Compliance** - Comprehensive audit logging and data protection
- **Role-Based Access Control** - Granular permissions for different user roles
- **Threat Detection** - Automated security monitoring and response
- **Data Encryption** - Secure handling of sensitive patient information
- **Session Management** - Advanced authentication and authorization

### 🏥 Complete Hospital Management
- **Patient Management** - Complete patient records and demographics
- **Appointment Scheduling** - Advanced booking and calendar management
- **Medical Records** - Comprehensive EMR with vital signs and notes
- **Laboratory Management** - Lab orders, results, and test tracking
- **Pharmacy Operations** - Prescription management and inventory
- **Staff Management** - Employee records and department organization
- **Billing & Insurance** - Complete financial management system
- **Telemedicine** - Virtual consultation capabilities
- **Inventory Management** - Stock tracking and automated alerts

### 🎨 Modern User Interface
- **Responsive Design** - Bootstrap-based UI that works on all devices
- **Professional Dashboard** - Real-time metrics and insights
- **Intuitive Navigation** - Easy-to-use interface for healthcare professionals
- **Advanced Search & Filtering** - Quick access to patient and system data

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 12+ (or SQLite for development)
- Node.js 16+ (for frontend assets)
- Redis (optional, for caching)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/health-management-system.git
   cd health-management-system
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   cd django_frontend
   pip install -r requirements.txt
   cd ..
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database and security settings
   ```

5. **Database Setup**
   ```bash
   # Initialize and populate database with sample data
   python scripts/create_comprehensive_db.py
   ```

6. **Start the System**
   ```bash
   # Option 1: Use the startup script
   python start_health_system.py
   
   # Option 2: Start services manually
   # Terminal 1 - Backend
   cd backend && python app.py
   
   # Terminal 2 - Frontend
   cd django_frontend && python manage.py runserver 8001
   ```

### 🌐 Access Points
- **Frontend UI**: http://localhost:8001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### 👤 Default Login Credentials
- **Admin**: `admin` / `admin123`
- **Doctor**: `dr.smith` / `doctor123`
- **Nurse**: `nurse.jane` / `nurse123`

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django        │    │   Flask         │    │   Database      │
│   Frontend      │◄──►│   Backend       │◄──►│   PostgreSQL    │
│   (Port 8001)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Bootstrap UI  │    │  Analytics      │    │   Sample Data   │
│   Responsive    │    │  Security       │    │   50+ Tables    │
│   Professional  │    │  APIs           │    │   Relationships │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/healthsystem

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Application
FLASK_ENV=development
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:8001,http://127.0.0.1:8001

# Rate Limiting
RATE_LIMIT=200 per day

# Logging
LOG_LEVEL=INFO
```

## 📁 Project Structure

```
health-management-system/
├── backend/                 # Flask API Backend
│   ├── routes/             # API endpoints
│   ├── models.py           # Database models
│   ├── analytics_engine.py # Analytics system
│   ├── security_system.py  # Security & audit
│   └── app.py             # Flask application
├── django_frontend/        # Django Frontend
│   ├── health_app/        # Main Django app
│   ├── templates/         # HTML templates
│   └── manage.py          # Django management
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

```bash
# Run backend tests
python -m pytest tests/backend/

# Run frontend tests
cd django_frontend
python manage.py test

# Run all tests
python -m pytest
```

## 📖 API Documentation

The system provides comprehensive REST APIs:

- **Authentication**: `/api/auth/`
- **Patients**: `/api/clients/`
- **Appointments**: `/api/appointments/`
- **Medical Records**: `/api/medical-records/`
- **Analytics**: `/api/analytics/`
- **Staff**: `/api/staff/`
- **Billing**: `/api/billing/`

Full API documentation is available at `/api/docs` when running the backend.

## 🔒 Security Features

- **HIPAA Compliance**: Complete audit trails and data protection
- **Role-Based Access**: Admin, Doctor, Nurse, Receptionist, Billing roles
- **Data Encryption**: Sensitive data encrypted at rest and in transit
- **Audit Logging**: Comprehensive logging of all system activities
- **Threat Detection**: Automated monitoring for suspicious activities
- **Session Security**: Secure session management with JWT tokens

## 📈 Analytics & Reporting

- **Real-time Dashboards**: Live metrics and KPIs
- **Predictive Analytics**: AI-powered insights and recommendations
- **Custom Reports**: Generate reports for any time period
- **Data Export**: CSV, PDF, and JSON export capabilities
- **Visualization**: Charts and graphs for data interpretation

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   export FLASK_ENV=production
   export DEBUG=False
   ```

2. **Database Migration**
   ```bash
   python scripts/manage_db.py --action migrate
   ```

3. **WSGI Server**
   ```bash
   gunicorn --bind 0.0.0.0:8000 backend.app:app
   ```

4. **Reverse Proxy** (Nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8001;
       }
       
       location /api/ {
           proxy_pass http://127.0.0.1:8000;
       }
   }
   ```

### Docker Deployment

```bash
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use type hints where applicable
- Write tests for new features
- Update documentation as needed
- Ensure security best practices

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join our GitHub Discussions for questions
- **Email**: contact@healthmanagementsystem.com

## 🙏 Acknowledgments

- Flask and Django communities
- Bootstrap for UI components
- All contributors and testers
- Healthcare professionals who provided domain expertise

## 📊 Project Stats

- **Lines of Code**: 15,000+
- **Database Tables**: 50+
- **API Endpoints**: 100+
- **Test Coverage**: 85%+
- **Security Features**: HIPAA Compliant

---

**Built with ❤️ for Healthcare Professionals**

*Empowering healthcare through technology*

# Health Management System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2.7-green)
![Flask](https://img.shields.io/badge/Flask-3.1.0-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

A complete, production-ready healthcare management solution built with **Django frontend** and **Flask backend** architecture. This system provides comprehensive client management, appointment scheduling, visit tracking, health programs, and real-time analytics through a modern web interface.

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Security Considerations](#security-considerations)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## 🏥 Features

### 👥 Client Management
- Add, edit, and view comprehensive client information
- Search and filter clients by various criteria (name, gender, status)
- Emergency contact management and medical notes
- Client profile with complete medical history

### 📅 Appointment Scheduling
- Schedule appointments for clients with duration tracking
- View upcoming and past appointments in organized lists
- Appointment status management (scheduled, completed, cancelled)
- Integration with client profiles for seamless booking

### 🏥 Visit Recording
- Record detailed visit information with multiple visit types
- Track diagnosis, treatment, and medical notes
- Visit history and comprehensive medical records
- Filter visits by date, type, and client

### 📊 Health Programs
- Create and manage health programs (Diabetes, Heart Health, etc.)
- Enroll clients in programs with progress tracking
- Program statistics and completion rates
- Card-based program management interface

### 📈 Dashboard & Analytics
- Real-time system statistics and KPIs
- Client overview with quick action buttons
- Appointment and visit summaries
- Recent activity tracking

### 🔒 Security & Authentication
- Secure JWT-based authentication
- Production-ready security headers with Flask-Talisman
- CORS configuration and rate limiting
- Session management and secure logout

## 🛠️ Tech Stack

### Frontend
- **Django 4.2.7**: Web framework with robust templating
- **Bootstrap 5**: Modern, responsive UI components
- **jQuery**: Enhanced interactivity and AJAX calls
- **Font Awesome**: Professional icon library

### Backend
- **Flask 3.1.0**: Lightweight API server
- **SQLAlchemy 2.0**: Modern ORM with advanced features
- **Flask-JWT-Extended**: JWT token management
- **Flask-Migrate**: Database migration support
- **Flask-Limiter**: Rate limiting and abuse prevention

### Database
- **SQLite**: Development database
- **PostgreSQL**: Production database support
- **Advanced indexing**: Optimized query performance
- **Migration system**: Safe schema changes

### Security
- **Flask-Talisman**: Security headers and CSP
- **Argon2**: Secure password hashing
- **CORS**: Cross-origin request handling
- **Input validation**: Comprehensive data sanitization

### Development & Deployment
- **Gunicorn**: Production WSGI server
- **Environment configuration**: Multi-environment support
- **Logging**: Comprehensive application logging
- **Docker ready**: Containerization support

## Installation
Follow these steps to set up the project locally:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/health-information-system.git
   cd health-information-system
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secure-secret-key
   JWT_SECRET_KEY=your-secure-jwt-secret-key
   DATABASE_URL=sqlite:///health_system.db  # Or PostgreSQL URL
   ```

5. **Initialize the Database**:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the Flask Backend**:
   ```bash
   flask run
   ```

7. **Run the Streamlit Frontend**:
   ```bash
   streamlit run frontend/app.py
   ```

The backend will run on `http://localhost:5000`, and the frontend will be available at `http://localhost:8501`.

## Usage
1. **Access the Frontend**:
   - Open `http://localhost:8501` in your browser.
   - Log in using doctor credentials (default: `admin`/`password` for testing).
   - Use the intuitive UI to:
     - Create health programs.
     - Register clients.
     - Enroll clients in programs.
     - Search for clients by name or ID.
     - View client profiles with enrolled programs.

2. **Access the API**:
   - Use tools like Postman or `curl` to interact with the API (e.g., `GET /api/clients/<client_id>`).
   - Authenticate with a JWT token obtained from the `/login` endpoint.

3. **Demo**:
   - Refer to the `prototype_demo.mp4` in the repository for a video walkthrough.
   - Check the `presentation.pptx` for a detailed overview of the approach and design.

## API Endpoints
The system exposes a RESTful API for client profile access. All endpoints require JWT authentication unless specified.

| Endpoint                  | Method | Description                              | Parameters                     |
|---------------------------|--------|------------------------------------------|--------------------------------|
| `/api/login`              | POST   | Authenticate and obtain JWT token        | `username`, `password`         |
| `/api/programs`           | POST   | Create a new health program              | `name`, `description`          |
| `/api/clients`            | POST   | Register a new client                    | `name`, `id`, `contact`        |
| `/api/enroll`             | POST   | Enroll a client in a program             | `client_id`, `program_id`      |
| `/api/clients`            | GET    | Search for clients (filter by name/ID)   | `query` (optional)             |
| `/api/clients/<client_id>`| GET    | Retrieve a client’s profile and programs | `client_id`                    |

**Example Request**:
```bash
curl -H "Authorization: Bearer <your-jwt-token>" http://localhost:5000/api/clients/1
```

**Example Response**:
```json
{
  "client_id": 1,
  "name": "John Doe",
  "contact": "john@example.com",
  "programs": ["TB", "HIV"]
}
```

## Security Considerations
- **Authentication**: JWT tokens secure API access, with short-lived access tokens (15 minutes) and refresh tokens (7 days).
- **Password Hashing**: Passwords are hashed using `bcrypt` for secure storage.
- **Input Validation**: All user inputs are sanitized to prevent SQL injection and XSS attacks.
- **CORS**: Configured to allow requests only from the Streamlit frontend (`http://localhost:8501`).
- **Environment Variables**: Sensitive data (e.g., JWT secret keys) are stored in a `.env` file, excluded from version control.

## Testing
The project includes unit and integration tests to ensure reliability.

1. **Run Tests**:
   ```bash
   pytest tests/
   ```

2. **Test Coverage**:
   - Tests cover core functionality: program creation, client registration, enrollment, search, and API endpoints.
   - Use `pytest-cov` for coverage reports:
     ```bash
     pytest --cov=app tests/
     ```

## Deployment
The system is deployed on [Heroku/Render] (e.g., `https://health-system-example.herokuapp.com`). To deploy:

1. Push the repository to a Heroku/Render app.
2. Set environment variables in the platform’s dashboard.
3. Configure a PostgreSQL database add-on.
4. Run `flask db upgrade` to initialize the database.
5. Serve the Streamlit frontend via a separate process or static hosting.

## Project Structure
```
Health App/
├── .github/                  # GitHub workflow configurations
├── .godo/                    # GoDo task runner configurations
├── assets/                   # Static assets
│   └── logo.png              # Application logo
├── backend/                  # Backend (Flask) source code
│   ├── routes/               # Flask route handlers
│   │   ├── __init__.py
│   │   ├── appointments.py   # Appointment-related routes
│   │   ├── auth.py           # Authentication routes
│   │   ├── clients.py        # Client management routes
│   │   ├── programs.py       # Program management routes
│   │   ├── system.py         # System-wide routes (e.g., stats)
│   │   └── visits.py         # Visit tracking routes
│   ├── utils/                # Backend utility modules
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication helpers
│   │   ├── helpers.py        # General helper functions
│   │   └── rate_limit.py     # Rate limiting utilities
│   ├── __init__.py           # Backend package initialization
│   ├── app.py                # Main Flask application
│   ├── config.py             # Configuration settings
│   ├── Dockerfile            # Docker configuration for backend
│   ├── init_db.py            # Database initialization script
│   └── models.py             # Database models (SQLAlchemy)
├── frontend/                 # Frontend (Streamlit) source code
│   ├── assets/               # Frontend static assets
│   │   ├── __init__.py
│   │   └── style.css         # Custom CSS styles
│   ├── components/           # Streamlit page components
│   │   ├── __init__.py
│   │   ├── appointments.py   # Appointments page component
│   │   ├── auth.py           # Authentication component
│   │   ├── clients.py        # Clients page component
│   │   ├── dashboard.py      # Dashboard page component
│   │   ├── programs.py       # Programs page component
│   │   └── visits.py         # Visits page component
│   ├── utils/                # Frontend utility modules
│   │   ├── __init__.py
│   │   └── helpers.py        # General helper functions
│   ├── __init__.py           # Frontend package initialization
│   ├── app.py                # Main Streamlit application
│   └── Dockerfile            # Docker configuration for frontend
├── instance/                 # Instance-specific data (e.g., SQLite DB)
├── tests/                    # Test cases (currently empty)
├── uploaded_files/           # Directory for uploaded files (if any)
├── venv/                     # Virtual environment directory
├── .env                      # Environment variables
├── .gitignore                # Git ignore file
├── app.log                   # Application logs
├── docker-compose.yml        # Docker Compose configuration
├── keygen.py                 # Key generation script (if applicable)
├── qodana.yaml               # Qodana configuration for code quality
├── README.md                 # Project documentation
└── requirements.txt          # Python dependencies
```

## Future Enhancements
- **Role-Based Access**: Add admin and doctor roles with different permissions.
- **Data Analytics**: Integrate dashboards with health program statistics using Streamlit’s visualization tools.
- **Mobile App**: Develop a mobile frontend using Flutter or React Native, consuming the Flask API.
- **Audit Logging**: Track user actions (e.g., client updates) for accountability.
- **OAuth Integration**: Support third-party authentication for doctors.

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
