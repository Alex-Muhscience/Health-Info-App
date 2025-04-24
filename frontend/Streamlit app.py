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

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'menu_choice' not in st.session_state:
    st.session_state.menu_choice = "Dashboard"
if 'view_client_id' not in st.session_state:
    st.session_state.view_client_id = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None


# Helper functions
def make_authenticated_request(method, endpoint, **kwargs):
    """Handle all API requests with authentication and error handling"""
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

    if not st.session_state.token:
        st.markdown("### Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            with st.spinner("Authenticating..."):
                response = make_authenticated_request(
                    "POST", "/api/auth/login",
                    json={"username": username, "password": password}
                )

                if response and response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data.get('token')
                    st.session_state.current_user = data.get('user')
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                elif response:
                    st.error(f"Login failed: {response.json().get('message', 'Invalid credentials')}")
    else:
        st.markdown(f"### Welcome, {st.session_state.current_user.get('username', 'User')}")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.current_user = None
            st.session_state.menu_choice = "Dashboard"
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
        st.markdown("---")
        st.markdown("""
            <div style="font-size: 0.8rem; color: #e0e0e0;">
                <p>Version 1.2.0</p>
                <p>Last updated: {}</p>
            </div>
        """.format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)

# Main content - only show if authenticated
if st.session_state.token:
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

        st.markdown("---")
        st.markdown("### Quick Actions")

        quick_col1, quick_col2, quick_col3 = st.columns(3)

        with quick_col1:
            if st.button("Register New Client", key="quick_register"):
                st.session_state.menu_choice = "Register Client"
                st.rerun()

        with quick_col2:
            if st.button("Process Enrollment", key="quick_enroll"):
                st.session_state.menu_choice = "Enroll Client"
                st.rerun()

        with quick_col3:
            if st.button("Generate Reports", key="quick_reports"):
                st.warning("Reports feature coming soon!")

    elif st.session_state.menu_choice == "Programs":
        st.subheader("Health Programs Management")

        tab1, tab2 = st.tabs(["View Programs", "Add New Program"])

        with tab1:
            with st.spinner("Loading programs..."):
                response = make_authenticated_request("GET", "/api/programs")

                if response and response.status_code == 200:
                    programs = response.json()
                    if programs:
                        st.success(f"Found {len(programs)} programs")
                        for program in programs:
                            with st.expander(f"{program['name']} ({'Active' if program['is_active'] else 'Inactive'})"):
                                st.write(f"**Description:** {program.get('description', 'No description')}")

                                cols = st.columns(3)
                                with cols[0]:
                                    if st.button("Edit", key=f"edit_{program['id']}"):
                                        st.session_state.edit_program_id = program['id']
                                        st.rerun()
                                with cols[1]:
                                    if st.button("Delete", key=f"delete_{program['id']}"):
                                        delete_response = make_authenticated_request(
                                            "DELETE", f"/api/programs/{program['id']}"
                                        )
                                        if delete_response and delete_response.status_code == 200:
                                            st.success("Program deleted successfully!")
                                            st.rerun()
                                        elif delete_response:
                                            st.error(
                                                f"Failed to delete: {delete_response.json().get('message', 'Unknown error')}")
                    else:
                        st.info("No programs found")
                elif response:
                    st.error(f"Failed to load programs: {response.json().get('message', 'Unknown error')}")

        with tab2:
            with st.form("add_program_form"):
                name = st.text_input("Program Name*")
                description = st.text_area("Description")
                is_active = st.checkbox("Active", value=True)

                submitted = st.form_submit_button("Add Program")
                if submitted:
                    if name:
                        with st.spinner("Adding program..."):
                            response = make_authenticated_request(
                                "POST", "/api/programs",
                                json={
                                    "name": name,
                                    "description": description,
                                    "is_active": is_active
                                }
                            )

                            if response and response.status_code == 201:
                                st.success("Program added successfully!")
                                st.rerun()
                            elif response:
                                st.error(f"Failed to add program: {response.json().get('message', 'Unknown error')}")
                    else:
                        st.warning("Program name is required")

    elif st.session_state.menu_choice == "Client Profile":
        st.subheader("Client Profile")

        client_id = st.session_state.get('view_client_id') or st.text_input("Enter Client ID")

        if client_id:
            with st.spinner("Loading client data..."):
                response = make_authenticated_request("GET", f"/api/clients/{client_id}")

                if response and response.status_code == 200:
                    client = response.json()

                    # Display profile header
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image("https://via.placeholder.com/150?text=Profile", width=150)
                    with cols[1]:
                        st.markdown(f"# {client.get('first_name', '')} {client.get('last_name', '')}")
                        st.markdown(f"**ID:** {client.get('id', 'N/A')} | **Phone:** {client.get('phone', 'N/A')}")

                    # Tabs for different sections
                    tab1, tab2, tab3 = st.tabs(["📋 Profile", "🏥 Programs", "📅 Visits"])

                    with tab1:
                        # Personal information
                        cols = st.columns(2)
                        with cols[0]:
                            st.markdown("### Personal Information")
                            st.write(f"**Date of Birth:** {client.get('dob', 'N/A')}")
                            st.write(f"**Gender:** {client.get('gender', 'N/A')}")
                            st.write(f"**Address:** {client.get('address', 'N/A')}")
                        with cols[1]:
                            st.markdown("### Emergency Contact")
                            st.write(f"**Name:** {client.get('emergency_contact_name', 'N/A')}")
                            st.write(f"**Phone:** {client.get('emergency_contact_phone', 'N/A')}")
                            st.write(f"**Notes:** {client.get('notes', 'None')}")

                    with tab2:
                        # Program enrollment
                        st.markdown("### Enrolled Programs")
                        programs_response = make_authenticated_request("GET", f"/api/clients/{client_id}/programs")

                        if programs_response and programs_response.status_code == 200:
                            programs = programs_response.json()
                            if programs:
                                for program in programs:
                                    with st.expander(
                                            f"{program.get('program', {}).get('name', 'Unknown')} - {program.get('status', 'Active')}"):
                                        st.write(f"**Enrolled:** {program.get('enrollment_date', 'N/A')}")
                                        st.write(f"**Progress:**")
                                        st.progress(program.get('progress', 0) / 100)
                                        if program.get('notes'):
                                            st.write(f"**Notes:** {program['notes']}")
                            else:
                                st.info("Client is not enrolled in any programs")

                        # Enroll in new program
                        with st.form("enroll_form"):
                            available_programs_response = make_authenticated_request("GET", "/api/programs")
                            available_programs = []
                            if available_programs_response and available_programs_response.status_code == 200:
                                available_programs = [(p['id'], p['name']) for p in available_programs_response.json()]

                            selected_programs = st.multiselect(
                                "Available Programs",
                                options=[p[1] for p in available_programs],
                                format_func=lambda x: x
                            )

                            if st.form_submit_button("Enroll in Selected Programs"):
                                if selected_programs:
                                    program_ids = [p[0] for p in available_programs if p[1] in selected_programs]
                                    enroll_response = make_authenticated_request(
                                        "POST", f"/api/clients/{client_id}/enroll",
                                        json={"program_ids": program_ids}
                                    )

                                    if enroll_response and enroll_response.status_code == 201:
                                        st.success("Enrollment successful!")
                                        st.rerun()
                                    elif enroll_response:
                                        st.error(
                                            f"Enrollment failed: {enroll_response.json().get('message', 'Unknown error')}")
                                else:
                                    st.warning("Please select at least one program")

                    with tab3:
                        # Visit history
                        st.markdown("### Visit History")
                        visits_response = make_authenticated_request("GET", f"/api/visits/client/{client_id}")

                        if visits_response and visits_response.status_code == 200:
                            visits = visits_response.json()
                            if visits:
                                for visit in visits:
                                    with st.expander(f"Visit on {visit.get('visit_date', 'N/A')}"):
                                        st.write(f"**Purpose:** {visit.get('purpose', 'N/A')}")
                                        st.write(f"**Diagnosis:** {visit.get('diagnosis', 'N/A')}")
                                        st.write(f"**Treatment:** {visit.get('treatment', 'N/A')}")
                                        if visit.get('notes'):
                                            st.write(f"**Notes:** {visit['notes']}")
                            else:
                                st.info("No visit history found")

                        # Add new visit
                        with st.form("new_visit_form"):
                            st.markdown("### Record New Visit")
                            purpose = st.text_input("Purpose*")
                            diagnosis = st.text_area("Diagnosis")
                            treatment = st.text_area("Treatment")
                            visit_notes = st.text_area("Notes")

                            if st.form_submit_button("Save Visit"):
                                if purpose:
                                    new_visit_response = make_authenticated_request(
                                        "POST", f"/api/visits/client/{client_id}",
                                        json={
                                            "purpose": purpose,
                                            "diagnosis": diagnosis,
                                            "treatment": treatment,
                                            "notes": visit_notes
                                        }
                                    )

                                    if new_visit_response and new_visit_response.status_code == 201:
                                        st.success("Visit recorded successfully!")
                                        st.rerun()
                                    elif new_visit_response:
                                        st.error(
                                            f"Failed to record visit: {new_visit_response.json().get('message', 'Unknown error')}")
                                else:
                                    st.warning("Purpose is required")

                elif response:
                    st.error(f"Failed to load client: {response.json().get('message', 'Unknown error')}")

    elif st.session_state.menu_choice == "Admin":
        st.subheader("Administration Panel")

        if st.session_state.current_user.get('role') != 'admin':
            st.warning("You don't have permission to access this section")
            st.session_state.menu_choice = "Dashboard"
            st.rerun()

        tab1, tab2 = st.tabs(["User Management", "System Settings"])

        with tab1:
            st.markdown("### User Management")

            with st.form("register_user_form"):
                st.markdown("#### Register New User")
                username = st.text_input("Username*")
                email = st.text_input("Email*")
                password = st.text_input("Password*", type="password")
                role = st.selectbox("Role", ["user", "admin"])

                if st.form_submit_button("Register User"):
                    if username and email and password:
                        with st.spinner("Registering user..."):
                            response = make_authenticated_request(
                                "POST", "/api/auth/register",
                                json={
                                    "username": username,
                                    "email": email,
                                    "password": password,
                                    "role": role
                                }
                            )

                            if response and response.status_code == 201:
                                st.success("User registered successfully!")
                            elif response:
                                st.error(f"Registration failed: {response.json().get('message', 'Unknown error')}")
                    else:
                        st.warning("Please fill all required fields (*)")

# Footer
st.markdown("---")
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