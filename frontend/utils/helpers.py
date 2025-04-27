import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime, timedelta


# Load CSS from file
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "../assets/style.css")
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# API request helper
BASE_URL = "http://127.0.0.1:8000/api"  # Match your Flask server's address and port


def make_request(method, endpoint, data=None, params=None, headers=None):
    # Ensure endpoint starts with a slash but doesn't end with one
    global response
    endpoint = endpoint if endpoint.startswith('/') else f'/{endpoint}'
    endpoint = endpoint.rstrip('/')

    url = f"{BASE_URL}{endpoint}"

    if headers is None:
        headers = {}

    if st.session_state.get('token'):
        headers['Authorization'] = f"Bearer {st.session_state.token}"

    try:
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError("Invalid HTTP method")

        # Handle role violations
        if response.status_code == 403:
            st.error("You don't have permission to perform this action")
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as err:
        error_msg = f"HTTP Error: {err}"
        if response.status_code == 404:
            error_msg = "Endpoint not found. Please check the API configuration."
        st.error(error_msg)
        return None
    except Exception as err:
        st.error(f"An error occurred: {err}")
        return None

# Date formatting helpers
def format_date(date_str):
    if not date_str:
        return ""
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")


def format_datetime(datetime_str):
    if not datetime_str:
        return ""
    return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S").strftime("%b %d, %Y %I:%M %p")


# Create a date range filter component
def date_range_filter(key_prefix=""):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From date",
            value=datetime.now() - timedelta(days=30),
            key=f"{key_prefix}_start_date"
        )
    with col2:
        end_date = st.date_input(
            "To date",
            value=datetime.now(),
            key=f"{key_prefix}_end_date"
        )
    return start_date, end_date


# Display data in a styled table
def display_data_table(data, columns=None):
    if not data:
        st.info("No data available")
        return

    df = pd.DataFrame(data)
    if columns:
        df = df[columns]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": None,
            "client_id": None,
            "created_at": None
        }
    )