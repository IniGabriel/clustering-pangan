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





# === 3️⃣ Fungsi Validasi Dataset ===
def validasi_dataset(file_path):
    # === 1️⃣ Baca file sesuai tipe ===
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)

        elif file_path.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(file_path)
            if "Sheet1" not in xls.sheet_names:
                st.warning("❌ Sheet tidak bernama 'Sheet1'. Pastikan sheet utama bernama 'Sheet1'.")
                return None, False
            df = pd.read_excel(file_path, sheet_name="Sheet1")

        elif file_path.endswith(".geojson"):
            df = gpd.read_file(file_path)

        else:
            st.warning("❌ Format file tidak dikenali. Hanya mendukung .csv, .xlsx, dan .geojson.")
            st.stop()
            return None, False

    except Exception as e:
        st.warning(f"❌ Gagal membaca file: {e}")
        return None, False

    # === 2️⃣ Kolom wajib minimal salah satu ===
    has_label = "Label" in df.columns
    has_kabkota = "kab_kota" in df.columns

    if not has_label and not has_kabkota:
        st.warning("❌ Tidak ditemukan kolom 'Label' maupun 'kab_kota'. Minimal salah satu harus ada.")
        st.stop()
        return None, False
    elif has_label and has_kabkota:
        pass
    elif has_label:
        label=True
    elif has_kabkota:
        label=False

    # === 3️⃣ Tidak boleh ada duplikat / missing ===
    if df.duplicated().any():
        st.warning("⚠️ Dataset mengandung baris duplikat. Harap bersihkan data terlebih dahulu, lalu unggah dataset kembali!.")
        st.stop()
        return None, False

    if df.isnull().any().any():
        st.warning("⚠️ Dataset mengandung missing values. Harap isi atau hapus nilai kosong, lalu unggah dataset kembali!.")
        st.stop()
        return None, False
    base_names = [re.sub(r'\.\d+$', '', c) for c in df.columns]  # hapus .1, .2, dst.
    duplicate_cols = [col for col in set(base_names) if base_names.count(col) > 1]    
    if duplicate_cols:
        st.warning("⚠️ Dataset memiliki kolom fitur yang duplikat. Silahkan ubah nama kolom, lalu unggah data kembali!")
        st.stop()
    # === 5️⃣ Kolom tahun (Fitur_202x)
    fitur_tahun = [col for col in df.columns if "_202" in col]
    if fitur_tahun:
        pass
    else:
        pass

    # === 6️⃣ Tampilkan ringkasan ===
    st.write("### 📊 Ringkasan Dataset")
    st.dataframe(df.head(), use_container_width=True)
    st.caption(f"Jumlah baris: {len(df)} | Jumlah kolom: {len(df.columns)}")

    return df, True, label


#     return df_long
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
        # --- 1️⃣ Deteksi apakah ada kolom tahun (misal IKP_2021, PPH_2022)
        kolom_tahun = [col for col in df.columns if "_202" in col]

        if kolom_tahun:
            # === TEMPLATE 2: Dataset dengan kolom tahun ===
            kolom_id = [col for col in df.columns if col not in kolom_tahun]

            # Pastikan kolom penting tidak ikut dilelehkan
            for penting in ["Label", "Cluster", "Silhouette"]:
                if penting in df.columns and penting not in kolom_id:
                    kolom_id.append(penting)

            # --- Melt ke format long ---
            df_long = df.melt(
                id_vars=kolom_id,
                value_vars=kolom_tahun,
                var_name="Fitur_Tahun",
                value_name="Nilai"
            )

            # --- Pisahkan nama fitur & tahun ---
            df_long[["Fitur", "Tahun"]] = df_long["Fitur_Tahun"].str.split("_", expand=True)
            df_long.drop(columns="Fitur_Tahun", inplace=True)

        else:
            # === TEMPLATE 1: Dataset tanpa kolom tahun ===
            kolom_fitur = df.select_dtypes(include=["number"]).columns.tolist()
            kolom_id = [c for c in df.columns if c not in kolom_fitur]

            # Pastikan kolom penting tidak ikut dilelehkan
            for penting in ["Label", "Cluster", "Silhouette"]:
                if penting in df.columns and penting not in kolom_id:
                    kolom_id.append(penting)

            # --- Melt ke format long ---
            df_long = df.melt(
                id_vars=kolom_id,
                value_vars=kolom_fitur,
                var_name="Fitur",
                value_name="Nilai"
            )

            # --- Tambahkan kolom Tahun kosong agar format tetap konsisten ---
            df_long["Tahun"] = None

        # --- 2️⃣ Pastikan kolom utama tersusun rapi ---
        if "kab_kota" in df_long.columns:
            kolom_utama = ["kab_kota", "Fitur", "Tahun", "Nilai"]
        elif "Label" in df_long.columns:
            kolom_utama = ["Label", "Fitur", "Tahun", "Nilai"]
        else:
            raise ValueError("❌ Kolom utama 'kab_kota' atau 'Label' tidak ditemukan.")

        kolom_tambahan = [c for c in ["Cluster", "Silhouette", "Label"] if c in df_long.columns]
        kolom_final = kolom_utama + [c for c in kolom_tambahan if c not in kolom_utama]

        # --- 3️⃣ Susun urutan kolom ---
        df_long = df_long[kolom_final]

        # --- 4️⃣ Pastikan Cluster tetap ada jika hilang saat melt ---
        if "Cluster" not in df_long.columns and "Cluster" in df.columns:
            df_long["Cluster"] = df["Cluster"].iloc[0] if len(df) > 0 else np.nan

    except Exception as e:
        raise ValueError(f"❌ Terjadi kesalahan saat mengubah ke format long: {e}")

    return df_long


def data_wide(df_long):
    """
    Ubah dari format long (kab_kota | Fitur | Tahun | Nilai)
    kembali ke format wide (fitur_tahun jadi kolom)
    """
    df = df_long.copy()

    wajib = ["kab_kota", "Fitur", "Tahun", "Nilai"]
    if not all(c in df.columns for c in wajib):
        raise ValueError("❌ Kolom wajib belum lengkap (kab_kota, Fitur, Tahun, Nilai).")

    # --- 1️⃣ Gabungkan Fitur_Tahun ---
    df["Fitur_Tahun"] = df["Fitur"].astype(str) + "_" + df["Tahun"].astype(str)

    # --- 2️⃣ Pivot tabel ke wide ---
    df_wide = df.pivot_table(
        index="kab_kota",
        columns="Fitur_Tahun",
        values="Nilai",
        aggfunc="first"
    ).reset_index()

    # --- 3️⃣ Tambahkan kolom cluster/label kalau ada ---
    for col in ["Cluster", "Silhouette", "Label"]:
        if col in df.columns:
            nilai_unik = df.groupby("kab_kota")[col].first().reset_index()
            df_wide = df_wide.merge(nilai_unik, on="kab_kota", how="left")

    df_wide.columns.name = None
    df_wide = df_wide.sort_index(axis=1)

    return df_wide
    """
    Mengubah data long (kolom: kab_kota, Fitur, Tahun, Nilai) 
    menjadi format wide (misal kolom: PPH_2021, IKP_2022, ...)

    Output kolom: kab_kota, [fitur_tahun...], [Cluster], [Label]
    """
    df = df_long.copy()

    # --- 1️⃣ Pastikan kolom wajib ada ---
    wajib = ["kab_kota", "Fitur", "Tahun", "Nilai"]
    if not all(k in df.columns for k in wajib):
        raise ValueError("❌ Data long harus memiliki kolom: kab_kota, Fitur, Tahun, Nilai")

    # --- 2️⃣ Buat kolom gabungan Fitur_Tahun ---
    df["Fitur_Tahun"] = df["Fitur"].astype(str) + "_" + df["Tahun"].astype(str)

    # --- 3️⃣ Pivot: baris = kab_kota, kolom = Fitur_Tahun, nilai = Nilai ---
    df_wide = df.pivot_table(
        index="kab_kota",
        columns="Fitur_Tahun",
        values="Nilai",
        aggfunc="first"  # hindari duplikasi
    ).reset_index()

    # --- 4️⃣ Bawa kembali kolom Cluster/Label kalau ada ---
    for tambahan in ["Cluster", "Label"]:
        if tambahan in df.columns:
            nilai_unik = df.groupby("kab_kota")[tambahan].first().reset_index()
            df_wide = df_wide.merge(nilai_unik, on="kab_kota", how="left")

    # --- 5️⃣ Rapikan nama kolom ---
    df_wide.columns.name = None
    df_wide = df_wide.sort_index(axis=1)

    return df_wide
# === 4️⃣ Halaman utama ===
if logged_in:
    conn = get_conn()
    cur = conn.cursor()

    # Ambil user_id berdasarkan email
    cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", (email,))
    user_row = cur.fetchone()
    if not user_row:
        st.error("User tidak ditemukan di database.")
        st.stop()
    user_id = user_row[0]

    st.markdown("<h2 style='text-align:center;'>⚙️ Proses Data</h2>", unsafe_allow_html=True)
    st.write("---")

    if st.button("⬅️ Kembali ke halaman sebelumnya"):
        st.switch_page("pages/dataset.py")

    algoritma = st.selectbox("Pilih Algoritma:", ["K-Means", "AHC", "Spectral Bridges"])
    jumlah_cluster = st.slider("Pilih Jumlah Cluster:", 2, 7, 2, 1)
    tampilkan = st.button("🧠 Mulai Training")
    template_1_2 = None

    if tampilkan:
        # 1️⃣ Pastikan file ada
        if not os.path.exists(selected_dataset):
            st.error(f"⚠️ File dataset tidak ditemukan di lokasi:\n`{selected_dataset}`")
            st.info("Silakan upload ulang dataset tersebut di halaman 'Upload Dataset'.")
            cur.execute("DELETE FROM Dataset WHERE user_id = %s AND path_dataset = %s;", (user_id, selected_dataset))
            conn.commit()
            st.stop()

        # 2️⃣ Jalankan validasi
        status_placeholder = st.empty()
        with st.spinner("⏳ Sedang melatih data..."):
            df, valid, label = validasi_dataset(selected_dataset)
        # 3️⃣ Kalau gagal validasi
        if not valid:
            status_placeholder.error("❌ Gagal melatih data. Silahkan periksa kembali dan upload ulang.")
            st.stop()

        # 4️⃣ Kalau berhasil validasi
        else:
            color_map = get_color(jumlah_cluster)
            # hasil_kmeans_path = f"../Dataset/model/summary/hasil_kmeans_all_all.pkl"
            # hasil_ahc_path = f"../Dataset/model/summary/hasil_ahc_all_all.pkl"
            # hasil_sb_path = f"../Dataset/model/summary/hasil_sb_all_all.pkl"
            hasil_kmeans_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_kmeans_all_all.pkl")
            hasil_ahc_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_ahc_all_all.pkl")
            hasil_sb_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_sb_all_all.pkl")
            kolom_fitur = [col for col in df.columns if col not in ["Label", "kab_kota"]]

            scaler = minmax()
            df_scaled = pd.DataFrame(scaler.fit_transform(df[kolom_fitur]), columns=kolom_fitur)


            if algoritma == "K-Means":
                model,df_model = train_kmeans(
                    data_scaled = df_scaled,
                    hasil_kmeans_path=hasil_kmeans_path,  
                    jumlah_cluster=jumlah_cluster,    
                    data_inverse= df,    
                    kolom_fitur=kolom_fitur
                )
                table_name="model_kmeans"
            if algoritma == "AHC":
                model,df_model = train_ahc(
                    data_scaled = df_scaled,
                    hasil_ahc_path=hasil_ahc_path,  
                    jumlah_cluster=jumlah_cluster,    
                    data_inverse= df,    
                    kolom_fitur=kolom_fitur
                )
                table_name="model_ahc"
            if algoritma == "Spectral Bridges":
                model,df_model = train_sb(
                    data_scaled = df_scaled,
                    hasil_sb_path=hasil_sb_path,  
                    jumlah_cluster=jumlah_cluster,    
                    data_inverse= df,    
                    kolom_fitur=kolom_fitur
                )     
                table_name="model_sb"                
                
            df_model_copy = df_model.copy()
            kolom_fitur = [c for c in df.columns if c.lower() not in ["kab_kota","label"]]
            if any("_202" in col for col in df.columns):
                if all(re.search(r"_20(1|2)[0-9]", col) for col in kolom_fitur): 
                    df_long = data_long(df_model_copy)
                else:
                    st.warning("Template yang dipilih memiliki format fitur_tahun, namun tidak semua seperti itu. Silahkan perbaiki dan unggah dataset kembali!.")
                    st.stop()  
            else: 
                df_long = data_long(df_model_copy)
            
            if template_1_2 is not None:
                df_wide = data_wide(df_long)
            else:
                df_wide = df_model.copy()

    
            st.write("### 📊 Dataset setelah clustering")            
            st.dataframe(df_model)


            # --- Simpan 3 hasil (df_model_copy, df_long, df_wide) ke folder yang sama dengan dataset ---
           # --- Simpan 3 hasil (df_model_copy, df_long, df_wide) ke folder yang sama dengan dataset ---
            dataset_folder = os.path.dirname(selected_dataset)

            # 🔹 Ambil dataset_id dulu
            cur.execute("""
                SELECT dataset_id FROM Dataset WHERE user_id = %s AND path_dataset = %s LIMIT 1;
            """, (user_id, selected_dataset))
            row = cur.fetchone()
            dataset_id = row[0] if row else "unknown"

            namamodel1 = "df_model"
            namamodel2 = "df_long"
            namamodel3 = "df_wide"

            # 🔹 Tambahkan _dataset{dataset_id} ke nama file
            path_df_model = os.path.join(dataset_folder, f"{namamodel1}_{algoritma}_{jumlah_cluster}_dataset{dataset_id}.csv")
            path_df_long  = os.path.join(dataset_folder, f"{namamodel2}_{algoritma}_{jumlah_cluster}_dataset{dataset_id}.csv")
            path_df_wide  = os.path.join(dataset_folder, f"{namamodel3}_{algoritma}_{jumlah_cluster}_dataset{dataset_id}.csv")

            # Simpan sebagai CSV
            try:
                df_model_copy.to_csv(path_df_model, index=False)
                df_long.to_csv(path_df_long, index=False)
                df_wide.to_csv(path_df_wide, index=False)
            except Exception as e:
                st.error(f"❌ Gagal menyimpan hasil CSV: {e}")
                st.stop()


            # --- 7️⃣ Ambil metrik evaluasi dari hasil model ---
            silhouette = float(model.get("silhouette_avg", 0)) if model.get("silhouette_avg") is not None else None
            dbi = float(model.get("dbi", 0)) if model.get("dbi") is not None else None
            waktu = float(model.get("waktu_komputasi", 0)) if model.get("waktu_komputasi") is not None else None

            # --- 8️⃣ Simpan metadata hasil ke database ---
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

                    # 🔍 Cek apakah sudah ada di database
                    cur.execute(check_query, (user_id, selected_dataset, nama_model_iter))
                    sudah_ada = cur.fetchone()[0]

                    if sudah_ada:
                        continue

                    # 💾 Insert jika belum ada
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
