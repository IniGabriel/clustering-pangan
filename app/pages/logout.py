import streamlit as st
import os,sys
st.set_page_config(
    page_title="Clustering Website",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Hapus semua session data yang berkaitan dengan login
for key in ["logged_in", "username", "email"]:
    if key in st.session_state:
        del st.session_state[key]

# Beri notifikasi singkat
st.success("Anda telah logout. Mengarahkan ke halaman utama...")

# Tunggu sebentar supaya user sempat lihat pesan
import time
# time.sleep(1.5)

# ✅ Tambahkan path project root supaya bisa impor file dari luar /pages
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ✅ Baru sekarang import modul dari root
from save_session import  clear_session

# ✅ (opsional) langsung load session di awal

clear_session()
# Kembali ke halaman utama (home)
st.switch_page("home.py")
