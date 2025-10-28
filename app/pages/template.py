import streamlit as st
import pandas as pd
import os, sys, time, psycopg2
import geopandas as gpd

# === 1️⃣ Akses modul session dari folder root ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from session import init_session

# === 2️⃣ Load CSS ===
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === 3️⃣ Load session ===
init_session()
logged_in = st.session_state.get("logged_in", False)
email = st.session_state.get("email", "")

st.session_state.selected_folder = ""
st.session_state.show_uploader = False
st.session_state.upload_status = None  # "success", "duplicate", "error"
st.session_state.last_file_path = None
# === 4️⃣ Konfigurasi halaman ===
st.set_page_config(page_title="Download Template Dataset", layout="wide")

# === 5️⃣ Validasi login ===
if not logged_in:
    st.warning("Terjadi kesalahan, silahkan login kembali!")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()

# === 6️⃣ Header ===
st.markdown("<h2 style='text-align:center;'>📥 Download Template Dataset</h2>", unsafe_allow_html=True)
st.write("---")

if st.button("⬅️ Kembali ke halaman sebelumnya"):
    st.switch_page("pages/upload.py")

# ===================================================================
# === 7️⃣ TEMPLATE 1 & 2 ===
st.markdown("### 🧩 Template 1 & 2 — Struktur Umum ")
col1, col2 = st.columns(2)

# ---------------------- Template 1 ----------------------
with col1:
    st.subheader("🗂️ Template 1 — Sederhana")
    st.caption("Struktur dasar: hanya label dan fitur hingga **Fitur_n**.")

    df_1 = pd.DataFrame({
        "Label": ["Label1","Label2","Label3"],
        "Fitur1": [0.0, 0.0, 0.0],
        "Fitur2": [0.0, 0.0, 0.0],
        "...": ["...", "...", "..."],
        "Fiturn": [0.0, 0.0, 0.0],
    })

    st.dataframe(df_1, use_container_width=True)
    st.download_button(
        label="📄 Unduh Template 1",
        data=df_1.to_csv(index=False).encode("utf-8"),
        file_name="template_1.csv",
        mime="text/csv",
        use_container_width=True
    )

# ---------------------- Template 2 ----------------------
with col2:
    st.subheader("🗓️ Template 2 — Dengan Tahun")
    st.caption("Struktur label + fitur per tahun hingga **Fitur_n_tahun**.")

    df_2 = pd.DataFrame({
        "Label": ["Label1","Label2",'Label3'],
        "Fitur1_2021": [0.0, 0.0, 0.0],
        "Fitur2_2021": [0.0, 0.0, 0.0],
        "Fiturn_2021": [0.0, 0.0, 0.0],
        "Fitur1_2022": [0.0, 0.0, 0.0],
        "Fiturn_2022": [0.0, 0.0, 0.0],
    })

    st.dataframe(df_2, use_container_width=True)
    st.download_button(
        label="📄 Unduh Template 2",
        data=df_2.to_csv(index=False).encode("utf-8"),
        file_name="template_2.csv",
        mime="text/csv",
        use_container_width=True
    )

# ===================================================================
# === 8️⃣ TEMPLATE 3 & 4 ===
st.markdown("---")
st.markdown("### 🌍 Template 3 & 4 — Struktur Untuk Visualisasi Peta (Kabupaten/Kota)")
col3, col4 = st.columns(2)

# ---------------------- Template 3 ----------------------
with col3:
    st.subheader("🌐 Template 3 — Kabupaten/Kota (Tanpa Tahun)")
    st.caption("Struktur umum kabupaten/kota tanpa tahun, fitur hingga **Fitur_n**.")

    df_3= pd.read_excel("..\\Dataset\\template\\template3.xlsx")
    st.dataframe(df_3, use_container_width=True)
    st.download_button(
        label="🌍 Unduh Template 3",
        data=df_3.to_csv(index=False).encode("utf-8"),
        file_name="template_3.csv",
        mime="text/csv",
        use_container_width=True
    )

# ---------------------- Template 4 ----------------------
with col4:
    st.subheader("🗺️ Template 4 — Kabupaten/Kota + Tahun")
    st.caption("Gabungan kabupaten/kota dan fitur tahunan hingga **Fitur_n_tahun**.")

    df_4= pd.read_excel("..\\Dataset\\template\\template4.xlsx")
    st.dataframe(df_4, use_container_width=True)
    st.download_button(
        label="🧭 Unduh Template 4",
        data=df_4.to_csv(index=False).encode("utf-8"),
        file_name="template_4.csv",
        mime="text/csv",
        use_container_width=True
    )


# ===================================================================
# === 9️⃣ Catatan ===
st.info("""
**Catatan:**
- Jangan merubah nama kolom "Label" atau "kab_kota
- Data yang digunakan pada template merupakan data bersih tanpa duplikat dan missing values
- Pada template 3&4 jangan mengubah isi dari pada kolom kab_kota
- Simbol `...` menunjukkan bahwa kolom dapat dilanjutkan hingga **Fitur_n** sesuai kebutuhan.
- Jika menggunakan fitur yang memiliki rentang waktu tahun, pastikan bahwa nama kolomnya adalah "Fitur_202x"
- Jika menggunakan ekstensi file .xlsx, pastikan data yang ingin ditrain ditaruh pada "Sheet1"
""")
