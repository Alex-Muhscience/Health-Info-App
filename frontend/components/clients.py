import streamlit as st
import pandas as pd
from utils.helpers import make_request, format_date
from datetime import datetime


def get_clients():
    user_role = st.session_state.current_user['role']
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']

    if user_role not in allowed_roles:
        st.warning("You don't have permission to access this section")
        return

    st.title("Client Management")
    st.markdown("---")

    # Check user role for permissions
    user_role = st.session_state.current_user['role']
    can_edit = user_role in ['admin', 'doctor', 'nurse']
    can_delete = user_role == 'admin'

    # Tab navigation
    tab1, tab2 = st.tabs(["View Clients", "Manage Clients"])

    with tab1:
        st.subheader("Client Records")

        # Filters
        with st.expander("Filters", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                search_query = st.text_input("Search by name, phone, or email")
            with col2:
                gender = st.selectbox(
                    "Filter by gender",
                    ["All", "Male", "Female", "Other"],
                    index=0
                )

            active_only = st.checkbox("Show active clients only", value=True)
            min_age, max_age = st.columns(2)
            with min_age:
                min_age_filter = st.number_input("Minimum age", min_value=0, max_value=120, value=0)
            with max_age:
                max_age_filter = st.number_input("Maximum age", min_value=0, max_value=120, value=100)

        # Fetch clients with filters
        params = {
            "query": search_query if search_query else None,
            "gender": gender.lower() if gender != "All" else None,
            "active_only": active_only,
            "min_age": min_age_filter if min_age_filter > 0 else None,
            "max_age": max_age_filter if max_age_filter < 100 else None
        }

        clients = make_request("GET", "/clients", params=params)

        if clients and clients['data']:
            # Prepare data for display
            df = pd.DataFrame(clients['data'])
            df['dob'] = df['dob'].apply(format_date)
            df['age'] = df['dob'].apply(
                lambda x: (datetime.now() - datetime.strptime(x, "%b %d, %Y")).days // 365 if x else None)

            # Display table
            display_columns = [
                "id", "first_name", "last_name", "age", "gender",
                "phone", "email", "is_active"
            ]

            st.dataframe(
                df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "first_name": "First Name",
                    "last_name": "Last Name",
                    "age": "Age",
                    "gender": "Gender",
                    "phone": "Phone",
                    "email": "Email",
                    "is_active": "Active"
                }
            )
        else:
            st.info("No clients found matching your criteria")

    with tab2:
        if not can_edit:
            st.warning("You don't have permission to manage clients")
            return

        action = st.radio(
            "Select action",
            ["Create New Client", "Update Client", "Deactivate Client"],
            horizontal=True
        )

        if action == "Create New Client":
            st.subheader("Register New Client")
            with st.form("create_client_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name*", key="create_first_name")
                with col2:
                    last_name = st.text_input("Last Name*", key="create_last_name")

                col1, col2, col3 = st.columns(3)
                with col1:
                    dob = st.date_input("Date of Birth*", key="create_dob")
                with col2:
                    gender = st.selectbox(
                        "Gender*",
                        ["Male", "Female", "Other"],
                        key="create_gender"
                    )
                with col3:
                    phone = st.text_input("Phone Number*", key="create_phone")

                email = st.text_input("Email", key="create_email")
                address = st.text_area("Address", key="create_address")

                st.markdown("**Emergency Contact**")
                col1, col2 = st.columns(2)
                with col1:
                    emergency_name = st.text_input("Name", key="create_emergency_name")
                with col2:
                    emergency_phone = st.text_input("Phone", key="create_emergency_phone")

                notes = st.text_area("Notes", key="create_notes")

                if st.form_submit_button("Create Client", type="primary"):
                    if not all([first_name, last_name, dob, gender, phone]):
                        st.error("Please fill in all required fields (*)")
                    else:
                        client_data = {
                            "first_name": first_name,
                            "last_name": last_name,
                            "dob": dob.isoformat(),
                            "gender": gender.lower(),
                            "phone": phone,
                            "email": email if email else None,
                            "address": address,
                            "emergency_contact_name": emergency_name,
                            "emergency_contact_phone": emergency_phone,
                            "notes": notes
                        }

                        response = make_request("POST", "/clients", data=client_data)
                        if response:
                            st.success("Client created successfully!")
                            st.rerun()

        elif action == "Update Client":
            st.subheader("Update Client Information")
            client_id = st.text_input("Enter Client ID to update")

            if client_id:
                client = make_request("GET", f"/clients/{client_id}")
                if client:
                    with st.form("update_client_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            first_name = st.text_input(
                                "First Name*",
                                value=client['first_name'],
                                key="update_first_name"
                            )
                        with col2:
                            last_name = st.text_input(
                                "Last Name*",
                                value=client['last_name'],
                                key="update_last_name"
                            )

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            dob = st.date_input(
                                "Date of Birth*",
                                value=datetime.strptime(client['dob'], "%Y-%m-%d"),
                                key="update_dob"
                            )
                        with col2:
                            gender = st.selectbox(
                                "Gender*",
                                ["Male", "Female", "Other"],
                                index=["male", "female", "other"].index(client['gender']),
                                key="update_gender"
                            )
                        with col3:
                            phone = st.text_input(
                                "Phone Number*",
                                value=client['phone'],
                                key="update_phone"
                            )

                        email = st.text_input(
                            "Email",
                            value=client['email'] or "",
                            key="update_email"
                        )
                        address = st.text_area(
                            "Address",
                            value=client['address'] or "",
                            key="update_address"
                        )

                        st.markdown("**Emergency Contact**")
                        col1, col2 = st.columns(2)
                        with col1:
                            emergency_name = st.text_input(
                                "Name",
                                value=client['emergency_contact_name'] or "",
                                key="update_emergency_name"
                            )
                        with col2:
                            emergency_phone = st.text_input(
                                "Phone",
                                value=client['emergency_contact_phone'] or "",
                                key="update_emergency_phone"
                            )

                        notes = st.text_area(
                            "Notes",
                            value=client['notes'] or "",
                            key="update_notes"
                        )

                        is_active = st.checkbox(
                            "Active",
                            value=client['is_active'],
                            key="update_active"
                        )

                        if st.form_submit_button("Update Client", type="primary"):
                            if not all([first_name, last_name, dob, gender, phone]):
                                st.error("Please fill in all required fields (*)")
                            else:
                                update_data = {
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "dob": dob.isoformat(),
                                    "gender": gender.lower(),
                                    "phone": phone,
                                    "email": email if email else None,
                                    "address": address,
                                    "emergency_contact_name": emergency_name,
                                    "emergency_contact_phone": emergency_phone,
                                    "notes": notes,
                                    "is_active": is_active
                                }

                                response = make_request("PUT", f"/clients/{client_id}", data=update_data)
                                if response:
                                    st.success("Client updated successfully!")
                                    st.rerun()
                else:
                    st.error("Client not found")

        elif action == "Deactivate Client" and can_delete:
            st.subheader("Deactivate Client")
            client_id = st.text_input("Enter Client ID to deactivate")

            if client_id and st.button("Deactivate Client", type="primary"):
                response = make_request("DELETE", f"/clients/{client_id}")
                if response:
                    st.success("Client deactivated successfully")
                    st.rerun()