import streamlit as st
import psycopg2
import os, sys
import time
# === 4️⃣ Database Configuration ===
from utils.db import get_conn
# === 0️⃣ Konfigurasi halaman ===
st.set_page_config(
    page_title="Upload Dataset",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === 1️⃣ Akses modul session dari folder root ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from session import init_session

# === 2️⃣ Inisialisasi session login ===
init_session()
logged_in = st.session_state.get("logged_in", False)
username = st.session_state.get("username", "")
email = st.session_state.get("email", "")

# === 3️⃣ Load CSS ===
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


con = get_conn()
cur = con.cursor()

# === 5️⃣ State variables ===
if "selected_folder" not in st.session_state:
    st.session_state.selected_folder = ""
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False
if "upload_status" not in st.session_state:
    st.session_state.upload_status = None  # "success", "duplicate", "error"
if "last_file_path" not in st.session_state:
    st.session_state.last_file_path = None

# === 6️⃣ Navbar ===
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

    # === 7️⃣ Judul Halaman ===
    st.markdown("<h2 style='text-align:center;'>📤 Upload Dataset</h2>", unsafe_allow_html=True)
    st.write("")

    # === 8️⃣ Kolom besar: Download / Upload / Lihat ===
    col1, col2, col3 = st.columns(3)

    # === 📥 Kolom 1: Download Template ===
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

        # csv_template = "col1,col2,col3\n1,2,3\n4,5,6"
        # st.download_button(
        #     label="Download Template Dataset",
        #     data=csv_template,
        #     file_name="template_dataset.csv",
        #     use_container_width=True
        # )
        if st.button("Unduh Template", use_container_width=True):
            st.switch_page("pages/template.py")

    # === 📁 Kolom 2: Pilih Lokasi Upload ===
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

        st.caption("💡 Tuliskan Absolute path contoh: D:/User/Documents/DataApp")
        folder_input = st.text_input("Masukkan lokasi penyimpanan dataset:", placeholder="Contoh: D:/DataUpload")

        if st.button("✅ Konfirmasi Lokasi"):
            folder_input = folder_input.strip()
            if not folder_input:
                st.error("⚠️ Harap isi path lengkap lokasi penyimpanan terlebih dahulu.")
                st.session_state.show_uploader = False
            elif not os.path.isabs(folder_input):
                st.write(folder_input)
                st.error("❌ Path tidak valid. Harap masukkan path lengkap (absolute path) tanpa tanda kutip.")
                st.session_state.show_uploader = False
            elif not os.path.exists(folder_input):
                st.error(f"❌ Folder `{folder_input}` tidak ditemukan. Buat foldernya lalu coba lagi.")
                st.session_state.show_uploader = False
            elif not os.path.isdir(folder_input):
                st.error(f"⚠️ Path ditemukan tapi bukan folder: `{folder_input}`")
                st.session_state.show_uploader = False
            else:
                st.session_state.selected_folder = folder_input
                st.session_state.show_uploader = True
                st.success(f"✅ Folder diset ke: {folder_input}")

    # === 📊 Kolom 3: Lihat Dataset ===
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

    # === 📤 Bagian Upload File ===
    placeholder = st.empty()  # kontainer dinamis untuk uploader
    if st.session_state.selected_folder and st.session_state.show_uploader:
        with placeholder.container():
            uploaded_file = st.file_uploader("📤 Pilih file CSV untuk diunggah:", type=["csv","xlsx"])

            if uploaded_file:
                save_path = st.session_state.selected_folder
                file_path = os.path.join(save_path, uploaded_file.name)
                st.session_state.last_file_path = file_path  # ✅ simpan path di session

                try:
                    # Ambil user_id
                    cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", (email,))
                    user_row = cur.fetchone()
                    if not user_row:
                        st.error("❌ Gagal mendapatkan user_id dari database.")
                        st.stop()
                    user_id = user_row[0]

                    # Cek duplikat file
                    cur.execute("""
                        SELECT dataset_id FROM dataset 
                        WHERE user_id = %s AND path_dataset = %s;
                    """, (user_id, file_path))
                    duplicate = cur.fetchone()

                    if not duplicate:
                        # Simpan file fisik
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Insert ke database
                        cur.execute("""
                            INSERT INTO dataset (nama_dataset, path_dataset, user_id, sudah_dilatih)
                            VALUES (%s, %s, %s, %s);
                        """, (uploaded_file.name, file_path, user_id, False))
                        con.commit()

                        st.session_state.upload_status = "success"
                        st.success("✅ File berhasil diunggah!")
                        st.markdown(
                            f"📁 **File disimpan di:** <span style='color:#007BFF'>{file_path}</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.session_state.upload_status = "duplicate"
                        st.warning(f"⚠️ Dataset ini sudah diupload pada path: `{file_path}`.\nSilakan rename file dataset agar tidak duplikat!")

                    # tunggu 1.5 detik lalu hilangkan uploader
                    st.session_state.show_uploader = False
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.session_state.upload_status = "error"
                    st.error(f"❌ Terjadi error: {e}")
                    time.sleep(1.5)
                    st.session_state.show_uploader = False
                    st.rerun()

    elif not st.session_state.selected_folder:
        st.warning("⚠️ Tentukan lokasi penyimpanan terlebih dahulu sebelum mengunggah dataset.")
    else:
        last_path = st.session_state.get("last_file_path", None)

        if st.session_state.upload_status == "success":
            st.success(f"✅ Upload selesai. Dataset disimpan di:\n`{last_path}`")
        elif st.session_state.upload_status == "duplicate":
            st.warning(f"⚠️ Dataset sudah ada di path:\n`{last_path}`\nSilakan rename file agar tidak duplikat!")
        elif st.session_state.upload_status == "error":
            st.error(f"❌ Terjadi kesalahan saat memproses file: `{last_path or 'tidak diketahui'}`")

else:
    st.warning("Mohon maaf terjadi kesalahan. Silahkan login kembali!")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()
