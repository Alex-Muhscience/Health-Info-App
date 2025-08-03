# 🚀 Quick Start Guide

## Prerequisites

Before you begin, ensure you have:
- **Python 3.9+** installed on your system
- **Git** for cloning the repository
- **Virtual environment** capability (venv or conda)

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/health-management-system.git
cd health-management-system
```

### 2. Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings (optional for quick start)
# The system will create default settings automatically
```

## 🏃‍♂️ Running the System

### Option 1: Automated Startup (Recommended)
```bash
python start_system.py
```

This will:
- ✅ Check system requirements
- ✅ Create sample database if needed
- ✅ Start Flask backend (Port 8000)
- ✅ Start Django frontend (Port 8001)
- ✅ Display access URLs and login credentials

### Option 2: Manual Startup
```bash
# Terminal 1 - Start Backend
cd backend
python app.py

# Terminal 2 - Start Frontend
cd django_frontend
python manage.py runserver 8001
```

## 🌐 Access the System

Once started, access the system at:

- **🎨 Web Interface**: http://localhost:8001
- **🔧 API Backend**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/api/docs

## 👤 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Doctor | `dr.smith` | `doctor123` |
| Nurse | `nurse.jane` | `nurse123` |

## 🎯 First Steps

1. **Login** with admin credentials
2. **Explore Dashboard** - View system overview and analytics
3. **Browse Patients** - See sample patient data
4. **Check Analytics** - View comprehensive healthcare insights
5. **Try Features** - Explore appointments, visits, staff management

## 🔧 Configuration

### Database
- **Development**: SQLite (automatic)
- **Production**: PostgreSQL (configure DATABASE_URL in .env)

### Security
- **JWT Tokens**: Automatically configured for development
- **CORS**: Configured for localhost
- **Rate Limiting**: Basic protection enabled

### Analytics
- **Real-time Dashboard**: Automatic
- **Sample Data**: Pre-loaded for testing
- **Reports**: Available in Analytics menu

## 📊 Sample Data

The system includes:
- 👥 **50+ Patients** with medical histories
- 👨‍⚕️ **Medical Staff** across departments
- 📅 **Appointments** and visits
- 🏥 **Hospital Operations** (admissions, billing)
- 📈 **Analytics Data** for insights

## 🆘 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Kill processes on ports 8000/8001
# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

**Database Issues**
```bash
# Recreate database
python scripts/create_comprehensive_db.py
```

**Permission Errors**
```bash
# Ensure virtual environment is activated
# Check Python version: python --version
```

### Still Need Help?

1. Check the full [README.md](README.md) for detailed information
2. Review error messages in the terminal
3. Ensure all dependencies are installed
4. Verify Python version compatibility

## 🚀 What's Next?

- Explore the **Analytics Dashboard** for healthcare insights
- Try **Patient Management** features
- Test **Appointment Scheduling**
- Review **Security Features** and audit logs
- Check out **API Endpoints** for integration

## 🎉 You're Ready!

The Health Management System is now running and ready for use. Enjoy exploring all the healthcare management features!

---

**Need more help?** Check our detailed documentation in the `/docs` folder or refer to the main README.md file.
