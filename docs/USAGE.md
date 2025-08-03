# Health Management System - Usage Guide

## 🚀 Quick Start

The Health Management System is a complete healthcare application with a Flask backend API and Streamlit frontend interface.

### Prerequisites
- Python 3.11 or higher
- All dependencies from `requirements.txt` installed

### Running the Application

#### Option 1: Complete Startup (Recommended)
```bash
cd "D:\Personal_Projects\Health App"
python start_app.py
```

This will start both backend and frontend servers and provide access URLs.

#### Option 2: Manual Startup
Start backend:
```bash
python run_backend.py
```

In a separate terminal, start frontend:
```bash
python run_frontend.py
```

## 🏥 Application Access

- **Frontend (Web Interface)**: http://localhost:8501
- **Backend API**: http://127.0.0.1:8000
- **Health Check**: http://127.0.0.1:8000/health

## 🔐 Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

## 📋 Features Overview

### User Roles & Permissions

| Feature | Admin | Doctor | Nurse | Receptionist |
|---------|-------|--------|-------|--------------|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| View Clients | ✅ | ✅ | ✅ | ✅ |
| Create/Update Clients | ✅ | ✅ | ✅ | ✅ |
| Delete Clients | ✅ | ❌ | ❌ | ❌ |
| Manage Programs | ✅ | ✅ | ❌ | ❌ |
| Record Visits | ✅ | ✅ | ✅ | ❌ |
| Schedule Appointments | ✅ | ✅ | ✅ | ✅ |
| User Management | ✅ | ❌ | ❌ | ❌ |

## 📊 Dashboard

The dashboard provides:
- System statistics (total clients, programs, recent activity)
- Recent appointments and visits
- Quick action buttons for common tasks
- System health information

## 👥 Client Management

### Viewing Clients
- **Access**: Dashboard → Clients → View Clients
- **Features**:
  - Search by name, phone, or email
  - Filter by gender, age range, active status
  - Pagination support
  - View client details

### Managing Clients

#### Creating New Clients
1. Go to **Clients → Manage Clients → Create New Client**
2. Fill required fields (marked with *)
3. Add optional information (address, emergency contact, notes)
4. Click "Create Client"

#### Updating Clients
1. Go to **Clients → Manage Clients → Update Client**
2. Enter Client ID and click "Load Client"
3. Modify the information as needed
4. Click "Update Client"

#### Deactivating Clients (Admin Only)
1. Go to **Clients → Manage Clients → Deactivate Client**
2. Enter Client ID
3. Preview client information
4. Confirm deactivation

## 🏥 Program Management

### Viewing Programs
- Lists all health programs with descriptions and duration
- Filter by active status or search by name

### Managing Programs (Admin/Doctor Only)

#### Creating Programs
1. Go to **Programs → Manage Programs → Create New Program**
2. Enter program name (required), description, and duration
3. Set active status
4. Click "Create Program"

#### Updating Programs
1. Enter Program ID to load existing program
2. Modify information as needed
3. Click "Update Program"

### Program Enrollments
- View all clients enrolled in a specific program
- Enroll new clients in programs
- Track enrollment status and progress

## 📅 Appointment Management

### Viewing Appointments
- Filter by client ID, status, or date range
- View appointment details including duration and notes

### Scheduling Appointments
1. Go to **Appointments → Schedule Appointment**
2. Enter client ID, date/time, duration, and reason
3. Add optional notes
4. Click "Schedule Appointment"

### Updating Appointments
1. Enter Appointment ID to load existing appointment
2. Modify details as needed
3. Update status (Scheduled/Completed/Cancelled)
4. Click "Update Appointment"

## 🏥 Visit Management

Visit management allows healthcare providers to record and track patient visits.

### Recording Visits
1. Go to **Visits → Record Visit**
2. Enter client ID and visit date/time
3. Select visit type (consultation, follow-up, emergency, etc.)
4. Add purpose, diagnosis, treatment, and notes
5. Click "Record Visit"

### Visit Types
- **Consultation**: General medical consultation
- **Follow-up**: Follow-up appointment
- **Emergency**: Emergency visit
- **Vaccination**: Vaccination appointment
- **Test**: Medical test or examination
- **Procedure**: Medical procedure
- **Other**: Other types of visits

### Updating Visits
1. Enter Visit ID to load existing visit
2. Modify information as needed
3. Click "Update Visit"

## 🔧 API Documentation

The backend provides a RESTful API with the following endpoints:

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/register` - Register new user (admin only)

### Clients
- `GET /api/clients` - List clients with filters
- `POST /api/clients` - Create new client
- `GET /api/clients/{id}` - Get client by ID
- `PUT /api/clients/{id}` - Update client
- `DELETE /api/clients/{id}` - Deactivate client
- `GET /api/clients/{id}/programs` - Get client's programs
- `POST /api/clients/{id}/programs` - Enroll client in programs

### Programs
- `GET /api/programs` - List programs
- `POST /api/programs` - Create new program
- `GET /api/programs/{id}` - Get program by ID
- `PUT /api/programs/{id}` - Update program
- `GET /api/programs/{id}/enrollments` - Get program enrollments

### Appointments
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Create new appointment
- `GET /api/appointments/{id}` - Get appointment by ID
- `PUT /api/appointments/{id}` - Update appointment

### Visits
- `GET /api/visits` - List visits
- `POST /api/visits/{client_id}` - Create new visit
- `GET /api/visits/{id}` - Get visit by ID
- `PUT /api/visits/{id}` - Update visit

### Dashboard
- `GET /api/dashboard/stats` - Get system statistics
- `GET /api/dashboard/appointments` - Get recent appointments
- `GET /api/dashboard/visits` - Get recent visits

## 🛠️ Technical Details

### Backend Technology Stack
- **Framework**: Flask 3.1.0
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0.40
- **Authentication**: JWT (JSON Web Tokens)
- **Serialization**: Marshmallow
- **Security**: Flask-Talisman, CORS, Rate Limiting
- **Validation**: Custom validators for emails, phones, etc.

### Frontend Technology Stack
- **Framework**: Streamlit 1.44.1
- **UI Components**: streamlit-option-menu
- **Data Handling**: Pandas, Plotly
- **HTTP Requests**: requests library
- **Styling**: Custom CSS

### Database Schema
- **Users**: System users with roles and permissions
- **Clients**: Patient/client information
- **Programs**: Health programs and services
- **ClientPrograms**: Client enrollment in programs
- **Visits**: Medical visit records
- **Appointments**: Scheduled appointments

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for secure password storage
- **Role-Based Access Control**: Different permissions for user roles
- **Input Validation**: Comprehensive validation for all user inputs
- **CORS Protection**: Configured for frontend/backend communication
- **Security Headers**: HSTS, CSP, XSS protection
- **Rate Limiting**: Protection against abuse (disabled in development)

## 🚀 Deployment

### Development
The application is configured for local development with:
- SQLite database
- Debug mode enabled
- CORS configured for localhost
- Disabled HTTPS requirements

### Production Considerations
For production deployment:
1. Update database to PostgreSQL
2. Enable HTTPS and security headers
3. Configure Redis for rate limiting
4. Set proper environment variables
5. Use production WSGI server (Gunicorn)
6. Configure proper logging

## 📝 Logging

The application includes comprehensive logging:
- Request/response logging
- Error tracking
- User action auditing
- Configurable log levels
- Rotating log files

## 🧪 Testing

Run tests using:
```bash
pytest tests/
```

For coverage reports:
```bash
pytest --cov=backend tests/
```

## 🤝 Support

For issues or questions:
1. Check the logs in `app.log`
2. Verify all dependencies are installed
3. Ensure database connectivity
4. Check API endpoint documentation

## 📈 Performance Tips

1. **Database Optimization**:
   - Use pagination for large datasets
   - Implement database indexing
   - Use connection pooling

2. **Frontend Optimization**:
   - Use caching for API responses
   - Implement lazy loading for large tables
   - Optimize Streamlit state management

3. **API Optimization**:
   - Implement proper error handling
   - Use appropriate HTTP status codes
   - Implement API versioning

## 🔄 Data Management

### Backup Recommendations
- Regular database backups
- Export client data periodically
- Version control for code changes

### Data Migration
- Use SQLAlchemy migrations for schema changes
- Test migrations on staging environment
- Maintain data integrity during updates
