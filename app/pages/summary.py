# pages/summary.py
import os
import pandas as pd
import streamlit as st

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Summary", layout="wide")

# -------------------- SESSION (sesuaikan dengan punyamu) --------------------
logged_in = st.session_state.get("logged_in", False)
username = st.session_state.get("username", "User")

current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# -------------------- NAVBAR --------------------
if logged_in:
    cols = st.columns(7)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)
    with cols[1]:
        st.page_link("home.py", label="Home")
    with cols[2]:
        st.page_link("pages/upload.py", label="Upload Dataset")
    with cols[3]:
        st.page_link("pages/visualization.py", label="Visualization")
    with cols[4]:
        st.page_link("pages/about.py",label='About')
    with cols[5]:
        st.write(f"Halo, {username} 👋")
    with cols[6]:
        if st.button("Logout"):
            for k in ["logged_in", "username", "email"]:
                st.session_state.pop(k, None)
            st.switch_page("home.py")
else:
    cols = st.columns(5)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)
    with cols[1]:
        st.page_link("home.py", label="Home")
    with cols[2]:
        st.page_link("pages/visualization.py", label="Visualization")
    with cols[3]:
        st.page_link("pages/about.py",label='About')
    with cols[4]:
        st.page_link("pages/login.py", label="Login")

# -------------------- MAIN CONTENT --------------------
st.title("📊 Ringkasan (Top 10 Silhouette)")

st.info("Silakan pilih **minimal 1 algoritma** lalu klik **Lihat Hasil**. "
        "Tabel akan menampilkan 10 konfigurasi terbaik berdasarkan Silhouette (descending).")

algoritma_opsi = ["K-Means", "Agglomerative (AHC)", "Spectral Bridges"]
pilihan = st.multiselect(
    "Pilih algoritma:",
    options=algoritma_opsi,
    default=[],
    max_selections=3,
    help="Kamu bisa memilih 1–3 algoritma."
)

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

file_map = {
    # "K-Means": os.path.join(BASE_DIR, "summary", "kmeans", "kmeans.xlsx"),
    # "Agglomerative (AHC)": os.path.join(BASE_DIR, "summary","ahc", "ahc.xlsx"),
    # "Spectral Bridges": os.path.join(BASE_DIR, "summary","sb", "sb.xlsx"),
    "K-Means": os.path.join(current_dir, "..","summary","kmeans", "kmeans.xlsx"),
    "Agglomerative (AHC)": os.path.join(current_dir, "..","summary","ahc", "ahc.xlsx"),
    "Spectral Bridges": os.path.join(current_dir, "..","summary","sb", "sb.xlsx")
}

# Helper: cari nama kolom silhouette yang valid
def find_silhouette_col(columns):
    cols = [c.strip() for c in columns]
    # kandidat nama yang sering muncul
    candidates = [
        "Silhouette", "Silhouette Avg", "Silhouette Score",
        # toleransi typo
        "ilhouette", "ilouette", "Silouette", "Silhoutte"
    ]
    for cand in candidates:
        for c in cols:
            if cand.lower() in c.lower():
                return c
    # fallback: cari yang mengandung 'sil'
    for c in cols:
        if "sil" in c.lower():
            return c
    return None

# Helper: paksa kolom numeric (kalau angka pakai koma)
def coerce_numeric(series):
    if series.dtype == "O":
        # ganti koma jadi titik, hapus spasi
        s = series.astype(str).str.replace(",", ".", regex=False).str.strip()
        return pd.to_numeric(s, errors="coerce")
    return pd.to_numeric(series, errors="coerce")

# -------------------- ACTION BUTTON --------------------
if st.button("🔍 Lihat Hasil", use_container_width=False):
    if not pilihan:
        st.warning("⚠️ Silakan pilih minimal **1** algoritma terlebih dahulu.")
    else:
        for algo in pilihan:
            st.subheader(f"🏆 Top 10 Hasil Terbaik: {algo}")

            file_path = file_map.get(algo)
            if not file_path or not os.path.exists(file_path):
                st.error(f"❌ File untuk {algo} tidak ditemukan: `{file_path}`")
                continue

            try:
                # --- Load Excel ---
                df = pd.read_excel(file_path)
                # Normalisasi nama kolom
                df.columns = df.columns.str.strip()

                # Temukan kolom silhouette
                sil_col = find_silhouette_col(df.columns)
                if not sil_col:
                    st.error(f"Kolom 'Silhouette' tidak ditemukan di file: `{file_path}`")
                    continue

                # Pastikan kolom numeric
                df[sil_col] = coerce_numeric(df[sil_col])

                # Sort desc & ambil top 10
                df_sorted = df.sort_values(by="Silhouette", ascending=False).head(10)

                # Sembunyikan kolom 'Metode' jika ada
                if "Metode" in df_sorted.columns:
                    df_sorted = df_sorted.drop(columns=["Metode"])

                # Reset index 1..10 (bukan index Excel)
                df_sorted = df_sorted.reset_index(drop=True)
                df_sorted.index = df_sorted.index + 1
                df_sorted.index.name = "Urutan"

                # Tampilkan tabel
                st.dataframe(df_sorted, use_container_width=True)

            except Exception as e:
                st.error(f"Gagal memuat data {algo}: {e}")
