import streamlit as st
import time
from utils.db import get_conn
from utils.auth_utils import verify_password,hash_password
import os
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.set_page_config(page_title="Login", layout="centered")
st.title("🔒 Login Pengguna")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Masuk"):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username, password FROM Pengguna WHERE email = %s;", (email,))
                user = cur.fetchone()
                if user and verify_password(password, user[1]):
                    st.session_state.logged_in = True
                    st.session_state.username = user[0]
                    st.session_state.email = email
                    st.success(f"Berhasil login sebagai {user[0]}!")
                    time.sleep(1.2)

                    cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", ("dummy@email.com",))
                    dummy_user = cur.fetchone()
                    if not dummy_user:
                        dummy_hashed_pw = hash_password("IniDummy123")
                        cur.execute("""
                            INSERT INTO Pengguna (username, email, password)
                            VALUES (%s, %s, %s);
                        """, ("dummy", "dummy@email.com", dummy_hashed_pw))
                        conn.commit()

                    if email == "admin@email.com":
                        st.switch_page("pages/admin.py")
                    else:
                        st.switch_page("home.py")
                else:
                    st.error("Email atau password salah.")
    except Exception as e:
        st.error(f"Kesalahan koneksi: {e}")

st.markdown("---")
st.page_link("pages/register.py", label="📩 Belum punya akun? Daftar di sini")
st.page_link("pages/forgot_password.py", label="🔁 Lupa password?")
st.write("---")
st.page_link("home.py", label="⬅️ Kembali ke Home")
