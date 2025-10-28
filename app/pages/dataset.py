import streamlit as st
import psycopg2
import os, sys
import time
from utils.db import get_conn
# === 1️⃣ Akses modul session dari folder root ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from session import init_session

current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_session()
logged_in = st.session_state.get("logged_in", False)
email = st.session_state.get("email", "")

# === 4️⃣ Konfigurasi halaman ===
st.set_page_config(page_title="Data Saya", layout="wide")

st.session_state.selected_folder = ""
st.session_state.show_uploader = False
st.session_state.upload_status = None  # "success", "duplicate", "error"
st.session_state.last_file_path = None



# === 6️⃣ Validasi login ===
if not logged_in:
    st.warning("Terjadi kesalahan, silahkan login kembali!")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()

# === 7️⃣ Ambil user_id ===
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", (email,))
    user_row = cur.fetchone()
    if not user_row:
        st.error("User tidak ditemukan di database.")
        st.stop()
    user_id = user_row[0]
except Exception as e:
    st.error(f"❌ Gagal koneksi database: {e}")
    st.stop()

# === 8️⃣ Judul Halaman ===
st.markdown("<h2 style='text-align:center;'>📁 Data Saya</h2>", unsafe_allow_html=True)
st.write("---")

if st.button("⬅️ Kembali ke halaman sebelumnya"):
    st.switch_page("pages/upload.py")

# === 9️⃣ Ambil dataset milik user ===
cur.execute("""
    SELECT dataset_id, nama_dataset, path_dataset, sudah_dilatih
    FROM Dataset 
    WHERE user_id = %s;
""", (user_id,))
datasets = cur.fetchall()

# === 🔟 Cek file yang sudah tidak ada ===
deleted_count = 0
for (dataset_id, nama_dataset, path_dataset, sudah_dilatih) in datasets:
    if not os.path.exists(path_dataset):
        try:
            cur.execute(
                "DELETE FROM Dataset WHERE user_id = %s AND path_dataset = %s;",
                (user_id, path_dataset)
            )
            conn.commit()
            deleted_count += 1
        except Exception as e:
            st.warning(f"Gagal menghapus dataset yang hilang ({nama_dataset}): {e}")

if deleted_count > 0:
    st.info(f"🧹 {deleted_count} file dari dataset ini sudah tidak ada. Silakan upload ulang.")
    time.sleep(1)
    st.rerun()

# === 1️⃣1️⃣ Ambil ulang dataset setelah pembersihan ===
cur.execute("""
    SELECT dataset_id, nama_dataset, path_dataset, sudah_dilatih
    FROM Dataset 
    WHERE user_id = %s;
""", (user_id,))
datasets = cur.fetchall()

if not datasets:
    st.info("Belum ada dataset yang diunggah.")
    st.stop()

# === 1️⃣2️⃣ State untuk konfirmasi delete ===
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None

# === 1️⃣3️⃣ Tampilkan dataset ===
for idx, (dataset_id, nama_dataset, path_dataset, sudah_dilatih) in enumerate(datasets):
    if sudah_dilatih:
        col1, col2, col3, col4 = st.columns([3.5, 1.2, 1.2, 1.2])
    else:
        col1,col2,col4 =st.columns([3.5,1.2,1.2])

    # === Kolom 1: Info ===
    with col1:
        st.markdown(f"**📄 {nama_dataset}**")
        st.caption(f"{path_dataset}")
        if sudah_dilatih:
            st.markdown("<span style='color:#2ECC71;'>✅ Sudah Diproses</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#E67E22;'>⚙️ Belum Diproses</span>", unsafe_allow_html=True)

    # === Kolom 2: Train ===
    with col2:
        if sudah_dilatih:
            train_btn = st.button("🚀 Proses Ulang", key=f"train_{idx}", use_container_width=True)
        else:
            train_btn = st.button("🚀 Proses Data", key=f"train_{idx}", use_container_width=True)            
        if train_btn:
            st.session_state["selected_dataset"] = path_dataset
            st.switch_page("pages/train.py")

    # === Kolom 3: Lihat Visualisasi (jika sudah dilatih) ===
    if sudah_dilatih:
        with col3:
            view_btn = st.button("📊 Lihat Visualisasi", key=f"view_{idx}", use_container_width=True)
            if view_btn:
                st.session_state["selected_dataset"] = path_dataset
                st.switch_page("pages/visual_dataset.py")

    # === Kolom 4: Delete ===
    with col4:
        del_btn = st.button("🗑️ Hapus Dataset", key=f"delete_{idx}", use_container_width=True)

    # ==== Delete ====
    if del_btn:
        st.session_state.confirm_delete_id = dataset_id
        st.rerun()

    # ==== Konfirmasi hapus inline ====
    if st.session_state.confirm_delete_id == dataset_id:
        st.warning(f"Apakah Anda yakin ingin menghapus dataset **{nama_dataset}**?")
        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✅ Ya, Hapus Dataset Ini", key=f"confirm_{idx}"):
                try:
                    if os.path.exists(path_dataset):
                        os.remove(path_dataset)
                        st.info(f"🧹 File dihapus dari folder: `{path_dataset}`")
                    else:
                        st.warning(f"⚠️ File tidak ditemukan di: `{path_dataset}`")

                    cur.execute(
                        "DELETE FROM Dataset WHERE user_id = %s AND path_dataset = %s;",
                        (user_id, path_dataset)
                    )
                    conn.commit()

                    st.success(f"✅ Dataset '{nama_dataset}' berhasil dihapus sepenuhnya!")
                    st.session_state.confirm_delete_id = None
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal menghapus dataset: {e}")

        with col_no:
            if st.button("❌ Batal", key=f"cancel_{idx}"):
                st.session_state.confirm_delete_id = None
                st.rerun()

# === 1️⃣4️⃣ CSS Tombol Berwarna ===
st.markdown("""
<style>
div[data-testid="stButton"][key^="train_"] > button {
    background-color: #2a9d8f !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
}
div[data-testid="stButton"][key^="view_"] > button {
    background-color: #007bff !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
}
div[data-testid="stButton"][key^="delete_"] > button {
    background-color: #e63946 !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
}
div[data-testid="stButton"][key^="confirm_"] > button {
    background-color: #d62828 !important;
    color: white !important;
    border-radius: 8px;
}
div[data-testid="stButton"][key^="cancel_"] > button {
    background-color: #adb5bd !important;
    color: black !important;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)
