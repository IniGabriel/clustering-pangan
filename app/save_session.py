import streamlit as st
import json, os

SESSION_FILE = "session_state.json"

def save_session():
    """Simpan session_state ke file"""
    with open(SESSION_FILE, "w") as f:
        json.dump({
            "logged_in": st.session_state.get("logged_in", False),
            "username": st.session_state.get("username", ""),
            "email": st.session_state.get("email", "")
        }, f)

def load_session():
    """Muat session_state dari file"""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            st.session_state.logged_in = data.get("logged_in", False)
            st.session_state.username = data.get("username", "")
            st.session_state.email = data.get("email", "")
    else:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.email = ""

def clear_session():
    """Hapus file session"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.email = ""
