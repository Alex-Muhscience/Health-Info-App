# 🏥 Health Management System - Startup Guide

## 🚀 Quick Start

### Option 1: Use the Batch File (Windows)
Simply double-click `start_services.bat` to start both backend and frontend automatically.

### Option 2: Manual Start

1. **Start Backend Server**:
   ```bash
   cd backend
   python app.py
   ```

2. **Start Frontend Server** (in a new terminal):
   ```bash
   cd frontend
   streamlit run app.py --server.port 8501
   ```

## 🔐 Admin Login

Once both services are running:

1. Open your browser and go to: http://localhost:8501
2. Login with the admin credentials:
   - **Username**: `admin`
   - **Password**: `admin123`

## ✅ Admin Permissions

When logged in as admin, you have **full access** to all system features:

- ✅ **Dashboard**: View system statistics and overview
- ✅ **Clients**: Create, view, edit, and manage patient records
- ✅ **Appointments**: Schedule and manage appointments
- ✅ **Visits**: Record and track patient visits
- ✅ **Programs**: Create and manage health programs

## 🔧 System Components

### Backend (Flask API)
- **URL**: http://127.0.0.1:8000
- **Health Check**: http://127.0.0.1:8000/health
- **API Documentation**: Available when logged in

### Frontend (Streamlit)
- **URL**: http://localhost:8501
- **Interactive Interface**: Web-based dashboard

## 🛠️ Troubleshooting

### Backend Won't Start
1. Check if Python packages are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify database connection:
   ```bash
   python create_admin.py
   ```

### Frontend Won't Start
1. Check if Streamlit is installed:
   ```bash
   pip install streamlit streamlit-option-menu
   ```

2. Verify backend is running first

### Login Issues
1. Ensure backend is running on port 8000
2. Check system status using the "Check System Status" button
3. Verify admin user exists by running:
   ```bash
   python create_admin.py
   ```

### Permission Issues
- Admin users have access to **all features**
- Other roles have restricted access:
  - **Doctor**: Dashboard, Clients, Appointments, Visits, Programs
  - **Nurse/Receptionist**: Dashboard, Clients, Appointments, Visits
  - **Others**: Dashboard, Clients only

## 📋 Database Setup

The system uses SQLite by default, but can be configured for PostgreSQL:

### SQLite (Default)
- Database file: `instance/health_system.db`
- No additional setup required

### PostgreSQL (Optional)
1. Run the PostgreSQL setup script:
   ```bash
   python setup_postgresql.py
   ```

2. Update the `.env` file to use PostgreSQL URLs

## 🔒 Security Notes

- **Change the default admin password** after first login
- The system includes JWT authentication
- API endpoints are protected with role-based access control
- Input validation and sanitization are implemented

## 📝 System Features

### For Admins
- User management (create new users)
- Full system access
- System configuration
- All CRUD operations

### Core Functionality
- Patient/Client management
- Health program enrollment
- Appointment scheduling
- Visit tracking
- Dashboard analytics

## 🔄 Stopping the Services

- Press `Ctrl+C` in the terminal windows running the services
- Or close the command windows opened by the batch file

## 📞 Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all requirements are installed
3. Ensure ports 8000 and 8501 are available
4. Check the database connection

---

**Happy Healthcare Managing! 🏥**
