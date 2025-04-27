import streamlit as st
import pandas as pd
from utils.helpers import make_request, format_datetime
from datetime import datetime, timedelta


def get_stats():
    user_role = st.session_state.current_user['role']
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']

    st.title("Dashboard")
    st.markdown("---")

    # Fetch stats
    stats = make_request("GET", "/stats")

    if not stats:
        st.error("Failed to load dashboard data")
        return

    # Display stats cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Active Clients", stats['total_clients'])
    with col2:
        st.metric("Active Programs", stats['active_programs'])
    with col3:
        st.metric("New Clients (30 days)", stats['new_clients_last_30_days'])

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Recent Visits (7 days)", stats['visits_last_7_days'])
    with col5:
        st.metric("Upcoming Appointments", stats['upcoming_appointments'])
    with col6:
        st.metric(
            "Most Popular Program",
            stats['most_popular_program']['name'] or "N/A",
            help=f"{stats['most_popular_program']['enrollments']} enrollments"
        )

    st.markdown("---")

    # Recent activity sections
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent Appointments")
        appointments = make_request(
            "GET",
            "/appointments",
            params={
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "per_page": 5
            }
        )

        if appointments and appointments['data']:
            df = pd.DataFrame(appointments['data'])
            df['date'] = df['date'].apply(format_datetime)
            st.dataframe(
                df[['date', 'client_id', 'reason', 'status']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "client_id": "Client ID",
                    "date": "Date",
                    "reason": "Reason",
                    "status": "Status"
                }
            )
        else:
            st.info("No recent appointments found")

    with col2:
        st.subheader("Recent Visits")
        visits = make_request(
            "GET",
            "/visits",
            params={
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "per_page": 5
            }
        )

        if visits and visits['data']:
            df = pd.DataFrame(visits['data'])
            df['visit_date'] = df['visit_date'].apply(format_datetime)
            st.dataframe(
                df[['visit_date', 'client_id', 'purpose', 'visit_type']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "client_id": "Client ID",
                    "visit_date": "Date",
                    "purpose": "Purpose",
                    "visit_type": "Type"
                }
            )
        else:
            st.info("No recent visits found")

    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 Schedule New Appointment"):
            st.session_state.appointment_action = "create"
            st.switch_page("pages/appointments.py")

    with col2:
        if st.button("👤 Register New Client"):
            st.session_state.client_action = "create"
            st.switch_page("pages/clients.py")

    with col3:
        if st.button("🏥 Record New Visit"):
            st.session_state.visit_action = "create"
            st.switch_page("pages/visits.py")