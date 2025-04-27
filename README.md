# Health Information Management System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0%2B-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

A modern, user-friendly **Health Information System** designed to manage clients and health programs/services, built as a software engineering intern task. This system enables doctors to create health programs, register and manage clients, enroll clients in programs, search for clients, view detailed client profiles, and expose client profiles via a secure API. The solution prioritizes clean code, intuitive UI/UX, and extensibility, with additional features like data security, testing, and deployment.

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

## Features
- **Health Program Management**: Create and manage health programs (e.g., TB, Malaria, HIV).
- **Client Registration**: Register new clients with essential details (e.g., name, ID, contact).
- **Program Enrollment**: Enroll clients in one or more health programs.
- **Client Search**: Search for clients by name or ID from the registered client list.
- **Client Profile View**: View detailed client profiles, including enrolled programs, via a clean Streamlit UI.
- **API Exposure**: Securely expose client profiles through a RESTful API for integration with external systems.
- **Enhanced UI/UX**: Modern, responsive frontend built with Streamlit, featuring intuitive navigation and separated CSS for maintainability.
- **Security**: JWT-based authentication, password hashing, and input validation to protect sensitive data.
- **Testing**: Unit and integration tests to ensure reliability.
- **Deployment**: Deployed on a cloud platform (e.g., Heroku, Render) for accessibility.

## Tech Stack
- **Backend**: Flask (Python) with SQLAlchemy for ORM and SQLite/PostgreSQL for the database.
- **Frontend**: Streamlit for a reactive, user-friendly interface with external CSS for styling.
- **Authentication**: JWT (JSON Web Tokens) for secure API access.
- **API**: RESTful endpoints with Flask-RESTful.
- **Testing**: Pytest for unit and integration tests.
- **Deployment**: Heroku/Render with Gunicorn for production-grade hosting.
- **Others**: `python-dotenv` for environment variables, `bcrypt` for password hashing.

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
health-information-system/
├── app.py                  # Flask backend entry point
├── frontend/
│   ├── app.py            # Streamlit frontend entry point
│   └── static/
│       └── styles.css    # Separated CSS for UI
├── models/                 # SQLAlchemy models (Client, Program, Enrollment)
├── routes/                 # Flask API routes
├── tests/                  # Unit and integration tests
├── .env                    # Environment variables (not committed)
├── requirements.txt        # Python dependencies
├── prototype_demo.mp4      # Prototype demonstration video
├── presentation.pptx       # PowerPoint presentation
├── README.md               # Project documentation
└── .gitignore              # Git ignore file
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
