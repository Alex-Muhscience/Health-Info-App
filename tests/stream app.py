# streamlit_login_test.py
import streamlit as st
import requests

st.title("Login Test")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    response = requests.post(
        "http://localhost:8000/api/auth/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        st.success("Login successful!")
        st.json(response.json())
    else:
        st.error(f"Login failed: {response.json().get('error')}")