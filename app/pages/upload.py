import streamlit as st
import psycopg2
import os, sys
import time
from utils.db import get_conn  # pastikan fungsi ini mengembalikan psycopg2.connect(...)
# (opsional) kalau nanti mau validasi isi file, baru import pandas di halaman lain.

# ========== 0️⃣ Halaman ==========
st.set_page_config(
    page_title="Upload Dataset",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== 1️⃣ Akses modul session dari root ==========
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from session import init_session

# ========== 2️⃣ Inisialisasi session login ==========
init_session()
logged_in = st.session_state.get("logged_in", False)
username  = st.session_state.get("username", "")
email     = st.session_state.get("email", "")

# ========== 3️⃣ Load CSS ==========
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ========== 4️⃣ Koneksi DB ==========
con = get_conn()
cur = con.cursor()

# ========== 5️⃣ Helper ==========
BASE_UPLOAD_DIR = "uploads"  # relatif terhadap root app (aman untuk Streamlit Cloud & lokal)

def get_user_id_by_email(cur, email: str):
    cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", (email,))
    row = cur.fetchone()
    return row[0] if row else None

def ensure_user_folder(user_id: int) -> str:
    folder = os.path.join(BASE_UPLOAD_DIR, f"user_{user_id}")
    os.makedirs(folder, exist_ok=True)
    return folder

def is_duplicate_dataset(cur, user_id: int, path_dataset: str) -> bool:
    cur.execute("""
        SELECT dataset_id
        FROM dataset
        WHERE user_id = %s AND path_dataset = %s;
    """, (user_id, path_dataset))
    return cur.fetchone() is not None

def insert_dataset(cur, con, nama: str, path_rel: str, user_id: int, sudah_dilatih: bool = False):
    cur.execute("""
        INSERT INTO dataset (nama_dataset, path_dataset, user_id, sudah_dilatih)
        VALUES (%s, %s, %s, %s);
    """, (nama, path_rel, user_id, sudah_dilatih))
    con.commit()

# ========== 6️⃣ Navbar ==========
if logged_in:
    cols = st.columns(7)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)
    with cols[1]:
        st.page_link("home.py", label="Home")
    with cols[2]:
        st.page_link("pages/visualization.py", label="Visualization")
    with cols[3]:
        st.page_link("pages/summary.py", label="Summary")
    with cols[4]:
        st.page_link("pages/about.py", label="About")
    with cols[5]:
        st.write(f"Halo, {username} 👋")
    with cols[6]:
        if st.button("Logout"):
            for k in ["logged_in", "username", "email"]:
                st.session_state.pop(k, None)
            st.switch_page("home.py")

    # ========== 7️⃣ Judul ==========
    st.markdown("<h2 style='text-align:center;'>📤 Upload Dataset</h2>", unsafe_allow_html=True)
    st.write("")

    # ========== 8️⃣ Tiga Kolom (Template / Upload / Lihat) ==========
    col1, col2, col3 = st.columns(3)

    # ---- 📥 Kolom 1: Download Template ----

    with col1:
        st.markdown("""
        <div style="
            display:flex;justify-content:center;align-items:center;
            background-color:#f0f0f0;border-radius:15px;height:200px;
            box-shadow:2px 2px 8px rgba(0,0,0,0.2);
        ">
            <h3>📥 Unduh Template</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Unduh Template", use_container_width=True):
            st.switch_page("pages/template.py")

    # ---- 📁 Kolom 2: Unggah Dataset (tanpa input path) ----
    with col2:
        st.markdown("""
        <div style="
            display:flex;justify-content:center;align-items:center;
            background-color:#f0f0f0;border-radius:15px;height:200px;
            box-shadow:2px 2px 8px rgba(0,0,0,0.2);
        ">
            <h3>📁 Unggah Dataset</h3>
        </div>
        """, unsafe_allow_html=True)

        st.caption("💡 File akan otomatis disimpan di folder internal aplikasi: `uploads/user_{user_id}/`")

    # ---- 📊 Kolom 3: Lihat Dataset ----
    with col3:
        st.markdown("""
        <div style="
            display:flex;justify-content:center;align-items:center;
            background-color:#f0f0f0;border-radius:15px;height:200px;
            box-shadow:2px 2px 8px rgba(0,0,0,0.2);
        ">
            <h3>📊 Lihat Dataset</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Lihat Dataset", use_container_width=True):
            st.switch_page("pages/dataset.py")

    st.write("---")

    # ========== 9️⃣ Form Upload ==========
    uploaded_file = st.file_uploader("📤 Pilih file dataset (CSV/XLSX):", type=["csv", "xlsx"])

    user_id = get_user_id_by_email(cur, email)
    if not user_id:
        st.error("Terjadi kesalahan silahkan login kembali.")
        time.sleep(1.5)
        for key in ["logged_in", "username", "email"]:
            if key in st.session_state:
                del st.session_state[key]        
        st.switch_page("home.py")
        st.stop()
    if uploaded_file:
        try:

            # 2) Pastikan folder user ada
            user_folder = ensure_user_folder(user_id)

            # 3) Tentukan path relatif yang akan disimpan ke DB
            safe_name = uploaded_file.name.strip().replace("\\", "_").replace("/", "_")
            file_rel_path = os.path.join("uploads", f"user_{user_id}", safe_name)   # disimpan ke DB
            file_abs_path = os.path.join(user_folder, safe_name)                   # lokasi fisik

            # 4) Cek duplikat berdasarkan user_id + path_dataset
            if is_duplicate_dataset(cur, user_id, file_rel_path):
                st.warning(
                    f"⚠️ Dataset dengan nama yang sama sudah ada di: `{file_rel_path}`.\n"
                    f"Silakan rename file sebelum upload ulang."
                )
            else:
                # 5) Simpan file fisik
                with open(file_abs_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 6) Simpan metadata ke DB
                insert_dataset(cur, con, safe_name, file_rel_path, user_id, sudah_dilatih=False)

                st.success(f"✅ File '{safe_name}' berhasil diunggah!")
                st.markdown(
                    f"📁 **Lokasi (relatif app):** <code>{file_rel_path}</code>",
                    unsafe_allow_html=True
                )

        except Exception as e:
            con.rollback()
            st.error(f"❌ Terjadi error saat upload: {e}")

else:
    st.warning("Mohon maaf terjadi kesalahan. Silahkan login kembali!")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()
