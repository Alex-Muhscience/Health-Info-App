import streamlit as st
import pandas as pd
from utils.helpers import make_request, format_datetime
from datetime import datetime, timedelta


def get_stats():
    """Display dashboard with system statistics and recent activity"""
    # Check user permissions
    user_role = st.session_state.get('current_user', {}).get('role')
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']
    
    if user_role not in allowed_roles:
        st.error("You don't have permission to view this dashboard")
        return

    st.title("Dashboard")
    st.markdown("---")

    # Fetch stats with error handling
    with st.spinner("Loading dashboard data..."):
        stats = make_request("GET", "/dashboard/stats")

    if not stats:
        st.error("Failed to load dashboard data. Please check your connection and try again.")
        return

    # Display stats cards in a more organized layout
    st.subheader("📊 System Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total Active Clients", 
            value=stats.get('total_clients', 0),
            help="Number of currently active clients in the system"
        )
    with col2:
        st.metric(
            label="Active Programs", 
            value=stats.get('active_programs', 0),
            help="Number of currently active programs"
        )
    with col3:
        st.metric(
            label="New Clients (30 days)", 
            value=stats.get('new_clients_last_30_days', 0),
            help="New clients registered in the last 30 days"
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(
            label="Recent Visits (7 days)", 
            value=stats.get('visits_last_7_days', 0),
            help="Total visits in the last 7 days"
        )
    with col5:
        st.metric(
            label="Upcoming Appointments", 
            value=stats.get('upcoming_appointments', 0),
            help="Scheduled appointments for the next 7 days"
        )
    with col6:
        popular_program = stats.get('most_popular_program', {})
        program_name = popular_program.get('name') or "N/A"
        enrollments = popular_program.get('enrollments', 0)
        
        st.metric(
            label="Most Popular Program",
            value=program_name,
            help=f"{enrollments} total enrollments"
        )

    st.markdown("---")

    # Recent activity sections
    st.subheader("📅 Recent Activity")
    
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Recent Appointments**")
        
        # Calculate date range for recent appointments
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        appointments_response = make_request(
            "GET",
            "/appointments",
            params={
                "start_date": start_date,
                "per_page": 5
            }
        )

        if appointments_response and appointments_response.get('data'):
            appointments_data = appointments_response['data']
            
            # Process appointments data
            processed_appointments = []
            for apt in appointments_data:
                processed_appointments.append({
                    'Date': format_datetime(apt.get('date', '')),
                    'Client': apt.get('client_name', f"ID: {apt.get('client_id', 'Unknown')}"),
                    'Reason': apt.get('reason', 'General appointment'),
                    'Status': apt.get('status', 'scheduled').title()
                })
            
            if processed_appointments:
                df_appointments = pd.DataFrame(processed_appointments)
                st.dataframe(
                    df_appointments,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No recent appointments found")
        else:
            st.info("No recent appointments found")

    with col2:
        st.write("**Recent Visits**")
        
        visits_response = make_request(
            "GET",
            "/visits",
            params={
                "start_date": start_date,
                "per_page": 5
            }
        )

        if visits_response and visits_response.get('data'):
            visits_data = visits_response['data']
            
            # Process visits data
            processed_visits = []
            for visit in visits_data:
                processed_visits.append({
                    'Date': format_datetime(visit.get('visit_date', '')),
                    'Client': visit.get('client_name', f"ID: {visit.get('client_id', 'Unknown')}"),
                    'Purpose': visit.get('purpose', 'General visit'),
                    'Type': visit.get('visit_type', 'consultation').title()
                })
            
            if processed_visits:
                df_visits = pd.DataFrame(processed_visits)
                st.dataframe(
                    df_visits,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No recent visits found")
        else:
            st.info("No recent visits found")

    # Quick actions section
    st.markdown("---")
    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Schedule New Appointment", use_container_width=True):
            st.session_state.appointment_action = "create"
            st.switch_page("components/appointments.py")

    with col2:
        if st.button("👤 Register New Client", use_container_width=True):
            st.session_state.client_action = "create"
            st.switch_page("pages/clients.py")

    with col3:
        if st.button("🏥 Record New Visit", use_container_width=True):
            st.session_state.visit_action = "create"
            st.switch_page("pages/visits.py")

    # Additional system info
    st.markdown("---")
    with st.expander("ℹ️ System Information"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Last Updated:**")
            st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with col2:
            st.write("**User Role:**")
            st.write(user_role.title() if user_role else "Unknown")


# Call the function when this module is run
if __name__ == "__main__":
    get_stats()