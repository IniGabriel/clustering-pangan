import streamlit as st
from utils.db import get_conn
from utils.auth_utils import hash_password, generate_otp
from utils.email_utils import send_verification_email
import os
import re

# === Konfigurasi Halaman ===
st.set_page_config(page_title="Lupa Password", layout="centered")
st.title("🔁 Lupa Password")

# === Load CSS ===
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Fungsi Validasi Password ===
def is_strong_password(password: str) -> bool:
    """Password minimal 8 karakter, mengandung huruf dan angka."""
    return len(password) >= 8 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)

# === Input Email ===
email = st.text_input("Masukkan email yang terdaftar")

# === Tombol Kirim OTP ===
if st.button("Kirim Kode Reset"):
    if not email:
        st.warning("⚠️ Harap isi email terlebih dahulu.")
    else:
        try:
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM Pengguna WHERE email = %s;", (email,))
                    user_exists = cur.fetchone()
            
            if not user_exists:
                st.error("❌ Email tidak ditemukan di sistem. Pastikan kamu sudah terdaftar.")
            else:
                otp = generate_otp()
                st.session_state.reset_email = email
                st.session_state.reset_otp = otp
                try:
                    send_verification_email(email, otp)
                    st.success("✅ Kode reset telah dikirim ke email kamu!")
                except Exception as e:
                    st.error(f"❌ Gagal mengirim email: {e}")

        except Exception as e:
            st.error(f"❌ Gagal memeriksa email di database: {e}")

# === Input OTP dan Password Baru ===
if "reset_email" in st.session_state:
    kode = st.text_input("Masukkan kode verifikasi (OTP)")
    new_pw = st.text_input("Masukkan password baru", type="password")

    if st.button("Reset Password"):
        if kode != st.session_state.reset_otp:
            st.error("❌ Kode verifikasi salah.")
        elif not new_pw:
            st.warning("⚠️ Harap isi password baru terlebih dahulu.")
        elif not is_strong_password(new_pw):
            st.warning("⚠️ Password minimal 8 karakter dan harus mengandung huruf serta angka!")
        else:
            try:
                conn = get_conn()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE Pengguna 
                            SET password = %s 
                            WHERE email = %s;
                        """, (hash_password(new_pw), st.session_state.reset_email))
                st.success("✅ Password berhasil diubah! Silakan login.")
                st.session_state.pop("reset_email")
                st.session_state.pop("reset_otp")
                st.switch_page("pages/login.py")
            except Exception as e:
                st.error(f"❌ Gagal mengubah password: {e}")
