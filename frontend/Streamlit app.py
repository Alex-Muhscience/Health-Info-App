import streamlit as st
import requests
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
from typing import Optional, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "http://localhost:8000/api"  # Update with your backend URL
TOKEN_EXPIRY_BUFFER = 120  # 5 minutes buffer for token expiry
APP_NAME = "Health Information System"
APP_VERSION = "1.1.0"

# Page configuration
st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://example.com/help',
        'Report a bug': "https://example.com/bug",
        'About': f"### {APP_NAME} v{APP_VERSION}\nA comprehensive healthcare management system"
    }
)

# Type aliases
ClientData = Dict[str, Any]
UserData = Dict[str, Any]


# --- Utility Functions ---
def load_css() -> None:
    """Load custom CSS styles with enhanced UI elements"""
    custom_css = """
    <style>
        /* Main content styling */
        .main {
            padding: 2rem;
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
            padding: 1.5rem;
        }

        /* Button styling */
        .stButton>button {
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Input field styling */
        .stTextInput>div>div>input, 
        .stTextArea>div>div>textarea,
        .stSelectbox>div>div>select {
            border-radius: 8px;
            padding: 0.5rem;
        }

        /* Card styling */
        .card {
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            background-color: white;
        }

        /* Metrics styling */
        .metric {
            text-align: center;
            padding: 1rem;
            border-radius: 12px;
            background-color: #f8f9fa;
        }

        /* Custom colors */
        :root {
            --primary-color: #4e73df;
            --success-color: #1cc88a;
            --danger-color: #e74a3b;
            --warning-color: #f6c23e;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def initialize_session() -> None:
    """Initialize session state variables"""
    session_defaults = {
        'token': None,
        'token_expiry': None,
        'current_user': None,
        'menu_choice': "Dashboard",
        'view_client_id': None,
        'last_api_call': None,
        'dark_mode': False
    }

    for key, default in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def is_token_valid() -> bool:
    """Check if the current token is still valid"""
    if not st.session_state.token or not st.session_state.token_expiry:
        return False
    return datetime.utcnow() < st.session_state.token_expiry - timedelta(seconds=TOKEN_EXPIRY_BUFFER)


def make_authenticated_request(
        method: str,
        endpoint: str,
        **kwargs
) -> Optional[requests.Response]:
    """
    Make an authenticated API request with enhanced error handling
    and loading indicators
    """
    # Show loading spinner for API calls
    with st.spinner("Loading..."):
        try:
            # Check token validity
            if not is_token_valid():
                st.session_state.token = None
                st.session_state.current_user = None
                st.error("🔒 Session expired. Please login again.")
                st.rerun()
                return None

            headers = kwargs.pop('headers', {})
            headers.update({
                'Authorization': f"Bearer {st.session_state.token}",
                'Content-Type': 'application/json'
            })

            st.session_state.last_api_call = datetime.utcnow()
            response = requests.request(
                method,
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10,
                **kwargs
            )

            # Handle specific status codes
            if response.status_code == 401:
                st.error("🔒 Session expired. Please login again.")
                st.session_state.token = None
                st.session_state.current_user = None
                st.rerun()
            elif response.status_code == 403:
                st.error("⛔ You don't have permission to perform this action")
            elif response.status_code >= 500:
                st.error("🔴 Server error. Please try again later.")

            return response

        except requests.exceptions.ConnectionError:
            st.error("🔌 Could not connect to the server. Please check your connection.")
            logger.error("Connection error to backend")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error: {str(e)}")
            return None


def display_error(response: requests.Response) -> None:
    """Display API error messages in a user-friendly way"""
    try:
        error_data = response.json()
        error_msg = error_data.get('error', error_data.get('message', 'Unknown error'))
        st.error(f"⚠️ {error_msg}")
    except ValueError:
        st.error(f"⚠️ HTTP Error {response.status_code}: {response.text}")


# --- UI Components ---
def login_form() -> None:
    """Enhanced login form with better UX"""
    with st.sidebar:
        with st.form("login_form"):
            st.image("assets\logo.png", width=200)
            st.markdown("### Sign in to your account")

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            col1, col2 = st.columns([1, 2])
            with col1:
                login_btn = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                if st.form_submit_button("Forgot password?", use_container_width=True):
                    st.info("Please contact your system administrator")

            if login_btn:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    response = make_authenticated_request(
                        "POST",
                        "/auth/login",
                        json={"username": username, "password": password}
                    )

                    if response and response.ok:
                        data = response.json()
                        logger.info(f"Login successful. Token: {data['access_token'][:10]}...")
                        st.session_state.token = data['access_token']
                        st.session_state.current_user = data['user']
                        st.session_state.token_expiry = datetime.utcnow() + timedelta(seconds=data['expires_in'])
                        st.success("✅ Login successful")
                        time.sleep(1)
                        st.rerun()
                    elif response:
                        display_error(response)


def user_menu() -> None:
    """Enhanced sidebar navigation with user info"""
    with st.sidebar:
        if st.session_state.current_user:
            # User profile card
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h3 style="margin-top:0;">👋 Welcome, {st.session_state.current_user['username']}</h3>
                    <p><strong>Role:</strong> {st.session_state.current_user['role'].capitalize()}</p>
                    <p><strong>Email:</strong> {st.session_state.current_user.get('email', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

            # Navigation menu
            st.markdown("## Navigation")
            menu_options = {
                "Dashboard": "📊 Dashboard",
                "Clients": "👥 Clients",
                "Programs": "🏥 Programs",
                "Visits": "📅 Visits",
                "Reports": "📈 Reports"
            }

            if st.session_state.current_user['role'] == 'admin':
                menu_options["Admin"] = "⚙️ Admin"

            st.session_state.menu_choice = st.radio(
                "Menu",
                options=list(menu_options.values()),
                key="main_menu"
            )

            # Get the key for the selected menu option
            selected_key = [k for k, v in menu_options.items() if v == st.session_state.menu_choice][0]
            st.session_state.menu_choice = selected_key

            # Dark mode toggle
            st.session_state.dark_mode = st.toggle(
                "Dark Mode",
                value=st.session_state.dark_mode,
                help="Toggle dark/light mode"
            )

            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        else:
            st.warning("Please log in to access the system")


def dashboard_page() -> None:
    """Enhanced dashboard with metrics and visualizations"""
    st.title("📊 Dashboard Overview")

    # Fetch stats from API
    response = make_authenticated_request("GET", "/stats")

    if response and response.status_code == 200:
        stats = response.json()

        # Metrics cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Clients", stats.get('total_clients', 0), help="All active clients in the system")
        with col2:
            st.metric("Active Programs", stats.get('active_programs', 0), help="Currently available health programs")
        with col3:
            st.metric("Recent Visits", stats.get('visits_last_7_days', 0), "7 days", help="Visits in the last week")
        with col4:
            st.metric("Upcoming Appointments", stats.get('upcoming_appointments', 0), help="Scheduled appointments")

        st.divider()

        # Recent activity section
        st.subheader("Recent Activity")

        # Placeholder for charts (would be replaced with real data)
        tab1, tab2 = st.tabs(["Client Registrations", "Program Enrollment"])

        with tab1:
            st.area_chart({
                'Last 7 Days': [5, 7, 8, 6, 9, 10, 12],
                'Previous Week': [4, 6, 7, 5, 8, 7, 9]
            })
            st.caption("Client registrations over time")

        with tab2:
            if stats.get('most_popular_program'):
                st.bar_chart({
                    'Enrollments': [stats['most_popular_program']['enrollments']],
                    'Program': [stats['most_popular_program']['name']]
                })
                st.caption("Most popular health program")
            else:
                st.info("No program enrollment data available")

    elif response:
        display_error(response)


def client_management_page() -> None:
    """Enhanced client management interface"""
    st.title("👥 Client Management")

    # Tabbed interface
    tab1, tab2, tab3 = st.tabs(["Search Clients", "Register Client", "Client Details"])

    with tab1:
        st.subheader("Search Clients")

        # Search form
        with st.form("search_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input(
                    "Search by name, phone, or email",
                    placeholder="Enter search terms",
                    key="client_search_query"
                )
            with col2:
                st.form_submit_button("🔍 Search", use_container_width=True)

        if search_query:
            response = make_authenticated_request(
                "GET",
                f"/clients?query={search_query}"
            )

            if response and response.status_code == 200:
                clients = response.json().get('data', [])

                if not clients:
                    st.info("No clients found matching your search")
                else:
                    for client in clients:
                        with st.expander(f"{client['first_name']} {client['last_name']}"):
                            display_client_card(client)
            elif response:
                display_error(response)

    with tab2:
        st.subheader("Register New Client")
        client_registration_form()

    with tab3:
        if st.session_state.view_client_id:
            display_client_details(st.session_state.view_client_id)
        else:
            st.info("Select a client to view details")


def client_registration_form() -> None:
    """Enhanced client registration form"""
    with st.form("client_registration", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name*", placeholder="John")
            last_name = st.text_input("Last Name*", placeholder="Doe")
            dob = st.date_input("Date of Birth*", max_value=datetime.now().date())

        with col2:
            gender = st.selectbox(
                "Gender*",
                options=["Male", "Female", "Other", "Prefer not to say"],
                index=0
            )
            phone = st.text_input("Phone Number*", placeholder="+1234567890")
            email = st.text_input("Email", placeholder="john.doe@example.com")

        # Additional information in expander
        with st.expander("Additional Information"):
            address = st.text_area("Address", placeholder="123 Main St, City")
            emergency_contact = st.text_input("Emergency Contact Name")
            emergency_phone = st.text_input("Emergency Contact Phone")
            notes = st.text_area("Notes")

        # Form submission
        submitted = st.form_submit_button(
            "Register Client",
            type="primary",
            use_container_width=True
        )

        if submitted:
            if not all([first_name, last_name, phone]):
                st.error("Please fill in all required fields (marked with *)")
            else:
                payload = {
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "dob": dob.strftime("%Y-%m-%d"),
                    "gender": gender.lower(),
                    "phone": phone.strip(),
                    "email": email.strip() if email else None,
                    "address": address.strip() if address else None,
                    "emergency_contact_name": emergency_contact.strip() if emergency_contact else None,
                    "emergency_contact_phone": emergency_phone.strip() if emergency_phone else None,
                    "notes": notes.strip() if notes else None
                }

                response = make_authenticated_request(
                    "POST",
                    "/clients",
                    json=payload
                )

                if response and response.status_code == 201:
                    st.success("✅ Client registered successfully")
                    time.sleep(1)
                    st.session_state.menu_choice = "Clients"
                    st.rerun()
                elif response:
                    display_error(response)


def display_client_card(client: ClientData) -> None:
    """Display client information in a card format"""
    st.markdown(f"""
    <div class="card">
        <h4 style="margin-top:0;">{client['first_name']} {client['last_name']}</h4>
        <p><strong>Phone:</strong> {client['phone']}</p>
        <p><strong>Email:</strong> {client.get('email', 'N/A')}</p>
        <p><strong>DOB:</strong> {client.get('dob', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("View Full Profile", key=f"view_{client['id']}"):
        st.session_state.view_client_id = client['id']
        st.rerun()


def display_client_details(client_id: str) -> None:
    """Display detailed client information"""
    response = make_authenticated_request("GET", f"/clients/{client_id}")

    if response and response.status_code == 200:
        client = response.json()

        st.subheader(f"{client['first_name']} {client['last_name']}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Personal Information")
            st.markdown(f"""
            - **Phone:** {client['phone']}
            - **Email:** {client.get('email', 'N/A')}
            - **Date of Birth:** {client.get('dob', 'N/A')}
            - **Gender:** {client.get('gender', 'N/A').capitalize()}
            - **Address:** {client.get('address', 'N/A')}
            """)

        with col2:
            st.markdown("### Emergency Contact")
            st.markdown(f"""
            - **Name:** {client.get('emergency_contact_name', 'N/A')}
            - **Phone:** {client.get('emergency_contact_phone', 'N/A')}
            """)

        st.markdown("### Notes")
        st.markdown(client.get('notes', 'No notes available'))

        st.divider()

        # Client programs
        st.markdown("### Enrolled Programs")
        program_response = make_authenticated_request("GET", f"/clients/{client_id}/programs")

        if program_response and program_response.status_code == 200:
            programs = program_response.json()

            if not programs:
                st.info("Client is not enrolled in any programs")
            else:
                for program in programs:
                    st.markdown(f"""
                    - **{program.get('program', {}).get('name', 'Unknown')}**  
                      Status: {program.get('status', 'N/A').capitalize()}  
                      Enrollment Date: {program.get('enrollment_date', 'N/A')}
                    """)
        elif program_response:
            display_error(program_response)

        # Back button
        if st.button("← Back to Client List"):
            st.session_state.view_client_id = None
            st.rerun()

    elif response:
        display_error(response)


# --- Main Application Flow ---
def main():
    # Initialize app
    load_css()
    initialize_session()

    # Authentication flow
    if not st.session_state.token:
        login_form()
        if not st.session_state.token:
            st.warning("🔒 Please login to access the system")
            return

    # Render user menu
    user_menu()

    # Page routing
    if st.session_state.menu_choice == "Dashboard":
        dashboard_page()
    elif st.session_state.menu_choice == "Clients":
        client_management_page()
    elif st.session_state.menu_choice == "Admin":
        if st.session_state.current_user['role'] != 'admin':
            st.error("⛔ Admin access required")
        else:
            st.title("⚙️ Admin Dashboard")
            # Admin functionality would go here

    # Footer
    st.divider()
    st.markdown(
        f"""
        <div style="text-align: center; color: gray; margin-top: 2rem;">
            © 2023 {APP_NAME} | v{APP_VERSION} | 
            <a href="#" style="color: gray;">Help</a> | 
            <a href="#" style="color: gray;">Privacy</a> | 
            <a href="#" style="color: gray;">Terms</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()