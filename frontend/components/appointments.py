import streamlit as st
import pandas as pd
from utils.helpers import make_request, format_datetime, date_range_filter
from datetime import datetime


def get_appointments():
    user_role = st.session_state.current_user['role']
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']

    st.title("Appointment Management")
    st.markdown("---")

    # Tab navigation
    tab1, tab2 = st.tabs(["View Appointments", "Schedule Appointment"])

    with tab1:
        st.subheader("Appointment Records")

        # Filters
        with st.expander("Filters", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                client_id = st.text_input("Filter by Client ID")
            with col2:
                status = st.selectbox(
                    "Filter by status",
                    ["All", "Scheduled", "Completed", "Cancelled"],
                    index=0
                )

            start_date, end_date = date_range_filter("appointments")

        # Fetch appointments with filters
        params = {
            "client_id": client_id if client_id else None,
            "status": status.lower() if status != "All" else None,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        appointments = make_request("GET", "/appointments", params=params)

        if appointments and appointments['data']:
            # Prepare data for display
            df = pd.DataFrame(appointments['data'])
            df['date'] = df['date'].apply(format_datetime)

            # Display table
            display_columns = [
                "id", "client_id", "date", "reason",
                "duration_minutes", "status", "notes"
            ]

            st.dataframe(
                df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "client_id": "Client ID",
                    "date": "Date & Time",
                    "reason": "Reason",
                    "duration_minutes": "Duration (min)",
                    "status": "Status",
                    "notes": "Notes"
                }
            )
        else:
            st.info("No appointments found matching your criteria")

    with tab2:
        st.subheader("Schedule New Appointment")
        with st.form("create_appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                client_id = st.text_input("Client ID*")
            with col2:
                appointment_date = st.date_input("Date*")
                appointment_time = st.time_input("Time*")

            combined_datetime = datetime.combine(appointment_date, appointment_time)

            col1, col2 = st.columns(2)
            with col1:
                duration = st.number_input(
                    "Duration (minutes)*",
                    min_value=15,
                    max_value=120,
                    value=30,
                    step=15
                )
            with col2:
                status = st.selectbox(
                    "Status",
                    ["Scheduled", "Completed", "Cancelled"],
                    index=0
                )

            reason = st.text_input("Reason*")
            notes = st.text_area("Notes")

            if st.form_submit_button("Schedule Appointment", type="primary"):
                if not all([client_id, reason]):
                    st.error("Please fill in all required fields (*)")
                else:
                    appointment_data = {
                        "client_id": client_id,
                        "date": combined_datetime.isoformat(),
                        "duration_minutes": duration,
                        "reason": reason,
                        "status": status.lower(),
                        "notes": notes
                    }

                    response = make_request("POST", "/appointments", data=appointment_data)
                    if response:
                        st.success("Appointment scheduled successfully!")
                        st.rerun()

        st.markdown("---")
        st.subheader("Update Appointment")

        appointment_id = st.text_input("Enter Appointment ID to update")
        if appointment_id:
            appointment = make_request("GET", f"/appointments/{appointment_id}")
            if appointment:
                with st.form("update_appointment_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input(
                            "Date",
                            value=datetime.strptime(appointment['date'], "%Y-%m-%dT%H:%M:%S")
                        )
                        new_time = st.time_input(
                            "Time",
                            value=datetime.strptime(appointment['date'], "%Y-%m-%dT%H:%M:%S").time()
                        )
                    with col2:
                        duration = st.number_input(
                            "Duration (minutes)",
                            min_value=15,
                            max_value=120,
                            value=appointment['duration_minutes'],
                            step=15
                        )

                    combined_datetime = datetime.combine(new_date, new_time)

                    reason = st.text_input(
                        "Reason",
                        value=appointment['reason']
                    )

                    status = st.selectbox(
                        "Status",
                        ["Scheduled", "Completed", "Cancelled"],
                        index=["scheduled", "completed", "cancelled"].index(appointment['status'])
                    )

                    notes = st.text_area(
                        "Notes",
                        value=appointment['notes'] or ""
                    )

                    if st.form_submit_button("Update Appointment", type="primary"):
                        update_data = {
                            "date": combined_datetime.isoformat(),
                            "duration_minutes": duration,
                            "reason": reason,
                            "status": status.lower(),
                            "notes": notes
                        }

                        response = make_request("PUT", f"/appointments/{appointment_id}", data=update_data)
                        if response:
                            st.success("Appointment updated successfully!")
                            st.rerun()
            else:
                st.error("Appointment not found")