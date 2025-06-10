import streamlit as st
import pandas as pd
from utils.helpers import make_request, format_date
from datetime import datetime, date


def get_clients():
    """Main client management interface"""
    # Check if user is logged in
    if 'current_user' not in st.session_state:
        st.error("Please log in to access this section")
        return

    user_role = st.session_state.current_user.get('role')
    allowed_roles = ['admin', 'doctor', 'nurse', 'receptionist']

    if user_role not in allowed_roles:
        st.warning("You don't have permission to access this section")
        return

    st.title("Client Management")
    st.markdown("---")

    # Check user role for permissions
    can_edit = user_role in ['admin', 'doctor', 'nurse']
    can_delete = user_role == 'admin'

    # Handle action from session state (for navigation from dashboard)
    if st.session_state.get('client_action') == 'create':
        default_tab = 1
        st.session_state.client_action = None  # Clear the action
    else:
        default_tab = 0

    # Tab navigation
    tab1, tab2 = st.tabs(["View Clients", "Manage Clients"])

    with tab1:
        _display_clients_view()

    with tab2:
        if not can_edit:
            st.warning("You don't have permission to manage clients")
            return
        _display_clients_management(can_delete)


def _display_clients_view():
    """Display clients list with filters"""
    st.subheader("Client Records")

    # Filters
    with st.expander("Filters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            search_query = st.text_input("Search by name, phone, or email", key="search_clients")
        with col2:
            gender = st.selectbox(
                "Filter by gender",
                ["All", "Male", "Female", "Other"],
                index=0,
                key="filter_gender"
            )

        col1, col2 = st.columns(2)
        with col1:
            active_only = st.checkbox("Show active clients only", value=True, key="filter_active")
        with col2:
            per_page = st.selectbox("Clients per page", [10, 20, 50, 100], index=1, key="per_page")

        col1, col2 = st.columns(2)
        with col1:
            min_age_filter = st.number_input("Minimum age", min_value=0, max_value=120, value=0, key="min_age")
        with col2:
            max_age_filter = st.number_input("Maximum age", min_value=0, max_value=120, value=100, key="max_age")

    # Build request parameters
    params = {}
    if search_query:
        params['query'] = search_query
    if gender != "All":
        params['gender'] = gender.lower()
    params['active_only'] = str(active_only).lower()
    params['per_page'] = per_page
    if min_age_filter > 0:
        params['min_age'] = min_age_filter
    if max_age_filter < 100:
        params['max_age'] = max_age_filter

    # Fetch clients with loading indicator
    with st.spinner("Loading clients..."):
        response = make_request("GET", "/clients/clients/", params=params)

    if response and response.get('data'):
        clients_data = response['data']
        
        # Prepare data for display
        df_data = []
        for client in clients_data:
            df_data.append({
                'ID': client.get('id'),
                'First Name': client.get('first_name'),
                'Last Name': client.get('last_name'),
                'Age': client.get('age', 'N/A'),
                'Gender': client.get('gender', '').title(),
                'Phone': client.get('phone'),
                'Email': client.get('email') or 'N/A',
                'Active': '✅' if client.get('is_active') else '❌'
            })

        if df_data:
            df = pd.DataFrame(df_data)
            
            # Display pagination info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"Total clients: {response.get('total', 0)}")
            with col2:
                st.info(f"Page: {response.get('current_page', 1)} of {response.get('pages', 1)}")
            with col3:
                st.info(f"Showing: {len(df_data)} clients")

            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            # Pagination controls
            if response.get('pages', 1) > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    current_page = response.get('current_page', 1)
                    total_pages = response.get('pages', 1)
                    
                    page_options = list(range(1, total_pages + 1))
                    selected_page = st.selectbox(
                        "Go to page:",
                        page_options,
                        index=current_page - 1,
                        key="page_selector"
                    )
                    
                    if selected_page != current_page:
                        params['page'] = selected_page
                        st.rerun()
        else:
            st.info("No clients found matching your criteria")
    else:
        st.error("Failed to load clients. Please try again.")


def _display_clients_management(can_delete):
    """Display client management interface"""
    action = st.radio(
        "Select action",
        ["Create New Client", "Update Client", "Deactivate Client"] if can_delete else ["Create New Client", "Update Client"],
        horizontal=True,
        key="client_action_radio"
    )

    if action == "Create New Client":
        _create_client_form()
    elif action == "Update Client":
        _update_client_form()
    elif action == "Deactivate Client" and can_delete:
        _deactivate_client_form()


def _create_client_form():
    """Create new client form"""
    st.subheader("Register New Client")
    
    with st.form("create_client_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", key="create_first_name")
        with col2:
            last_name = st.text_input("Last Name*", key="create_last_name")

        col1, col2, col3 = st.columns(3)
        with col1:
            dob = st.date_input(
                "Date of Birth*", 
                max_value=date.today(),
                key="create_dob"
            )
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

        submitted = st.form_submit_button("Create Client", type="primary")
        
        if submitted:
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
                    "address": address if address else None,
                    "emergency_contact_name": emergency_name if emergency_name else None,
                    "emergency_contact_phone": emergency_phone if emergency_phone else None,
                    "notes": notes if notes else None
                }

                with st.spinner("Creating client..."):
                    response = make_request("POST", "/clients/clients", data=client_data)
                
                if response:
                    st.success("Client created successfully!")
                    st.balloons()
                    # Auto refresh after 2 seconds
                    if st.button("View Clients", key="view_after_create"):
                        st.rerun()


def _update_client_form():
    """Update client form"""
    st.subheader("Update Client Information")
    
    client_id = st.number_input(
        "Enter Client ID to update", 
        min_value=1, 
        step=1,
        key="update_client_id"
    )

    if client_id and st.button("Load Client", key="load_client"):
        with st.spinner("Loading client data..."):
            client = make_request("GET", f"/clients/clients/{client_id}")
        
        if client:
            st.session_state.client_to_update = client
            st.success("Client loaded successfully!")
        else:
            st.error("Client not found")

    if 'client_to_update' in st.session_state:
        client = st.session_state.client_to_update
        
        with st.form("update_client_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input(
                    "First Name*",
                    value=client.get('first_name', ''),
                    key="update_first_name"
                )
            with col2:
                last_name = st.text_input(
                    "Last Name*",
                    value=client.get('last_name', ''),
                    key="update_last_name"
                )

            col1, col2, col3 = st.columns(3)
            with col1:
                try:
                    dob_value = datetime.strptime(client.get('dob', ''), "%Y-%m-%d").date()
                except:
                    dob_value = date.today()
                
                dob = st.date_input(
                    "Date of Birth*",
                    value=dob_value,
                    max_value=date.today(),
                    key="update_dob"
                )
            with col2:
                gender_options = ["male", "female", "other"]
                current_gender = client.get('gender', 'male').lower()
                gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
                
                gender = st.selectbox(
                    "Gender*",
                    ["Male", "Female", "Other"],
                    index=gender_index,
                    key="update_gender"
                )
            with col3:
                phone = st.text_input(
                    "Phone Number*",
                    value=client.get('phone', ''),
                    key="update_phone"
                )

            email = st.text_input(
                "Email",
                value=client.get('email', '') or '',
                key="update_email"
            )
            address = st.text_area(
                "Address",
                value=client.get('address', '') or '',
                key="update_address"
            )

            st.markdown("**Emergency Contact**")
            col1, col2 = st.columns(2)
            with col1:
                emergency_name = st.text_input(
                    "Name",
                    value=client.get('emergency_contact_name', '') or '',
                    key="update_emergency_name"
                )
            with col2:
                emergency_phone = st.text_input(
                    "Phone",
                    value=client.get('emergency_contact_phone', '') or '',
                    key="update_emergency_phone"
                )

            notes = st.text_area(
                "Notes",
                value=client.get('notes', '') or '',
                key="update_notes"
            )

            is_active = st.checkbox(
                "Active",
                value=client.get('is_active', True),
                key="update_active"
            )

            submitted = st.form_submit_button("Update Client", type="primary")
            
            if submitted:
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
                        "address": address if address else None,
                        "emergency_contact_name": emergency_name if emergency_name else None,
                        "emergency_contact_phone": emergency_phone if emergency_phone else None,
                        "notes": notes if notes else None,
                        "is_active": is_active
                    }

                    with st.spinner("Updating client..."):
                        response = make_request("PUT", f"/clients/{client_id}", data=update_data)
                    
                    if response:
                        st.success("Client updated successfully!")
                        del st.session_state.client_to_update
                        st.rerun()


def _deactivate_client_form():
    """Deactivate client form"""
    st.subheader("Deactivate Client")
    st.warning("⚠️ This action will deactivate the client. They will no longer appear in active client lists.")
    
    client_id = st.number_input(
        "Enter Client ID to deactivate", 
        min_value=1, 
        step=1,
        key="deactivate_client_id"
    )

    if client_id:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Preview Client", key="preview_deactivate"):
                with st.spinner("Loading client..."):
                    client = make_request("GET", f"/clients/{client_id}")
                
                if client:
                    st.info(f"**Client:** {client.get('first_name')} {client.get('last_name')}")
                    st.info(f"**Phone:** {client.get('phone')}")
                    st.info(f"**Status:** {'Active' if client.get('is_active') else 'Inactive'}")
                else:
                    st.error("Client not found")

        with col2:
            if st.button("Deactivate Client", type="primary", key="confirm_deactivate"):
                with st.spinner("Deactivating client..."):
                    response = make_request("DELETE", f"/clients/{client_id}")
                
                if response:
                    st.success("Client deactivated successfully")
                    st.rerun()


# Call the function when this module is run
if __name__ == "__main__":
    get_clients()