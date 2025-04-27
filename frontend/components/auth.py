import streamlit as st
from utils.helpers import make_request


def show_auth_page():
    st.title("Healthcare Management System")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Login to your account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Login", type="primary"):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    response = make_request(
                        "POST",
                        "/auth/login",
                        data={"username": username, "password": password}
                    )

                    if response:
                        st.session_state.authenticated = True
                        st.session_state.current_user = response['user']
                        st.session_state.token = response['access_token']
                        st.rerun()

    with tab2:
        st.subheader("Request an account")
        st.info("Please contact your administrator to create an account for you")