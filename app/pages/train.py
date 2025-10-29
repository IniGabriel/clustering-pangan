import streamlit as st
import os, sys, time, psycopg2
import pandas as pd
import geopandas as gpd
from session import init_session
from fungsi import *
from sklearn.preprocessing import MinMaxScaler as minmax
import numpy as np 
import re
from utils.db import get_conn

st.set_page_config(
    page_title="⚙️ Proses Data",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 0️⃣ Inisialisasi sesi ===
init_session()
logged_in = st.session_state.get("logged_in", False)
email = st.session_state.get("email", "")
selected_dataset = st.session_state.get("selected_dataset", None)

# === 1️⃣ Path & CSS ===
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# === 3️⃣ Fungsi Validasi Dataset (revisi sesuai permintaan) ===
def validasi_dataset(file_path):
    # === 1️⃣ Baca file sesuai tipe ===
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(file_path)
            if "Sheet1" not in xls.sheet_names:
                st.warning("❌ Sheet tidak bernama 'Sheet1'. Pastikan sheet utama bernama 'Sheet1'.")
                return None, False, None
            df = pd.read_excel(file_path, sheet_name="Sheet1")
        elif file_path.endswith(".geojson"):
            df = gpd.read_file(file_path)
        else:
            st.warning("❌ Format file tidak dikenali. Hanya mendukung .csv, .xlsx, dan .geojson.")
            st.stop()
            return None, False, None
    except Exception as e:
        st.warning(f"❌ Gagal membaca file: {e}")
        return None, False, None

    # === 2️⃣ Kolom identitas opsional ===
    label_col = None
    for kandidat in ["Label", "kab_kota", "nama", "wilayah"]:
        if kandidat in df.columns:
            label_col = kandidat
            break

    # === 3️⃣ Validasi duplikat & missing
    if df.duplicated().any():
        st.warning("⚠️ Dataset mengandung baris duplikat. Harap bersihkan data terlebih dahulu.")
        st.stop()
        return None, False, None

    if df.isnull().any().any():
        st.warning("⚠️ Dataset mengandung missing values. Harap isi atau hapus nilai kosong.")
        st.stop()
        return None, False, None

    # === 4️⃣ Pastikan ada fitur numerik
    fitur_numerik = df.select_dtypes(include=["number"]).columns.tolist()
    if len(fitur_numerik) == 0:
        st.warning("❌ Dataset tidak memiliki fitur numerik untuk dilakukan clustering.")
        st.stop()
        return None, False, None

    # === 5️⃣ Deteksi kolom duplikat
    base_names = [re.sub(r'\.\d+$', '', c) for c in df.columns]
    duplicate_cols = [col for col in set(base_names) if base_names.count(col) > 1]
    if duplicate_cols:
        st.warning(f"⚠️ Dataset memiliki kolom duplikat: {duplicate_cols}. Harap ubah nama kolomnya.")
        st.stop()
        return None, False, None

    # === 6️⃣ Tampilkan ringkasan
    st.write("### 📊 Ringkasan Dataset")
    st.dataframe(df.head(), use_container_width=True)
    st.caption(f"Jumlah baris: {len(df)} | Jumlah kolom: {len(df.columns)}")

    return df, True, label_col



# === 4️⃣ Fungsi Data Long ===
def data_long(df):
    """
    Mengubah dataset ke format long agar bisa divisualisasikan.
    Mendukung 2 tipe template:
    - Template 1: Label / kab_kota + fitur (tanpa tahun)
    - Template 2: Label / kab_kota + fitur_tahun (misal IKP_2021, PPH_2022)

    Hasil akhir memiliki kolom:
    kab_kota / Label | Fitur | Tahun | Nilai | (Cluster) | (Silhouette)
    """
    import pandas as pd
    import numpy as np

    df = df.copy()

    try:
        kolom_tahun = [col for col in df.columns if "_202" in col]

        if kolom_tahun:
            kolom_id = [col for col in df.columns if col not in kolom_tahun]
            for penting in ["data_id", "Cluster", "Silhouette"]:
                if penting in df.columns and penting not in kolom_id:
                    kolom_id.append(penting)

            df_long = df.melt(
                id_vars=kolom_id,
                value_vars=kolom_tahun,
                var_name="Fitur_Tahun",
                value_name="Nilai"
            )
            df_long[["Fitur", "Tahun"]] = df_long["Fitur_Tahun"].str.split("_", expand=True)
            df_long.drop(columns="Fitur_Tahun", inplace=True)
        else:
            kolom_fitur = df.select_dtypes(include=["number"]).columns.tolist()
            kolom_id = [c for c in df.columns if c not in kolom_fitur]
            for penting in ["data_id", "Cluster", "Silhouette"]:
                if penting in df.columns and penting not in kolom_id:
                    kolom_id.append(penting)
            df_long = df.melt(
                id_vars=kolom_id if len(kolom_id) > 0 else None,
                value_vars=kolom_fitur,
                var_name="Fitur",
                value_name="Nilai"
            )
            df_long["Tahun"] = None

        if "kab_kota" in df_long.columns:
            kolom_utama = ["kab_kota", "Fitur", "Tahun", "Nilai"]
        elif "data_id" in df_long.columns:
            kolom_utama = ["data_id", "Fitur", "Tahun", "Nilai"]
        else:
            kolom_utama = ["Fitur", "Tahun", "Nilai"]

        kolom_tambahan = [c for c in ["Cluster", "Silhouette", "data_id"] if c in df_long.columns]
        kolom_final = kolom_utama + [c for c in kolom_tambahan if c not in kolom_utama]

        df_long = df_long[kolom_final]
        if "Cluster" not in df_long.columns and "Cluster" in df.columns:
            df_long["Cluster"] = df["Cluster"].iloc[0] if len(df) > 0 else np.nan

    except Exception as e:
        raise ValueError(f"❌ Terjadi kesalahan saat mengubah ke format long: {e}")

    return df_long



# === 5️⃣ Fungsi Data Wide ===
def data_wide(df_long):
    """
    Ubah dari format long (kab_kota | Fitur | Tahun | Nilai)
    kembali ke format wide (fitur_tahun jadi kolom)
    """
    df = df_long.copy()
    wajib = ["Fitur", "Tahun", "Nilai"]

    for w in wajib:
        if w not in df.columns:
            raise ValueError(f"❌ Kolom wajib '{w}' tidak ditemukan di dataset long.")

    if "kab_kota" in df.columns:
        index_col = "kab_kota"
    elif "Label" in df.columns:
        index_col = "Label"
    else:
        index_col = None

    df["Fitur_Tahun"] = df["Fitur"].astype(str) + "_" + df["Tahun"].astype(str)
    if index_col:
        df_wide = df.pivot_table(index=index_col, columns="Fitur_Tahun", values="Nilai", aggfunc="first").reset_index()
    else:
        df_wide = df.pivot_table(columns="Fitur_Tahun", values="Nilai", aggfunc="first").reset_index()

    for col in ["Cluster", "Silhouette", "Label"]:
        if col in df.columns and index_col:
            nilai_unik = df.groupby(index_col)[col].first().reset_index()
            df_wide = df_wide.merge(nilai_unik, on=index_col, how="left")

    df_wide.columns.name = None
    df_wide = df_wide.sort_index(axis=1)
    return df_wide



# === 6️⃣ Halaman utama ===
if logged_in:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", (email,))
    user_row = cur.fetchone()
    if not user_row:
        st.error("Terjadi kesalahan silahkan login kembali.")
        for key in ["logged_in", "username", "email"]:
            if key in st.session_state:
                del st.session_state[key]           
        time.sleep(1.5)
        st.switch_page("home.py")
        st.stop()
    user_id = user_row[0]

    st.markdown("<h2 style='text-align:center;'>⚙️ Proses Data</h2>", unsafe_allow_html=True)
    st.write("---")

    if st.button("⬅️ Kembali ke halaman sebelumnya"):
        st.switch_page("pages/dataset.py")

    algoritma = st.selectbox("Pilih Algoritma:", ["K-Means", "AHC", "Spectral Bridges"])
    jumlah_cluster = st.slider("Pilih Jumlah Cluster:", 2, 7, 2, 1)
    tampilkan = st.button("⚙️ Proses Data")
    template_1_2 = None

    if tampilkan:
        if not os.path.exists(selected_dataset):
            st.error(f"⚠️ File dataset tidak ditemukan di lokasi:\n`{selected_dataset}`")
            st.info("Silakan upload ulang dataset tersebut di halaman 'Upload Dataset'.")
            cur.execute("DELETE FROM Dataset WHERE user_id = %s AND path_dataset = %s;", (user_id, selected_dataset))
            conn.commit()
            st.stop()

        status_placeholder = st.empty()
        with st.spinner("⏳ Sedang melatih data..."):
            df, valid, label_col = validasi_dataset(selected_dataset)
        if not valid:
            status_placeholder.error("❌ Gagal melatih data. Silahkan periksa kembali dan upload ulang.")
            st.stop()

        else:
            color_map = get_color(jumlah_cluster)
            hasil_kmeans_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_kmeans_all_all.pkl")
            hasil_ahc_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_ahc_all_all.pkl")
            hasil_sb_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_sb_all_all.pkl")

            if label_col:
                kolom_fitur = [col for col in df.columns if col != label_col]
            else:
                kolom_fitur = df.select_dtypes(include=["number"]).columns.tolist()

            scaler = minmax()
            df_scaled = pd.DataFrame(scaler.fit_transform(df[kolom_fitur]), columns=kolom_fitur)

            if algoritma == "K-Means":
                model, df_model = train_kmeans(
                    data_scaled=df_scaled,
                    hasil_kmeans_path=hasil_kmeans_path,
                    jumlah_cluster=jumlah_cluster,
                    data_inverse=df,
                    kolom_fitur=kolom_fitur
                )
                table_name = "model_kmeans"
            elif algoritma == "AHC":
                model, df_model = train_ahc(
                    data_scaled=df_scaled,
                    hasil_ahc_path=hasil_ahc_path,
                    jumlah_cluster=jumlah_cluster,
                    data_inverse=df,
                    kolom_fitur=kolom_fitur
                )
                table_name = "model_ahc"
            else:
                model, df_model = train_sb(
                    data_scaled=df_scaled,
                    hasil_sb_path=hasil_sb_path,
                    jumlah_cluster=jumlah_cluster,
                    data_inverse=df,
                    kolom_fitur=kolom_fitur
                )
                table_name = "model_sb"

            df_model_copy = df_model.copy()
            kolom_fitur = [c for c in df.columns if c.lower() not in ["kab_kota","label"]]
            if any("_202" in col for col in df.columns):
                if all(re.search(r"_20(1|2)[0-9]", col) for col in kolom_fitur):
                    df_long = data_long(df_model_copy)
                else:
                    st.warning("Template yang dipilih memiliki format fitur_tahun, namun tidak semua seperti itu.")
                    st.stop()
            else:
                df_long = data_long(df_model_copy)
            
            if template_1_2 is not None:
                df_wide = data_wide(df_long)
            else:
                df_wide = df_model.copy()

            st.write("### 📊 Dataset setelah clustering")            
            st.dataframe(df_model)
            # === Tombol Unduh Dataset Hasil Klaster ===
            csv = df_model.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Unduh Dataset Hasil Klaster",
                data=csv,
                file_name=f"hasil_klaster_{algoritma}_{jumlah_cluster}.csv",
                mime="text/csv",
                help="Klik untuk mengunduh dataaset hasil clustering"
            )


            # simpan hasil dan metadata
            dataset_folder = os.path.dirname(selected_dataset)
            cur.execute("""
                SELECT dataset_id FROM Dataset WHERE user_id = %s AND path_dataset = %s LIMIT 1;
            """, (user_id, selected_dataset))
            row = cur.fetchone()
            dataset_id = row[0] if row else "unknown"

            namamodel1, namamodel2, namamodel3 = "df_model", "df_long", "df_wide"
            path_df_model = os.path.join(dataset_folder, f"{namamodel1}_{algoritma}_{jumlah_cluster}_dataset{dataset_id}.csv")
            path_df_long  = os.path.join(dataset_folder, f"{namamodel2}_{algoritma}_{jumlah_cluster}_dataset{dataset_id}.csv")
            path_df_wide  = os.path.join(dataset_folder, f"{namamodel3}_{algoritma}_{jumlah_cluster}_dataset{dataset_id}.csv")

            try:
                df_model_copy.to_csv(path_df_model, index=False)
                df_long.to_csv(path_df_long, index=False)
                df_wide.to_csv(path_df_wide, index=False)
            except Exception as e:
                st.error(f"❌ Gagal menyimpan hasil CSV: {e}")
                st.stop()

            silhouette = float(model.get("silhouette_avg", 0)) if model.get("silhouette_avg") is not None else None
            dbi = float(model.get("dbi", 0)) if model.get("dbi") is not None else None
            waktu = float(model.get("waktu_komputasi", 0)) if model.get("waktu_komputasi") is not None else None

            try:
                insert_query = f"""
                    INSERT INTO {table_name}
                    (nama_model, path_model, jumlah_cluster, silhouette, dbi, waktu_komputasi, user_id, dataset_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s,
                        (SELECT dataset_id FROM Dataset WHERE user_id = %s AND path_dataset = %s LIMIT 1)
                    );
                """
                check_query = f"""
                    SELECT EXISTS (
                        SELECT 1 FROM {table_name} m
                        JOIN Dataset d ON m.dataset_id = d.dataset_id
                        WHERE m.user_id = %s 
                        AND d.path_dataset = %s 
                        AND m.nama_model = %s
                    );
                """
                model_files = [
                    ("df_model", path_df_model),
                    ("df_long", path_df_long),
                    ("df_wide", path_df_wide)
                ]
                for nama, path_iter in model_files:
                    nama_model_iter = f"{nama}_{algoritma}_{jumlah_cluster}"
                    cur.execute(check_query, (user_id, selected_dataset, nama_model_iter))
                    sudah_ada = cur.fetchone()[0]
                    if sudah_ada:
                        continue
                    cur.execute(insert_query, (
                        nama_model_iter,
                        path_iter,
                        jumlah_cluster,
                        silhouette,
                        dbi,
                        waktu,
                        user_id,
                        user_id,
                        selected_dataset
                    ))
                conn.commit()
                cur.execute("""
                    UPDATE Dataset
                    SET sudah_dilatih = TRUE
                    WHERE user_id = %s AND path_dataset = %s;
                """, (user_id, selected_dataset))
                conn.commit()
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Gagal menyimpan metadata model ke database: {e}")
            status_placeholder.success("✅ Data berhasil diklaster!")

else:
    st.warning("Mohon maaf terjadi kesalahan. Silahkan login kembali!")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()
