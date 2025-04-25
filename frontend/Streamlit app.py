import streamlit as st
import requests
from datetime import datetime
import time
from pathlib import Path

BASE_URL = "http://localhost:5000"

# Configure page
st.set_page_config(
    page_title="Health Info System",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

# Initialize session state with default values
if 'initialized' not in st.session_state:
    st.session_state.update({
        'token': None,
        'current_user': None,
        'menu_choice': "Dashboard",
        'view_client_id': None,
        'initialized': True
    })


# Load CSS
def load_css():
    css = """
    <style>
        /* Main container styles */
        .main {
            padding: 2rem;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }

        /* Sidebar styles */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #2e7d32, #1b5e20);
            color: white;
            padding: 1.5rem;
        }

        /* Button styles */
        .stButton > button {
            background-color: #2e7d32;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
            border: none;
            font-weight: 500;
        }

        .stButton > button:hover {
            background-color: #1b5e20;
            transform: scale(1.02);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        /* Card styles */
        .card {
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1rem;
            background-color: #f8f9fa;
            border-left: 5px solid #2e7d32;
            transition: transform 0.3s;
        }

        /* Notification styles */
        .stAlert {
            border-radius: 8px;
        }

        .stSuccess {
            background-color: #e8f5e9;
            color: #2e7d32;
        }

        .stError {
            background-color: #ffebee;
            color: #c62828;
        }

        /* Footer styles */
        .footer {
            margin-top: 3rem;
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
            padding: 1rem;
            border-top: 1px solid #eee;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


load_css()


# Helper functions
def make_authenticated_request(method, endpoint, **kwargs):
    headers = kwargs.pop('headers', {})
    if st.session_state.token:
        headers['Authorization'] = f"Bearer {st.session_state.token}"

    try:
        response = requests.request(
            method,
            f"{BASE_URL}{endpoint}",
            headers=headers,
            **kwargs
        )

        if response.status_code == 401:
            st.error("Session expired. Please log in again.")
            st.session_state.token = None
            st.session_state.current_user = None
            st.rerun()
        return response

    except requests.exceptions.ConnectionError:
        st.error("🔴 Backend server unavailable. Please ensure the backend is running.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"🛑 Network error: {str(e)}")
        return None


# App title and description
st.title("🏥 Health Information Management System")
st.markdown("""
    <div style="margin-bottom: 2rem; color: #4a4a4a;">
        Comprehensive platform for managing client health records and program enrollments
    </div>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=Health+System", width=150)

    # In your sidebar
    if not st.session_state.token:
        st.markdown("### Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            with st.spinner("Authenticating..."):
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/auth/login",
                        json={"username": username, "password": password},
                        timeout=5
                    )
                    response.raise_for_status()

                    data = response.json()
                    st.session_state.update({
                        'token': data['token'],
                        'current_user': data['user'],
                        'menu_choice': "Dashboard"
                    })
                    st.success("Login successful!")
                    time.sleep(0.3)
                    st.rerun()  # More reliable than st.rerun()

                except requests.exceptions.RequestException as e:
                    error_msg = e.response.json().get('message', 'Login failed') if hasattr(e, 'response') else str(e)
                    st.error(f"Login failed: {error_msg}")
    else:
        # Show logged-in UI
        st.markdown(f"### Welcome, {st.session_state.current_user.get('username', 'User')}")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.current_user = None
            st.session_state.menu_choice = None
            st.rerun()

        st.markdown("""
            <div style="margin: 1rem 0; font-size: 1.1rem; font-weight: bold; color: white;">
                Main Navigation
            </div>
        """, unsafe_allow_html=True)

        menu = [
            {"icon": "🏠", "label": "Dashboard", "key": "home"},
            {"icon": "👤", "label": "Register Client", "key": "register"},
            {"icon": "📋", "label": "Enroll Client", "key": "enroll"},
            {"icon": "🔍", "label": "Search Clients", "key": "search"},
            {"icon": "📊", "label": "Client Profile", "key": "profile"},
            {"icon": "🏥", "label": "Programs", "key": "programs"},
            {"icon": "⚙️", "label": "Admin", "key": "admin"}
        ]

        choice = st.radio(
            "Navigate to:",
            options=[item["label"] for item in menu],
            format_func=lambda x: f"{next(item['icon'] for item in menu if item['label'] == x)} {x}",
            label_visibility="collapsed",
            key="nav_radio"
        )
        st.session_state.menu_choice = choice

# Main content
if not st.session_state.token:
    st.warning("Please login to access the system")
else:
    if st.session_state.menu_choice == "Dashboard":
        st.subheader("System Overview")
        with st.spinner("Loading system data..."):
            stats_response = make_authenticated_request("GET", "/api/stats")

            if stats_response and stats_response.status_code == 200:
                stats = stats_response.json()
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                        <div class="card">
                            <h3>Total Clients</h3>
                            <p style="font-size: 2rem; margin: 0.5rem 0;">{stats.get('total_clients', 'N/A')}</p>
                            <p style="color: #2e7d32; font-size: 0.9rem;">↑ {stats.get('client_growth', '0')}% from last month</p>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div class="card">
                            <h3>Active Programs</h3>
                            <p style="font-size: 2rem; margin: 0.5rem 0;">{stats.get('active_programs', 'N/A')}</p>
                            <p style="color: #2e7d32; font-size: 0.9rem;">{stats.get('program_names', 'Loading...')}</p>
                        </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                        <div class="card">
                            <h3>Recent Activity</h3>
                            <p style="font-size: 0.9rem;">{stats.get('recent_enrollments', '0')} new enrollments today</p>
                            <p style="font-size: 0.9rem;">{stats.get('recent_registrations', '0')} client registrations</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("Failed to load system statistics")

    # Other menu choices would follow the same pattern
    # Add similar blocks for Programs, Client Profile, Admin sections

# Footer
st.markdown("""
    <div class="footer">
        <p>© 2023 Health Information Management System | For authorized use only</p>
        <p>Need help? Contact <a href="mailto:support@healthsystem.org">support@healthsystem.org</a></p>
    </div>
""", unsafe_allow_html=True)

# Backend connection check
if st.session_state.token:
    with st.spinner("Checking backend connection..."):
        response = make_authenticated_request("GET", "/api/health")
        if not response:
            st.error("🚨 Cannot connect to the backend server! Please ensure the backend service is running.")
            st.stop()