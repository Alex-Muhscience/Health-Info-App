import streamlit as st
from streamlit_option_menu import option_menu
from components.auth import show_auth_page
from components.dashboard import get_stats
from components.clients import get_clients
from components.appointments import get_appointments
from components.visits import get_visits
from components.programs import get_programs

from frontend.utils.helpers import load_css

# Page configuration
st.set_page_config(
    page_title="Healthcare Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# App state management
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'token' not in st.session_state:
    st.session_state.token = None


# Main app logic
def main():
    if not st.session_state.authenticated:
        show_auth_page()
    else:
        show_main_app()


def show_main_app():
    # Sidebar navigation
    with st.sidebar:
        st.image("D:/Personal_Projects/Health App/assets/logo.png")
        st.write(f"Welcome, **{st.session_state.current_user['username']}**")
        st.write(f"Role: **{st.session_state.current_user['role'].capitalize()}**")

        menu_options = [
            "Dashboard", "Clients", "Appointments",
            "Visits", "Programs"
        ]

        # Filter options based on user role
        if st.session_state.current_user['role'] in ['nurse', 'receptionist']:
            menu_options = ["Dashboard", "Clients", "Appointments", "Visits"]
        elif st.session_state.current_user['role'] == 'doctor':
            menu_options = ["Dashboard", "Clients", "Appointments", "Visits", "Programs"]
        elif st.session_state.current_user['role'] == 'admin':
            menu_options = ["Dashboard", "Clients", "Appointments", "Visits", "Programs"]

        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=["house", "people", "calendar", "journal", "clipboard"],
            default_index=0,
            styles={
                "container": {"padding": "0!important"},
                "icon": {"color": "white", "font-size": "16px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#166088"},
            }
        )

        st.markdown("---")
        if st.button("Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.token = None
            st.rerun()

    # Main content area
    if selected == "Dashboard":
        get_stats()
    elif selected == "Clients":
        get_clients()
    elif selected == "Appointments":
        get_appointments()
    elif selected == "Visits":
        get_visits()
    elif selected == "Programs":
        get_programs()


if __name__ == "__main__":
    main()
