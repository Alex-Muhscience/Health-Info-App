# Health Management System

Welcome to the Health Management System, a comprehensive solution designed to streamline healthcare facility operations through modern web technologies. This system offers extensive functionalities including patient management, appointment scheduling, analytics, and more.

## Key Features

- **Patient Management:** Maintain comprehensive patient records, track appointments, and manage communications.
- **Analytics and Reporting:** Real-time dashboards, predictive analytics, and historical data analysis.
- **Security:** HIPAA compliant with role-based access, data encryption, and audit logs.
- **Integration:** Seamless integration between Django frontend and Flask API backend.
- **Responsive Design:** Accessible on multiple devices with a modern and intuitive user interface.

## Architecture Overview

The system is designed using a microservices approach with:

- **Django Frontend** (Port 8001): Manages the user interface and user authentication.
- **Flask Backend** (Port 8000): Handles API requests, business logic, and data processing.
- **PostgreSQL Database:** Stores all persistent data with reliability and scalability.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/health-management-system.git
   cd health-management-system
   ```

2. **Set Up the Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ````

4. **Environment Variables**

   Configure your `.env` file with necessary database connections and secret keys.

5. **Initialize the Database**

   ```bash
   python scripts/init_db.py
   ```

6. **Run the Applications**

   - **Backend**: `flask run`
   - **Frontend**: `python manage.py runserver 8001`

## Contribute

Contributions are welcome! Please fork the repository and submit pull requests for any improvements or new features.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For support or inquiries, please contact `support@healthmanagementsystem.com`.

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
