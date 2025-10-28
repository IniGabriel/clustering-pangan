import streamlit as st
from utils.db import get_conn
from utils.auth_utils import hash_password
import os
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.set_page_config(page_title="Verifikasi Email", layout="centered")
st.title("🔑 Verifikasi Email")

if "pending_user" not in st.session_state:
    st.warning("Silakan daftar terlebih dahulu.")
    st.stop()

otp_input = st.text_input("Masukkan Kode Verifikasi")

if st.button("Verifikasi"):
    user = st.session_state.pending_user
    if otp_input == user["otp"]:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS Pengguna (
                        user_id SERIAL PRIMARY KEY,
                        username VARCHAR(40) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password VARCHAR(200) NOT NULL
                    );
                """)
                cur.execute("""
                    INSERT INTO Pengguna (username, email, password)
                    VALUES (%s, %s, %s)
                """, (user["username"], user["email"], hash_password(user["password"])))
        conn.close()
        st.success("🎉 Email terverifikasi! Akun berhasil dibuat.")
        del st.session_state.pending_user
        st.switch_page("pages/login.py")
    else:
        st.error("Kode verifikasi salah.")
