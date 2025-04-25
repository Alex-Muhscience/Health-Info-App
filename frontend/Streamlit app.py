import streamlit as st
import requests
import time
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Health Info System",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

def load_css():
    style_path = Path(__file__).parent / "styles" / "style.css"
    with open(style_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

if 'token' not in st.session_state:
    st.session_state['token'] = None
    st.session_state['current_user'] = None
    st.session_state['menu'] = "Dashboard"

def make_authenticated_request(method, endpoint, **kwargs):
    headers = kwargs.pop('headers', {})
    if st.session_state.token:
        headers['Authorization'] = f"Bearer {st.session_state.token}"
    try:
        r = requests.request(method, f"{BASE_URL}{endpoint}", headers=headers, **kwargs)
        if r.status_code == 401:
            st.session_state['token'] = None
            st.session_state['current_user'] = None
            st.error("Session expired.")
            st.rerun()
        return r
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend server is not running!")
        return None

with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=Health+System", width=150)
    if not st.session_state['token']:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                res = requests.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": password})
                res.raise_for_status()
                data = res.json()
                st.session_state['token'] = data['token']
                st.session_state['current_user'] = data['user']
                st.success("Login successful!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error("Login failed.")
    else:
        st.success(f"Welcome {st.session_state['current_user']['username']}")
        if st.button("Logout"):
            st.session_state['token'] = None
            st.session_state['current_user'] = None
            st.rerun()
        st.subheader("Navigation")
        st.session_state['menu'] = st.radio("Menu", ["Dashboard", "Register Client", "Search Clients", "Programs"])

if not st.session_state['token']:
    st.warning("Login to use the system.")
else:
    choice = st.session_state['menu']
    if choice == "Dashboard":
        st.subheader("Dashboard")
        res = make_authenticated_request("GET", "/api/stats")
        if res and res.status_code == 200:
            stats = res.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Clients", stats['total_clients'], f"{stats['client_growth']}%")
            col2.metric("Programs", stats['active_programs'])
            col3.metric("Today's Registrations", stats['recent_registrations'])
        else:
            st.error("Unable to load dashboard.")

    elif choice == "Register Client":
        st.subheader("Register Client")
        with st.form("register_form"):
            fname = st.text_input("First Name")
            lname = st.text_input("Last Name")
            dob = st.date_input("DOB")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            submitted = st.form_submit_button("Register")
            if submitted:
                payload = {
                    "first_name": fname,
                    "last_name": lname,
                    "dob": dob.strftime("%Y-%m-%d"),
                    "gender": gender,
                    "phone": phone,
                    "email": email
                }
                r = make_authenticated_request("POST", "/api/clients/", json=payload)
                if r and r.status_code == 201:
                    st.success("Client registered.")
                else:
                    st.error("Registration failed.")

    elif choice == "Search Clients":
        st.subheader("Search Clients")
        query = st.text_input("Search query")
        if st.button("Search"):
            r = make_authenticated_request("GET", f"/api/clients?query={query}")
            if r and r.status_code == 200:
                results = r.json()
                for c in results:
                    st.markdown(f"**{c['first_name']} {c['last_name']}** - {c['phone']}")

    elif choice == "Programs":
        st.subheader("Available Programs")
        r = make_authenticated_request("GET", "/api/programs/")
        if r and r.status_code == 200:
            for prog in r.json():
                st.markdown(f"**{prog['name']}** - {prog.get('description', 'No description')}")
