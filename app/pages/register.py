import streamlit as st
import re
import time
from utils.db import get_conn
from utils.auth_utils import hash_password, generate_otp
from utils.email_utils import send_verification_email
import inspect
from utils import email_utils
print("📂 Email util file:", inspect.getfile(email_utils))

# === Konfigurasi Halaman ===
st.set_page_config(page_title="Registrasi", layout="centered")
st.title("📋 Registrasi Pengguna Baru")

# === Load CSS ===
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Input Form ===
username = st.text_input("Username")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

# === Fungsi Validasi ===
def is_valid_email(email: str) -> bool:
    """Validasi sederhana format email."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def is_strong_password(password: str) -> bool:
    """Password minimal 8 karakter, mengandung huruf dan angka."""
    return len(password) >= 8 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)

# === Tombol Kirim Verifikasi ===
if st.button("Kirim Kode Verifikasi"):
    # Cek semua kolom terisi
    if not all([username, email, password]):
        st.warning("⚠️ Isi semua kolom terlebih dahulu!")
    elif len(username) < 3:
        st.warning("⚠️ Username minimal 3 karakter!")
    elif not is_valid_email(email):
        st.warning("⚠️ Format email tidak valid. Gunakan format seperti user@example.com")
    elif not is_strong_password(password):
        st.warning("⚠️ Password minimal 8 karakter dan harus mengandung huruf serta angka!")
    else:
        otp = generate_otp()
        try:
            st.write("username:",username)
            st.write("email:",email)
            send_verification_email(email, otp)
            st.session_state.pending_user = {
                "username": username,
                "email": email,
                "password": password,
                "otp": otp
            }
            st.success("✅ Kode verifikasi telah dikirim ke email kamu!")
            time.sleep(1)
            st.switch_page("pages/verify_email.py")
        except Exception as e:
            st.error(f"❌ Gagal mengirim email: {e}")

# === Tombol Kembali ===
st.write("---")
if st.button("⬅️ Kembali ke Login"):
    st.switch_page("pages/login.py")
