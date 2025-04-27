import streamlit as st
import pandas as pd
from frontend.utils.helpers import make_request, format_datetime, date_range_filter
from datetime import datetime

VISIT_TYPES = [
    'consultation', 'follow_up', 'emergency',
    'vaccination', 'test', 'procedure', 'other'
]


def get_visits():
    user_role = st.session_state.current_user['role']
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']

    if user_role not in allowed_roles:
        st.warning("You don't have permission to access this section")
        return

    st.title("Visit Management")
    st.markdown("---")

    # Tab navigation
    tab1, tab2 = st.tabs(["View Visits", "Record Visit"])

    with tab1:
        st.subheader("Visit Records")

        # Filters
        with st.expander("Filters", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                client_id = st.text_input("Filter by Client ID")
            with col2:
                visit_type = st.selectbox(
                    "Filter by visit type",
                    ["All"] + [vt.capitalize() for vt in VISIT_TYPES],
                    index=0
                )

            start_date, end_date = date_range_filter("visits")

        # Fetch visits with filters
        params = {
            "client_id": client_id if client_id else None,
            "type": visit_type.lower() if visit_type != "All" else None,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        visits = make_request("GET", "/visits", params=params)

        if visits and visits['data']:
            # Prepare data for display
            df = pd.DataFrame(visits['data'])
            df['visit_date'] = df['visit_date'].apply(format_datetime)

            # Display table
            display_columns = [
                "id", "client_id", "visit_date", "visit_type",
                "purpose", "diagnosis", "treatment"
            ]

            st.dataframe(
                df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "client_id": "Client ID",
                    "visit_date": "Date & Time",
                    "visit_type": "Type",
                    "purpose": "Purpose",
                    "diagnosis": "Diagnosis",
                    "treatment": "Treatment"
                }
            )
        else:
            st.info("No visits found matching your criteria")

    with tab2:
        st.subheader("Record New Visit")
        with st.form("create_visit_form"):
            client_id = st.text_input("Client ID*")

            col1, col2 = st.columns(2)
            with col1:
                visit_date = st.date_input("Visit Date*")
                visit_time = st.time_input("Visit Time*")
            with col2:
                visit_type = st.selectbox(
                    "Visit Type*",
                    [vt.capitalize() for vt in VISIT_TYPES],
                    index=0
                )

            combined_datetime = datetime.combine(visit_date, visit_time)

            purpose = st.text_input("Purpose*")
            diagnosis = st.text_input("Diagnosis")
            treatment = st.text_input("Treatment")
            notes = st.text_area("Notes")

            if st.form_submit_button("Record Visit", type="primary"):
                if not all([client_id, purpose, visit_type]):
                    st.error("Please fill in all required fields (*)")
                elif combined_datetime > datetime.now():
                    st.error("Visit date cannot be in the future")
                else:
                    visit_data = {
                        "client_id": client_id,
                        "visit_date": combined_datetime.isoformat(),
                        "type": visit_type.lower(),
                        "purpose": purpose,
                        "diagnosis": diagnosis,
                        "treatment": treatment,
                        "notes": notes
                    }

                    response = make_request("POST", f"/visits/{client_id}", data=visit_data)
                    if response:
                        st.success("Visit recorded successfully!")
                        st.rerun()

        st.markdown("---")
        st.subheader("Update Visit")

        visit_id = st.text_input("Enter Visit ID to update")
        if visit_id:
            visit = make_request("GET", f"/visits/{visit_id}")
            if visit:
                with st.form("update_visit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input(
                            "Visit Date",
                            value=datetime.strptime(visit['visit_date'], "%Y-%m-%dT%H:%M:%S")
                        )
                        new_time = st.time_input(
                            "Visit Time",
                            value=datetime.strptime(visit['visit_date'], "%Y-%m-%dT%H:%M:%S").time()
                        )
                    with col2:
                        visit_type = st.selectbox(
                            "Visit Type",
                            [vt.capitalize() for vt in VISIT_TYPES],
                            index=VISIT_TYPES.index(visit['visit_type'])
                        )

                    combined_datetime = datetime.combine(new_date, new_time)

                    purpose = st.text_input(
                        "Purpose",
                        value=visit['purpose']
                    )
                    diagnosis = st.text_input(
                        "Diagnosis",
                        value=visit['diagnosis'] or ""
                    )
                    treatment = st.text_input(
                        "Treatment",
                        value=visit['treatment'] or ""
                    )
                    notes = st.text_area(
                        "Notes",
                        value=visit['notes'] or ""
                    )

                    if st.form_submit_button("Update Visit", type="primary"):
                        update_data = {
                            "visit_date": combined_datetime.isoformat(),
                            "type": visit_type.lower(),
                            "purpose": purpose,
                            "diagnosis": diagnosis,
                            "treatment": treatment,
                            "notes": notes
                        }

                        response = make_request("PUT", f"/visits/{visit_id}", data=update_data)
                        if response:
                            st.success("Visit updated successfully!")
                            st.rerun()
            else:
                st.error("Visit not found")