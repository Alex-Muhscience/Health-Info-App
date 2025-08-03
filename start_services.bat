@echo off
echo 🏥 Health Management System Startup
echo =====================================
echo.

echo 🚀 Starting Backend Server...
start "Backend Server" cmd /k "cd /d "%~dp0backend" && python app.py"

echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo 🚀 Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && streamlit run app.py --server.port 8501"

echo.
echo ✅ Both services are starting!
echo.
echo 🌐 Backend: http://127.0.0.1:8000
echo 🌐 Frontend: http://localhost:8501
echo.
echo 💡 Login with:
echo    Username: admin
echo    Password: admin123
echo.
echo Press any key to exit this window...
pause > nul
