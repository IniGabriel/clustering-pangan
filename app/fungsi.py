import os, sys, pickle
import streamlit as st
import pandas as pd
import time

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples, davies_bouldin_score
from sklearn.cluster import AgglomerativeClustering
from spectralbridges import SpectralBridges


def get_kolom_fitur(indikator_list, tahun_label, tahun):
    indikator_semua = ['PPH', 'IKP', 'AKE', 'AKP']
    tahun_semua = ['2021', '2022', '2023']

    if tahun_label == '2021':
        tahun_dipakai = ['2021']
    elif tahun_label == '2022':
        tahun_dipakai = ['2022']
    elif tahun_label == '2023':
        tahun_dipakai = ['2023']
    elif tahun_label == '2021–2022':
        tahun_dipakai = ['2021', '2022']
    elif tahun_label == '2022–2023':
        tahun_dipakai = ['2022', '2023']
    elif tahun_label == 'Semua Tahun':
        tahun_dipakai = tahun_semua
    else:
        tahun_dipakai = []

    if 'Semua Indikator' in indikator_list or len(indikator_list) == 0:
        indikator_dipakai = indikator_semua
    else:
        indikator_dipakai = indikator_list
    indikator_dipakai = sorted(indikator_dipakai)

    kolom_fitur = [f"{indikator}_{tahun}" for indikator in indikator_dipakai for tahun in tahun_dipakai]

    return kolom_fitur

def inverse(data_scaled,scaler):
    df=data_scaled.copy()
    if scaler is not None:
        try:
            kolom_fitur = ['PPH_2021','PPH_2022','PPH_2023',
               'IKP_2021','IKP_2022','IKP_2023',
               'AKE_2021','AKE_2022','AKE_2023',
               'AKP_2021','AKP_2022','AKP_2023']
            df[kolom_fitur] = scaler.inverse_transform(df[kolom_fitur])
            print("✅ Nilai fitur berhasil dikembalikan ke skala asli!")
            return df
        except Exception as e:
            print(f"⚠️ Gagal inverse transform: {e}")

def train_kmeans(data_scaled, hasil_kmeans_path, jumlah_cluster, data_scaled_null = None, data_inverse = None, tahun =None,kolom_fitur=None):
    if not hasil_kmeans_path or not os.path.exists(hasil_kmeans_path):
        st.error(f"❌ File hasil_kmeans.pkl tidak ditemukan di: {hasil_kmeans_path}")
        return None, None

    with open(hasil_kmeans_path, "rb") as f:
        hasil_kmeans = pickle.load(f)

    if isinstance(hasil_kmeans, pd.DataFrame):
        hasil_kmeans = hasil_kmeans.to_dict(orient="records")
    kandidat = [x for x in hasil_kmeans if x.get("Jumlah Cluster") == jumlah_cluster]
    if not kandidat:
        st.error(f"⚠️ Tidak ada data dengan Jumlah Cluster = {jumlah_cluster} di hasil_kmeans.pkl")
        return None, None

    random_state = kandidat[0].get("Random State", 42)
    X = data_scaled[kolom_fitur]

    start = time.time()
    kmeans = KMeans(
        n_clusters=jumlah_cluster,
        random_state=random_state,
        n_init=10
    )
    kmeans.fit(X)
    end = time.time()

    labels_kmeans = kmeans.labels_
    silhouette_avg_kmeans = silhouette_score(X, labels_kmeans)
    silhouette_vals_kmeans = silhouette_samples(X, labels_kmeans)
    dbi_kmeans = davies_bouldin_score(X, labels_kmeans)
    durasi_kmeans = end - start

    kmeans_result = {
        "model": kmeans,
        "metode":"K-Means",
        "n_clusters": jumlah_cluster,
        "random_state": random_state,
        "labels": labels_kmeans,
        "silhouette_avg": round(silhouette_avg_kmeans, 4),
        "silhouette_vals": silhouette_vals_kmeans.round(4),
        "dbi": round(dbi_kmeans, 4),
        "waktu_komputasi": round(durasi_kmeans, 4)
    }

    data_kmeans = data_scaled.copy()
    data_kmeans["Cluster"] = labels_kmeans
    data_kmeans["Silhouette"] = silhouette_vals_kmeans.round(3)

    if data_scaled_null is not None:
        data_kmeans_final = pd.concat([data_kmeans, data_scaled_null], ignore_index=True)
    else:
        data_kmeans_final = data_kmeans.copy()

    try:
        for col in kolom_fitur:
            if col in data_kmeans_final.columns and col in data_inverse.columns:
                data_kmeans_final[col] = data_inverse[col]
        print("✅ Nilai fitur pada data_kmeans_final berhasil diganti dengan data inverse (skala asli).")
    except Exception as e:
        print(f"⚠️ Gagal mengganti nilai fitur dengan data inverse: {e}")

    fitur_unik = sorted(list({c.split("_")[0] for c in kolom_fitur}))

    # --- 💾 Simpan ringkasan hasil ke Excel ---
    data_to_save = {
        "Metode": [kmeans_result["metode"]],
        "Jumlah Cluster":jumlah_cluster,
        "Tahun": [tahun],
        "Fitur": [", ".join(fitur_unik)],  # gabung biar rapi di satu kolom
        "Silhouette Avg": [kmeans_result["silhouette_avg"]],
        "DBI": [kmeans_result["dbi"]],
        "Waktu Komputasi (detik)": [kmeans_result["waktu_komputasi"]]
    }

    if data_scaled_null is not None:
        df_result = pd.DataFrame(data_to_save)

        # Buat nama file aman (hilangkan karakter tak valid)
        fitur_str = "_".join(fitur_unik)
        output_filename = f"hasil_kmeans_{jumlah_cluster}_{tahun}_{fitur_str}.xlsx"

        # df_result.to_excel(output_filename, index=False)
    # cari kolom identitas yang ada
    if data_scaled_null is None:
            try:
                data_kmeans_final["kab_kota"] = data_inverse["kab_kota"].values    
            except:
                if not any(col.lower() in ["kab_kota"] for col in data_kmeans_final.columns):
                    data_kmeans_final.insert(0, "data_id", range(1, len(data_kmeans_final) + 1))

    return kmeans_result, data_kmeans_final

def train_ahc(data_scaled, hasil_ahc_path, jumlah_cluster, data_inverse=None, tahun=None,data_scaled_null = None,kolom_fitur=None): 
    start = time.time()
    ahc = AgglomerativeClustering(
        n_clusters=jumlah_cluster,
        linkage='ward'
    )
    X = data_scaled[kolom_fitur]    
    labels_ahc = ahc.fit_predict(X)

    silhouette_avg_ahc = silhouette_score(X, labels_ahc)
    silhouette_vals_ahc = silhouette_samples(X, labels_ahc)
    dbi_ahc = davies_bouldin_score(X, labels_ahc)
    end = time.time()
    waktu = end-start
    ahc_result = {
        "model": ahc,
        "metode":"AHC",
        "n_clusters": jumlah_cluster,
        "labels": labels_ahc,
        "silhouette_avg": round(silhouette_avg_ahc, 4),
        "silhouette_vals": silhouette_vals_ahc.round(4),
        "dbi": round(dbi_ahc, 4),
        "waktu_komputasi":waktu
    }    
    data_ahc = data_scaled.copy()
    data_ahc["Cluster"] = labels_ahc
    data_ahc["Silhouette"] = silhouette_vals_ahc.round(3)

    if data_scaled_null is not None:
        data_ahc_final = pd.concat([data_ahc, data_scaled_null], ignore_index=True)   
    else:
        data_ahc_final = data_ahc.copy() 

    for col in kolom_fitur:
        if col in data_ahc_final.columns and col in data_inverse.columns:
            data_ahc_final[col] = data_inverse[col]    
    
    fitur_unik = sorted(list({c.split("_")[0] for c in kolom_fitur}))

    # --- 💾 Simpan ringkasan hasil ke Excel ---
    data_to_save = {
        "Metode": "AHC",
        "Jumlah Cluster":jumlah_cluster,
        "Tahun": [tahun],
        "Fitur": [", ".join(fitur_unik)],  # gabung biar rapi di satu kolom
        "Silhouette Avg": [ahc_result["silhouette_avg"]],
        "DBI": [ahc_result["dbi"]],
        "Waktu Komputasi (detik)": [ahc_result["waktu_komputasi"]]
    }

    if data_scaled_null is not None:
        df_result = pd.DataFrame(data_to_save)

        # Buat nama file aman (hilangkan karakter tak valid)
        fitur_str = "_".join(fitur_unik)
        output_filename = f"hasil_ahc_{jumlah_cluster}_{tahun}_{fitur_str}.xlsx"

        # df_result.to_excel(output_filename, index=False)
    if data_scaled_null is None:
            try:
                data_ahc_final["kab_kota"] = data_inverse["kab_kota"].values    
            except:
                if not any(col.lower() in ["kab_kota"] for col in data_ahc_final.columns):
                    data_ahc_final.insert(0, "data_id", range(1, len(data_ahc_final) + 1))    


    return ahc_result, data_ahc_final

def train_sb(data_scaled, hasil_sb_path, jumlah_cluster, data_inverse=None, tahun=None, data_scaled_null=None, kolom_fitur=None):
    with open(hasil_sb_path, "rb") as f:
        hasil_sb = pickle.load(f)

    X = data_scaled[kolom_fitur]

    kandidat = [x for x in hasil_sb if x.get("Jumlah Cluster") == jumlah_cluster]
    if not kandidat:
        st.error(f"⚠️ Tidak ada data dengan Jumlah Cluster = {jumlah_cluster} di hasil_sb.pkl")
        return None, None

    random_state_file = kandidat[0].get("Random State")

    fallback_states = [random_state_file, 76, 75, 42,2,13,25]
    model_sb, labels_sb = None, None

    for rs in fallback_states:
        try:
            start = time.time()
            if  jumlah_cluster == 2 and len(kolom_fitur) >3:
                rs = 18
            model_sb = SpectralBridges(
                n_clusters=jumlah_cluster,
                n_nodes=60,
                p=1,
                random_state=rs
            )
            model_sb.fit(X)
            labels_sb = model_sb.predict(X)
            end = time.time()
            waktu = end - start
            break
        except Exception as e:
            continue


    silhouette_avg_sb = silhouette_score(X, labels_sb)
    silhouette_vals_sb = silhouette_samples(X, labels_sb)
    dbi_sb = davies_bouldin_score(X, labels_sb)

    sb_result = {
        "model": model_sb,
        "metode": "Spectral Bridges",
        "n_clusters": jumlah_cluster,
        "random_state": rs,
        "n_nodes": 60,
        "labels": labels_sb,
        "silhouette_avg": round(silhouette_avg_sb, 4),
        "silhouette_vals": silhouette_vals_sb.round(4),
        "dbi": round(dbi_sb, 4),
        "waktu_komputasi": waktu
    }

    # === Gabungkan hasil ke DataFrame ===
    data_sb = data_scaled.copy()
    data_sb["Cluster"] = labels_sb
    data_sb["Silhouette"] = silhouette_vals_sb.round(3)

    if data_scaled_null is not None:
        data_sb_final = pd.concat([data_sb, data_scaled_null], ignore_index=True)
    else:
        data_sb_final = data_sb.copy()

    for col in kolom_fitur:
        if col in data_sb_final.columns and col in data_inverse.columns:
            data_sb_final[col] = data_inverse[col]

    fitur_unik = sorted(list({c.split("_")[0] for c in kolom_fitur}))

    data_to_save = {
        "Metode": "Spectral Bridges",
        "Jumlah Cluster": jumlah_cluster,
        "Tahun": [tahun],
        "Fitur": [", ".join(fitur_unik)],
        "Silhouette Avg": [sb_result["silhouette_avg"]],
        "DBI": [sb_result["dbi"]],
        "Waktu Komputasi (detik)": [sb_result["waktu_komputasi"]]
    }

    if data_scaled_null is not None:
        df_result = pd.DataFrame(data_to_save)
        fitur_str = "_".join(fitur_unik)
        output_filename = f"hasil_sb_{jumlah_cluster}_{tahun}_{fitur_str}.xlsx"
        # df_result.to_excel(output_filename, index=False)

    if data_scaled_null is None:
            try:
                data_sb_final["kab_kota"] = data_inverse["kab_kota"].values    
            except:
                if not any(col.lower() in ["kab_kota"] for col in data_sb_final.columns):
                    data_sb_final.insert(0, "data_id", range(1, len(data_sb_final) + 1))

    return sb_result, data_sb_final

def data_pivot_awal(data_asli, kolom_fitur, scaler=None):
    df = data_asli.copy()

    if scaler is not None:
        try:
            df[kolom_fitur] = scaler.inverse_transform(df[kolom_fitur])
            print("✅ Nilai fitur berhasil dikembalikan ke skala asli!")
        except Exception as e:
            print(f"⚠️ Gagal inverse transform: {e}")

    kolom_tahun = [col for col in df.columns if "_202" in col]
    if not kolom_tahun:
        raise ValueError("Tidak ditemukan kolom tahun seperti PPH_2021, IKP_2022, dll.")

    df_long = df.melt(
        id_vars=[col for col in df.columns if col not in kolom_tahun],
        value_vars=kolom_tahun,
        var_name="Fitur_Tahun",
        value_name="Nilai"
    )

    df_long[["Fitur", "Tahun"]] = df_long["Fitur_Tahun"].str.split("_", expand=True)
    df_long.drop(columns="Fitur_Tahun", inplace=True)

    kolom_final = ["kab_kota", "Fitur", "Tahun", "Nilai"]
    df_long = df_long[[col for col in kolom_final if col in df_long.columns]]

    if "geometry" in df_long.columns:
        df_long = df_long.drop(columns=["geometry"])

    if df_long["Nilai"].isnull().all():
        print("⚠️ Semua nilai kolom 'Nilai' kosong, periksa data sumber atau scaler.")
    return df_long

def buat_data_boxplot(data_algoritma, kolom_fitur):
    df = data_algoritma.copy()
    df = df.drop_duplicates(subset="geometry",keep='first')          

    kolom_tahun = [col for col in df.columns if "_202" in col]
    if not kolom_tahun:
        raise ValueError("Tidak ditemukan kolom tahun seperti PPH_2021, IKP_2022, dll.")

    df_long = df.melt(
        id_vars=[col for col in df.columns if col not in kolom_tahun],
        value_vars=kolom_tahun,
        var_name="Fitur_Tahun",
        value_name="Nilai"
    )
    
    df_long[["Fitur", "Tahun"]] = df_long["Fitur_Tahun"].str.split("_", expand=True)
    df_long.drop(columns="Fitur_Tahun", inplace=True)

    kolom_final = ["kab_kota", "Fitur", "Tahun", "Nilai", "Cluster", "Label"]
    df_long = df_long[[col for col in kolom_final if col in df_long.columns]]

    if "geometry" in df_long.columns:
        df_long = df_long.drop(columns=["geometry"])

    if df_long["Nilai"].isnull().all():
        print("⚠️ Semua nilai kolom 'Nilai' kosong, periksa data sumber.")
    print("len df akhir ==== ",len(df_long))
    return df_long

def tambah_label_cluster(df,jumlah_cluster,mean):
    df = df.copy()
    mean["Rata2"] = mean.mean(axis=1)
    mean_sorted = mean["Rata2"].sort_values(ascending=True)
    urutan_cluster = list(mean_sorted.index)  # misal [2, 0, 1]

    if jumlah_cluster == 2:
        label_urutan = ["Ketahanan Pangan Rendah", "Ketahanan Pangan Tinggi"]
    elif jumlah_cluster == 3:
        label_urutan = ["Ketahanan Pangan Rendah", "Ketahanan Pangan Sedang", "Ketahanan Pangan Tinggi"]
    elif jumlah_cluster ==4:
        label_urutan = ["Ketahanan Pangan Rendah", "Ketahanan Pangan Sedang", "Ketahanan Pangan Tinggi", "Ketahanan Pangan Sangat Tinggi"]
    elif jumlah_cluster ==5:
        label_urutan = ["Ketahanan Pangan Sangat Rendah","Ketahanan Pangan Rendah", "Ketahanan Pangan Sedang", "Ketahanan Pangan Tinggi", "Ketahanan Pangan Sangat Tinggi"]
    else:
        # fallback: misal 4+ cluster, buat label umum
        label_urutan = [f"{i+1}" for i in range(jumlah_cluster)]

    mapping = {cluster_id: label_urutan[i] for i, cluster_id in enumerate(urutan_cluster)}

    df["Label"] = df["Cluster"].map(mapping)

    df["Label"] = df["Label"].fillna("Undefined")
    return df

def get_color(jumlah_cluster):

    if jumlah_cluster <= 4:

        warna_palette = [
            "#1B5E20",  
            "#4CAF50", 
            "#F57C00",  
            "#D32F2F",  
        ]
    else:
        warna_palette = [
            "#4CAF50",  
            "#1B5E20",
            "#0288D1",
            "#7B1FA2", 
            "#FBC02D",  
            "#F57C00", 
            "#D32F2F",  
        ]



    color_map = {i: warna_palette[i % len(warna_palette)] for i in range(jumlah_cluster)}
    color_map["Undefined"] = "#A9A9A9"

    return color_map








import os, numpy as np
import time
import pickle
import itertools
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import streamlit as st
from fungsi import get_kolom_fitur  # pakai fungsi yang sudah ada di proyekmu

# === KONFIGURASI DASAR ===
MODEL_DIR = "../Dataset/model/summary"
DATA_DIR = "../Dataset/pre"
HASIL_KMEANS_PATH = os.path.join(MODEL_DIR, "hasil_kmeans_all_all.pkl")
HASIL_SB_PATH = os.path.join(MODEL_DIR, "hasil_sb_all_all.pkl")

TAHUN_LIST = ["2021", "2022", "2023", "2021–2022", "2022–2023", "Semua Tahun"]
CLUSTER_RANGE = [2, 3, 4, 5, 6, 7]
INDIKATOR_LIST = ["IKP", "PPH", "AKE", "AKP"]

def _ambil_random_state(hasil_kmeans_list, k):
    kandidat = [x for x in hasil_kmeans_list if x.get("Jumlah Cluster") == k]
    return kandidat[0].get("Random State", 42) if kandidat else 42


def train_all_kmeans_excel():
    """
    Latih KMeans untuk cluster 4–7 dan semua tahun,
    simpan 1 file Excel per cluster (4 file total).
    Tiap file berisi 6 tahun × 15 kombinasi fitur = 90 baris.
    """
    st.info("🚀 Memulai pelatihan otomatis K-Means (4–7 cluster, 6 tahun, 15 kombinasi fitur)...")

    # --- Load data scaled (sudah di-scale) ---
    df_scaled = gpd.read_file(os.path.join(DATA_DIR, "data_scaled.geojson"))

    # --- Baca hasil_kmeans.pkl untuk ambil random_state per jumlah cluster ---
    with open(HASIL_KMEANS_PATH, "rb") as f:
        hasil_kmeans = pickle.load(f)
    if isinstance(hasil_kmeans, pd.DataFrame):
        hasil_kmeans = hasil_kmeans.to_dict(orient="records")

    total_tasks = len(CLUSTER_RANGE) * len(TAHUN_LIST) * 15  # 15 kombinasi per tahun
    task_done = 0
    progress = st.progress(0)

    for k in CLUSTER_RANGE:
        rs = _ambil_random_state(hasil_kmeans, k)
        semua_hasil = []

        for tahun in TAHUN_LIST:
            for r in range(1, len(INDIKATOR_LIST) + 1):
                for comb in itertools.combinations(INDIKATOR_LIST, r):
                    indikator_sub = list(comb)
                    kolom_fitur = get_kolom_fitur(indikator_sub, tahun, tahun)
                    X = df_scaled[kolom_fitur]

                    start = time.time()
                    kmeans = KMeans(n_clusters=k, random_state=rs, n_init=10)
                    kmeans.fit(X)
                    dur = time.time() - start

                    sil = silhouette_score(X, kmeans.labels_)
                    dbi = davies_bouldin_score(X, kmeans.labels_)

                    semua_hasil.append({
                        "Metode": "K-Means",
                        "Jumlah Cluster": k,
                        "Tahun": tahun,
                        "Fitur": ", ".join(indikator_sub),
                        "Silhouette": round(sil, 4),
                        "DBI": round(dbi, 4),
                        "Waktu Komputasi (detik)": round(dur, 4)
                    })

                    task_done += 1
                    progress.progress(task_done / total_tasks)

        df_out = pd.DataFrame(semua_hasil)
        fname = f"hasil_kmeans_cluster{k}_semua_tahun.xlsx"
        fpath = os.path.join(MODEL_DIR, fname)
        df_out.to_excel(fpath, index=False)
        st.write(f"✅ File tersimpan: {fpath}")

    st.success("🎉 Selesai! 4 file Excel dibuat.")


def train_all_sb_excel():
    """
    Latih Spectral Bridges untuk cluster 2–7 dan semua tahun,
    simpan 1 file Excel per cluster (total 6 file).
    Tiap file berisi 6 tahun × 15 kombinasi fitur = 90 baris.
    """
    st.info("🚀 Memulai pelatihan otomatis Spectral Bridges (2–7 cluster, semua tahun, 15 kombinasi fitur)...")

    df_scaled = gpd.read_file(os.path.join(DATA_DIR, "data_scaled.geojson"))

    total_tasks = len(CLUSTER_RANGE) * len(TAHUN_LIST) * 15
    task_done = 0
    progress = st.progress(0)

    # === Load hasil_sb.pkl untuk ambil random_state ===
    with open(HASIL_SB_PATH, "rb") as f:
        hasil_sb = pickle.load(f)
    if isinstance(hasil_sb, pd.DataFrame):
        hasil_sb = hasil_sb.to_dict(orient="records")

    for k in CLUSTER_RANGE:
        rs = _ambil_random_state(hasil_sb, k)
        semua_hasil = []

        for tahun in TAHUN_LIST:
            for r in range(1, len(INDIKATOR_LIST) + 1):
                for comb in itertools.combinations(INDIKATOR_LIST, r):
                    indikator_sub = list(comb)
                    kolom_fitur = get_kolom_fitur(indikator_sub, tahun, tahun)

                    # --- Ambil subset data & bersihkan ---
                    X = df_scaled[kolom_fitur].copy()
                    X = X.replace([np.inf, -np.inf], np.nan).dropna()
                    X = X.astype("float32")

                    # --- Skip kalau data kosong ---
                    if X.shape[0] == 0:
                        st.warning(f"⚠️ Data kosong untuk tahun {tahun}, fitur {indikator_sub}. Dilewati.")
                        continue

                    start = time.time()
                    try:
                        sb = SpectralBridges(
                            n_clusters=k,
                            n_nodes=60,
                            p=1,
                            random_state=rs
                        )
                        sb.fit(X)
                        labels = sb.predict(X)
                        dur = time.time() - start

                        sil = silhouette_score(X, labels)
                        dbi = davies_bouldin_score(X, labels)

                        semua_hasil.append({
                            "Metode": "Spectral Bridges",
                            "Jumlah Cluster": k,
                            "Tahun": tahun,
                            "Fitur": ", ".join(indikator_sub),
                            "Silhouette": round(sil, 4),
                            "DBI": round(dbi, 4),
                            "Waktu Komputasi (detik)": round(dur, 4)
                        })
                    except Exception as e:
                        st.warning(f"❌ Gagal cluster: tahun {tahun}, fitur {indikator_sub} → {e}")
                        continue

                    task_done += 1
                    progress.progress(min(task_done / total_tasks, 1.0))

        df_out = pd.DataFrame(semua_hasil)
        fname = f"hasil_sb_cluster{k}_semua_tahun.xlsx"
        fpath = os.path.join(MODEL_DIR, fname)
        df_out.to_excel(fpath, index=False)
        st.write(f"✅ File tersimpan: {fpath}")

    st.success("🎉 Selesai! Semua file Spectral Bridges (2–7 cluster) berhasil dibuat.")
# === LATIH SPECTRAL BRIDGES MASSAL ===
def train_all_sb_excel():
    """
    Latih Spectral Bridges untuk cluster 2–7 dan semua tahun,
    simpan 1 file Excel per cluster (total 6 file).
    Tiap file berisi 6 tahun × 15 kombinasi fitur = 90 baris.
    """
    st.info("🚀 Memulai pelatihan otomatis Spectral Bridges (2–7 cluster, semua tahun, 15 kombinasi fitur)...")

    df_scaled = gpd.read_file(os.path.join(DATA_DIR, "data_scaled.geojson"))
    
    total_tasks = len(CLUSTER_RANGE) * len(TAHUN_LIST) * 15
    task_done = 0
    progress = st.progress(0)

    with open(HASIL_SB_PATH, "rb") as f:
        hasil_sb = pickle.load(f)
    if isinstance(hasil_sb, pd.DataFrame):
        hasil_sb = hasil_sb.to_dict(orient="records")

    for k in CLUSTER_RANGE:
        rs = _ambil_random_state(hasil_sb, k)
        semua_hasil = []

        for tahun in TAHUN_LIST:
            for r in range(1, len(INDIKATOR_LIST) + 1):
                for comb in itertools.combinations(INDIKATOR_LIST, r):
                    indikator_sub = list(comb)
                    kolom_fitur = get_kolom_fitur(indikator_sub, tahun, tahun)
                    X = df_scaled[kolom_fitur]

                    # === Try multiple random_state fallback ===
                    fallback_states = [rs, 76, 75, 42]
                    success = False

                    for rs_try in fallback_states:
                        try:
                            start = time.time()
                            sb = SpectralBridges(
                                n_clusters=k,
                                n_nodes=60,
                                p=1,
                                random_state=rs_try
                            )
                            sb.fit(X)
                            labels = sb.predict(X)
                            dur = time.time() - start

                            sil = silhouette_score(X, labels)
                            dbi = davies_bouldin_score(X, labels)

                            semua_hasil.append({
                                "Metode": "Spectral Bridges",
                                "Jumlah Cluster": k,
                                "Tahun": tahun,
                                "Fitur": ", ".join(indikator_sub),
                                "Silhouette": round(sil, 4),
                                "DBI": round(dbi, 4),
                                "Waktu Komputasi (detik)": round(dur, 4),
                                "Random State": rs_try
                            })

                            st.info(f"✅ Tahun {tahun}, fitur {indikator_sub}, cluster={k} sukses dengan rs={rs_try}")
                            success = True
                            break
                        except Exception as e:
                            st.warning(f"⚠️ Gagal cluster: tahun {tahun}, fitur {indikator_sub}, cluster={k}, rs={rs_try} → {e}")
                            continue

                    # Jika semua percobaan gagal
                    if not success:
                        st.error(f"❌ Semua percobaan gagal: tahun {tahun}, fitur {indikator_sub}, cluster={k}")
                        continue

                    task_done += 1
                    progress.progress(min(task_done / total_tasks, 1.0))

        # === Simpan hasil ke Excel ===
        df_out = pd.DataFrame(semua_hasil)
        fname = f"hasil_sb_cluster{k}_semua_tahun.xlsx"
        fpath = os.path.join(MODEL_DIR, fname)
        df_out.to_excel(fpath, index=False)
        st.write(f"✅ File tersimpan: {fpath}")

    st.success("🎉 Selesai! Semua file Spectral Bridges (2–7 cluster) dibuat.")

