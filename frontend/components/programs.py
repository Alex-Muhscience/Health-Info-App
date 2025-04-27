import streamlit as st
import pandas as pd
from utils.helpers import make_request


def get_programs():
    user_role = st.session_state.current_user['role']
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']

    if user_role not in allowed_roles:
        st.warning("You don't have permission to access this section")
        return
    st.title("Program Management")
    st.markdown("---")

    # Check user role for permissions
    user_role = st.session_state.current_user['role']
    if user_role not in ['admin', 'doctor']:
        st.warning("You don't have permission to access this section")
        return

    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["View Programs", "Manage Programs", "Enrollments"])

    with tab1:
        st.subheader("All Programs")

        # Filters
        with st.expander("Filters", expanded=False):
            search = st.text_input("Search by program name")
            active_only = st.checkbox("Show active programs only", value=True)

        # Fetch programs with filters
        params = {
            "search": search if search else None,
            "active_only": active_only
        }

        programs = make_request("GET", "/programs", params=params)

        if programs:
            # Display table
            display_columns = [
                "id", "name", "description",
                "duration_days", "is_active"
            ]

            st.dataframe(
                pd.DataFrame(programs)[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "name": "Program Name",
                    "description": "Description",
                    "duration_days": "Duration (days)",
                    "is_active": "Active"
                }
            )
        else:
            st.info("No programs found matching your criteria")

    with tab2:
        action = st.radio(
            "Select action",
            ["Create New Program", "Update Program"],
            horizontal=True
        )

        if action == "Create New Program":
            st.subheader("Create New Health Program")
            with st.form("create_program_form"):
                name = st.text_input("Program Name*")
                description = st.text_area("Description")
                duration = st.number_input(
                    "Duration (days)",
                    min_value=1,
                    max_value=365,
                    value=30
                )
                is_active = st.checkbox("Active", value=True)

                if st.form_submit_button("Create Program", type="primary"):
                    if not name:
                        st.error("Program name is required")
                    else:
                        program_data = {
                            "name": name,
                            "description": description,
                            "duration_days": duration,
                            "is_active": is_active
                        }

                        response = make_request("POST", "/programs", data=program_data)
                        if response:
                            st.success("Program created successfully!")
                            st.rerun()

        elif action == "Update Program":
            st.subheader("Update Program Information")
            program_id = st.text_input("Enter Program ID to update")

            if program_id:
                program = make_request("GET", f"/programs/{program_id}")
                if program:
                    with st.form("update_program_form"):
                        name = st.text_input(
                            "Program Name",
                            value=program['name']
                        )
                        description = st.text_area(
                            "Description",
                            value=program['description'] or ""
                        )
                        duration = st.number_input(
                            "Duration (days)",
                            min_value=1,
                            max_value=365,
                            value=program['duration_days'] or 30
                        )
                        is_active = st.checkbox(
                            "Active",
                            value=program['is_active']
                        )

                        if st.form_submit_button("Update Program", type="primary"):
                            update_data = {
                                "name": name,
                                "description": description,
                                "duration_days": duration,
                                "is_active": is_active
                            }

                            response = make_request("PUT", f"/programs/{program_id}", data=update_data)
                            if response:
                                st.success("Program updated successfully!")
                                st.rerun()
                else:
                    st.error("Program not found")

    with tab3:
        st.subheader("Program Enrollments")

        program_id = st.text_input("Enter Program ID to view enrollments")
        if program_id:
            enrollments = make_request(
                "GET",
                f"/programs/{program_id}/enrollments"
            )

            if enrollments:
                # Display enrollments
                df = pd.DataFrame(enrollments)

                # Get client details for each enrollment
                client_ids = df['client_id'].unique().tolist()
                clients = {}
                for client_id in client_ids:
                    client = make_request("GET", f"/clients/{client_id}")
                    if client:
                        clients[client_id] = f"{client['first_name']} {client['last_name']}"

                df['client_name'] = df['client_id'].map(clients)

                st.dataframe(
                    df[['id', 'client_name', 'enrollment_date', 'status', 'notes']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": "Enrollment ID",
                        "client_name": "Client",
                        "enrollment_date": "Enrollment Date",
                        "status": "Status",
                        "notes": "Notes"
                    }
                )
            else:
                st.info("No enrollments found for this program")

            st.markdown("---")
            st.subheader("Enroll Client in Program")

            client_id = st.text_input("Client ID to enroll")
            if client_id and st.button("Enroll Client", type="primary"):
                response = make_request(
                    "POST",
                    f"/clients/{client_id}/programs",
                    data={"program_ids": [program_id]}
                )

                if response:
                    st.success("Client enrolled successfully!")
                    st.rerun()