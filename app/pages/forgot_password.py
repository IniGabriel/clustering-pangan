import streamlit as st
from utils.db import get_conn
from utils.auth_utils import hash_password, generate_otp
from utils.email_utils import send_verification_email
import os
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.set_page_config(page_title="Lupa Password", layout="centered")
st.title("🔁 Lupa Password")

check_flow = st.session_state.flow
email = st.text_input("Masukkan email yang terdaftar")

if st.button("Kirim Kode Reset"):
    otp = generate_otp()
    st.session_state.reset_email = email
    st.session_state.reset_otp = otp
    try:
        send_verification_email(email, otp)
        st.success("Kode reset telah dikirim ke email kamu!")
    except Exception as e:
        st.error(f"Gagal kirim email: {e}")

if "reset_email" in st.session_state:
    kode = st.text_input("Masukkan kode verifikasi")
    new_pw = st.text_input("Password baru", type="password")
    if st.button("Reset Password"):
        if kode == st.session_state.reset_otp:
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE Pengguna SET password = %s WHERE email = %s
                    """, (hash_password(new_pw), st.session_state.reset_email))
            st.success("Password berhasil diubah! Silakan login.")
            st.session_state.pop("reset_email")
            st.session_state.pop("reset_otp")
            st.switch_page("pages/login.py")
        else:
            st.error("Kode salah.")
