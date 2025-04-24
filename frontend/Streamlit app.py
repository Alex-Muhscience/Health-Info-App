import streamlit as st
import requests
from datetime import datetime
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
    # Get the current file's directory
    current_dir = Path(__file__).parent

    # Construct the path to the CSS file
    css_file = current_dir / "styles" / "style.css"

    # Check if file exists
    if not css_file.exists():
        st.error(f"CSS file not found at: {css_file}")
        return

    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
        {"icon": "⚙️", "label": "System Settings", "key": "settings"}
    ]

    choice = st.radio(
        "Navigate to:",
        options=[item["label"] for item in menu],
        format_func=lambda x: f"{next(item['icon'] for item in menu if item['label'] == x)} {x}",
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("""
        <div style="font-size: 0.8rem; color: #e0e0e0;">
            <p>Version 1.0.0</p>
            <p>Last updated: {}</p>
        </div>
    """.format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)

# Main content
if choice == "Dashboard":
    st.subheader("System Overview")

    # Stats cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="card">
                <h3>Total Clients</h3>
                <p style="font-size: 2rem; margin: 0.5rem 0;">1,248</p>
                <p style="color: #2e7d32; font-size: 0.9rem;">↑ 12% from last month</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="card">
                <h3>Active Programs</h3>
                <p style="font-size: 2rem; margin: 0.5rem 0;">7</p>
                <p style="color: #2e7d32; font-size: 0.9rem;">TB, HIV, Malaria, etc.</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="card">
                <h3>Recent Activity</h3>
                <p style="font-size: 0.9rem;">5 new enrollments today</p>
                <p style="font-size: 0.9rem;">3 client registrations</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style="margin-top: 1rem;">
            <h3>Quick Actions</h3>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <button class="quick-action" onclick="window.location.href='#register'">Register New Client</button>
                <button class="quick-action" onclick="window.location.href='#enroll'">Process Enrollment</button>
                <button class="quick-action" onclick="window.location.href='#reports'">Generate Reports</button>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif choice == "Register Client":
    st.subheader("Client Registration")

    with st.form("registration_form"):
        cols = st.columns(2)
        with cols[0]:
            first_name = st.text_input("First Name*", placeholder="John", help="Enter client's first name")
        with cols[1]:
            last_name = st.text_input("Last Name*", placeholder="Doe", help="Enter client's last name")

        cols = st.columns(3)
        with cols[0]:
            dob = st.date_input("Date of Birth*", max_value=datetime.now(), help="Client's date of birth")
        with cols[1]:
            gender = st.selectbox("Gender*", ["", "Male", "Female", "Other", "Prefer not to say"], help="Client's gender identity")
        with cols[2]:
            phone = st.text_input("Phone Number*", placeholder="+1234567890", help="Primary contact number")

        address = st.text_input("Address", placeholder="123 Main St, City", help="Current residential address")

        notes = st.text_area("Additional Notes", height=100, placeholder="Any relevant health information or notes...")

        submitted = st.form_submit_button("Register Client", type="primary")
        if submitted:
            if first_name and last_name and dob and gender and phone:
                # Simulate API call
                client_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "dob": str(dob),
                    "gender": gender,
                    "phone": phone,
                    "address": address,
                    "notes": notes
                }
                try:
                    response = requests.post(f"{BASE_URL}/clients", json=client_data)
                    if response.status_code == 200:
                        st.success("Client registered successfully!")
                        st.balloons()
                        client_id = response.json().get("id")
                        st.markdown(f"""
                            <div class="card">
                                <h3>Registration Complete</h3>
                                <p>Client ID: <strong>{client_id}</strong></p>
                                <p>Name: <strong>{first_name} {last_name}</strong></p>
                                <p>Please note this ID for future reference.</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Registration failed. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please try again later.")
            else:
                st.warning("Please fill all required fields (*)")

elif choice == "Enroll Client":
    st.subheader("Client Program Enrollment")

    with st.expander("ℹ️ How to enroll a client", expanded=True):
        st.markdown("""
            1. Enter the client's ID (found in their profile)
            2. Select the programs to enroll in
            3. Choose an enrollment date
            4. Click "Enroll Client" to complete the process
        """)

    with st.form("enrollment_form"):
        client_id = st.text_input("Client ID*", placeholder="Enter client ID", help="The unique ID of the client")

        st.markdown("**Select Programs***")
        programs = st.multiselect(
            "Available Programs",
            ["TB Treatment", "HIV Care", "Malaria Prevention", "Maternal Health",
             "Child Immunization", "Nutrition Support", "Chronic Disease Management"],
            label_visibility="collapsed",
            help="Select one or more programs"
        )

        enrollment_date = st.date_input("Enrollment Date*", datetime.now(), help="Date when enrollment begins")

        submitted = st.form_submit_button("Enroll Client", type="primary")
        if submitted:
            if client_id and programs and enrollment_date:
                try:
                    response = requests.post(
                        f"{BASE_URL}/clients/{client_id}/enroll",
                        json={
                            "programs": programs,
                            "enrollment_date": str(enrollment_date)
                        }
                    )
                    if response.status_code == 200:
                        st.success(f"Client enrolled in {len(programs)} program(s) successfully!")
                        st.json(response.json())
                    else:
                        st.error("Enrollment failed. Please check the client ID.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please try again later.")
            else:
                st.warning("Please fill all required fields (*)")

elif choice == "Search Clients":
    st.subheader("Client Search")

    search_tab, advanced_tab = st.tabs(["🔍 Quick Search", "🔎 Advanced Search"])

    with search_tab:
        with st.form("quick_search"):
            query = st.text_input("Search by name, ID, or phone", placeholder="Enter search term", help="Search for clients by any identifier")
            cols = st.columns(2)
            with cols[0]:
                submitted = st.form_submit_button("Search", type="primary")
            with cols[1]:
                clear = st.form_submit_button("Clear")

            if submitted and query:
                try:
                    response = requests.get(f"{BASE_URL}/clients", params={"query": query})
                    if response.status_code == 200:
                        results = response.json()
                        if results:
                            st.success(f"Found {len(results)} matching clients")
                            for client in results:
                                with st.expander(f"{client.get('name', 'Unknown')} (ID: {client.get('id', 'N/A')})"):
                                    cols = st.columns(3)
                                    with cols[0]:
                                        st.markdown("**Contact Info**")
                                        st.write(f"📞 {client.get('phone', 'N/A')}")
                                        st.write(f"🏠 {client.get('address', 'No address')}")
                                    with cols[1]:
                                        st.markdown("**Programs**")
                                        if client.get("programs"):
                                            for prog in client["programs"]:
                                                st.write(f"- {prog}")
                                        else:
                                            st.write("No programs")
                                    with cols[2]:
                                        st.markdown("**Actions**")
                                        st.button("View Profile", key=f"view_{client['id']}")
                                        st.button("Enroll in Program", key=f"enroll_{client['id']}")
                        else:
                            st.info("No clients found matching your search")
                    else:
                        st.error("Search failed. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please try again later.")

    with advanced_tab:
        with st.form("advanced_search"):
            cols = st.columns(2)
            with cols[0]:
                first_name = st.text_input("First Name")
                gender = st.selectbox("Gender", ["Any", "Male", "Female", "Other"])
            with cols[1]:
                last_name = st.text_input("Last Name")
                program = st.selectbox("Enrolled in Program", ["Any", "TB", "HIV", "Malaria", "Other"])

            date_cols = st.columns(2)
            with date_cols[0]:
                reg_from = st.date_input("Registered from", value=None)
            with date_cols[1]:
                reg_to = st.date_input("Registered to", value=None)

            submitted = st.form_submit_button("Advanced Search", type="primary")
            if submitted:
                st.info("Advanced search functionality would be implemented here")

elif choice == "Client Profile":
    st.subheader("Client Profile")

    client_id = st.text_input("Enter Client ID", key="profile_search", placeholder="Enter the client's unique ID")

    if client_id:
        try:
            response = requests.get(f"{BASE_URL}/clients/{client_id}")
            if response.status_code == 200:
                client = response.json()

                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image("https://via.placeholder.com/150?text=Profile", width=150, use_column_width=True, output_format="PNG")
                    with cols[1]:
                        st.markdown(f"# {client.get('name', 'Unknown Client')}")
                        st.markdown(f"**ID:** {client.get('id', 'N/A')} | **Phone:** {client.get('phone', 'N/A')}")
                        st.markdown(f"**Address:** {client.get('address', 'No address')}")

                tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "🏥 Programs", "📅 Visits", "📂 Documents"])

                with tab1:
                    cols = st.columns(3)
                    with cols[0]:
                        st.markdown("**Personal Information**")
                        st.write(f"🎂 DOB: {client.get('dob', 'Unknown')}")
                        st.write(f"🧑 Gender: {client.get('gender', 'Unknown')}")
                    with cols[1]:
                        st.markdown("**Contact Details**")
                        st.write(f"📞 Phone: {client.get('phone', 'N/A')}")
                        st.write(f"✉️ Email: {client.get('email', 'N/A')}")
                    with cols[2]:
                        st.markdown("**Emergency Contact**")
                        st.write(f"👤 Name: {client.get('emergency_contact', {}).get('name', 'N/A')}")
                        st.write(f"📱 Phone: {client.get('emergency_contact', {}).get('phone', 'N/A')}")

                with tab2:
                    if client.get("programs"):
                        for program in client["programs"]:
                            with st.expander(f"{program.get('name', 'Unknown Program')} - {program.get('status', 'Active')}"):
                                st.write(f"📅 Enrolled: {program.get('enrollment_date', 'Unknown')}")
                                st.write(f"📊 Progress:")
                                st.progress(program.get('progress', 0))
                                if program.get('notes'):
                                    st.write(f"📝 Notes: {program.get('notes')}")
                    else:
                        st.info("This client is not enrolled in any programs")
                        st.button("Enroll in Program", key="enroll_from_profile")

                with tab3:
                    st.info("Visit history would be displayed here")
                    st.button("Record New Visit", key="new_visit")

                with tab4:
                    st.info("Client documents would be listed here")
                    st.button("Upload Document", key="upload_doc")

            else:
                st.error("Client not found. Please check the ID.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the server. Please try again later.")

# Footer
st.markdown("---")
st.markdown("""
    <div class="footer">
        <p>© 2023 Health Information Management System | For authorized use only</p>
        <p>Need help? Contact <a href="mailto:support@healthsystem.org">support@healthsystem.org</a></p>
    </div>
""", unsafe_allow_html=True)

# Backend connection check
try:
    requests.get(f"{BASE_URL}/clients")
except requests.exceptions.ConnectionError:
    st.error("🚨 Cannot connect to the backend server! Please ensure the backend service is running.")
    st.stop()