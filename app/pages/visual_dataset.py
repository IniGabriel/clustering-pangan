import streamlit as st
import numpy as np
import os, sys, psycopg2
import pandas as pd
from session import init_session
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import matplotlib.patches as mpatches
import itertools
import time
from utils.db import get_conn
# === 0️⃣ Inisialisasi sesi ===
init_session()
logged_in = st.session_state.get("logged_in", False)
email = st.session_state.get("email", "")
selected_dataset = st.session_state.get("selected_dataset", None)



# === 2️⃣ Load CSS ===
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === 3️⃣ Konfigurasi Halaman ===
st.set_page_config(page_title="📊 Visualisasi Dataset", layout="wide")

st.markdown("<h2 style='text-align:center;'>📊 Visualisasi Dataset Terlatih</h2>", unsafe_allow_html=True)
st.write("---")

if not logged_in:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()

conn = get_conn()
cur = conn.cursor()

# === 4️⃣ Ambil user_id berdasarkan email ===
cur.execute("SELECT user_id FROM Pengguna WHERE email = %s;", (email,))
row = cur.fetchone()
if not row:
    st.error("❌ User tidak ditemukan.")
    st.stop()
user_id = row[0]

# === 5️⃣ Ambil dataset_id berdasarkan path ===
if not selected_dataset:
    st.warning("⚠️ Tidak ada dataset yang sedang dipilih.")
    st.stop()

cur.execute("""
    SELECT dataset_id 
    FROM Dataset 
    WHERE user_id = %s AND path_dataset = %s
    LIMIT 1;
""", (user_id, selected_dataset))
dataset_row = cur.fetchone()

if not dataset_row:
    st.error("❌ Dataset tidak ditemukan di database.")
    st.stop()

dataset_id = dataset_row[0]
if st.button("⬅️ Kembali ke Halaman Sebelumnya"):
    st.switch_page("pages/dataset.py")

# === 6️⃣ Pilihan algoritma dan cluster ===
algoritma = st.selectbox("Pilih algoritma model:", ["K-Means", "AHC", "Spectral Bridges"])

jumlah_cluster = st.slider("Pilih jumlah cluster:", 2, 7, 2, 1)
if st.button("📊 Tampilkan Visualisasi"):
    status_placeholder = st.empty()    
    with st.spinner("⏳ Sedang memproses data..."):    
        if algoritma == "K-Means":
            table_name = "model_kmeans"
        elif algoritma == "AHC":
            table_name = "model_ahc"
        elif algoritma == "Spectral Bridges":
            table_name = "model_sb"
        cur.execute(f"""
            SELECT nama_model, path_model, silhouette, dbi
            FROM {table_name}
            WHERE dataset_id = %s 
              AND user_id = %s
              AND jumlah_cluster = %s;
        """, (dataset_id, user_id, jumlah_cluster))
        models = cur.fetchall()

        if not models:
            st.error(f"❌ Tidak ditemukan model {algoritma} dengan {jumlah_cluster} cluster.")
            st.stop()

        df_model = df_long = df_wide = None
        silhouette_val = dbi_val = None

        for nama_model, path_model, silhouette, dbi in models:
            if not os.path.exists(path_model):
                st.warning(f"⚠️ File {nama_model} tidak ditemukan di {path_model}")
                continue

            if silhouette_val is None and silhouette is not None:
                silhouette_val = silhouette
            if dbi_val is None and dbi is not None:
                dbi_val = dbi

            if "df_model" in nama_model:
                df_model = pd.read_csv(path_model)
            elif "df_long" in nama_model:
                df_long = pd.read_csv(path_model)
            elif "df_wide" in nama_model:
                df_wide = pd.read_csv(path_model)

        if df_model is None or df_long is None or df_wide is None:
            st.error("❌ Salah satu file model tidak ditemukan (df_model/df_long/df_wide).")
            st.stop()
        st.write("---")
        st.subheader(f"📄 Visualisasi {algoritma} (Cluster = {jumlah_cluster})")

        # === 8️⃣ Visualisasi Korelasi (pakai df_model) ===
        col1, col2 = st.columns(2)
        with col1:
            kolom_tahunan = [c for c in df_model.columns if "_202" in c]
            if not kolom_tahunan:
                # === Kasus tanpa kolom tahun ===
                df_pivot = df_model.copy()

                # Hilangkan kolom non-fitur sebelum korelasi
                drop_cols = [c for c in ["Cluster", "Silhouette", "Label", "kab_kota"] if c in df_pivot.columns]
                df_pivot = df_pivot.drop(columns=drop_cols, errors="ignore")

                # Ambil hanya kolom numerik
                df_pivot = df_pivot.select_dtypes(include=["number"])

            else:
                # === Kasus dengan kolom tahun ===
                df_temp = df_model.copy()

                # Pastikan hanya kab_kota dan kolom tahun yang dipakai
                df_melt = df_temp.melt(
                    id_vars=["kab_kota"],
                    value_vars=kolom_tahunan,
                    var_name="Fitur_Tahun",
                    value_name="Nilai"
                )

                # Pisahkan fitur & tahun
                df_melt[["Fitur", "Tahun"]] = df_melt["Fitur_Tahun"].str.split("_", expand=True)

                # Hitung rata-rata nilai per fitur
                df_avg = df_melt.groupby(["kab_kota", "Fitur"])["Nilai"].mean().reset_index()

                # Pivot jadi wide (fitur sebagai kolom)
                df_pivot = df_avg.pivot(index="kab_kota", columns="Fitur", values="Nilai").reset_index()

                # Hapus kolom non-fitur kalau ada
                drop_cols = [c for c in ["Cluster", "Silhouette", "Label"] if c in df_pivot.columns]
                df_pivot = df_pivot.drop(columns=drop_cols, errors="ignore")

                # Ambil hanya kolom numerik
                df_pivot = df_pivot.select_dtypes(include=["number"])

            # === Hitung korelasi hanya antar fitur ===
            hasil_korelasi = df_pivot.corr().round(2)

            fig, ax = plt.subplots(figsize=(6, 5))
            sns.heatmap(hasil_korelasi, annot=True, cmap="RdYlGn", fmt=".2f", vmin=-1, vmax=1, square=True, ax=ax)
            ax.set_title("Korelasi Antar Indikator", fontsize=11, pad=10)
            st.pyplot(fig)

        # === 9️⃣ Boxplot (pakai df_long) ===
        with col2:
            data_peta = None
            if "kab_kota" in df_model.columns:
                try:
                    df_geom = gpd.read_file("../Dataset/template/template.geojson")
                    df_geom["kab_kota"] = df_geom["kab_kota"].str.lower().str.strip()
                    df_model["kab_kota"] = df_model["kab_kota"].str.lower().str.strip()

                    data_peta = df_geom.merge(df_model, on="kab_kota", how="left")
                    data_peta = gpd.GeoDataFrame(data_peta, geometry="geometry", crs="EPSG:4326")
                    data_peta = data_peta.drop_duplicates(subset="geometry", keep="first")

                    unique_clusters = sorted(data_peta["Cluster"].dropna().unique())    
                except Exception as e:
                    st.warning(f"⚠️ Gagal memuat peta: {e}")
                    data_peta = None


            # === Tetap siapkan color_map dari cluster df_model ===
            if "Cluster" in df_model.columns:
                unique_clusters = sorted(df_model["Cluster"].dropna().unique())
            else:
                unique_clusters = []

            base_colors = [ "#67E3CA","#F1C40F", "#E67E22", "#FF351F", "#18A3FF", "#812DA1","#FF52F1"]
            color_map = {c: base_colors[i % len(base_colors)] for i, c in enumerate(unique_clusters)}
            # ===================================================================================
            plt.figure(figsize=(6, 5))
            sns.set_style("whitegrid")
            sns.boxplot(data=df_long, x="Fitur", y="Nilai", hue="Cluster" ,palette=color_map)
            plt.title("Distribusi Nilai Tiap Fitur per Cluster")
            plt.xlabel("Fitur Ketahanan Pangan")
            plt.ylabel("Nilai Indikator")
            plt.legend(title="Cluster", loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=True)
            plt.tight_layout()
            st.pyplot(plt)

        # === 🔟 Folium Map (pakai df_model) ===
        if data_peta is not None:
            center_lat, center_lon = -2.5, 118.0
            m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles="CartoDB Voyager")

            style_function = lambda feature: {
                "fillColor": color_map.get(feature["properties"].get("Cluster"), "gray"),
                "color": "black",
                "weight": 0.4,
                "fillOpacity": 0.9,
            }

            tooltip = GeoJsonTooltip(
                fields=["kab_kota", "Cluster", "Silhouette"],
                aliases=["Kabupaten/Kota:", "Cluster:", "Silhouette:"],
                localize=True,
                sticky=False,
                labels=True
            )

            folium.GeoJson(
                data_peta.to_json(),
                style_function=style_function,
                tooltip=tooltip,
                name="Hasil Clustering"
            ).add_to(m)

            legend_html = """
            <div style="
                position: fixed;
                bottom: 30px; left: 30px; width: 240px;
                background-color: white; border:2px solid gray;
                z-index:9999; font-size:14px; border-radius:8px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                padding: 10px;">
            <b>Legenda Cluster</b><br>
            """
            for label, color in color_map.items():
                legend_html += f'<i style="background:{color};width:15px;height:15px;float:left;margin-right:8px;"></i>Cluster {label}<br>'
            legend_html += "</div>"

            m.get_root().html.add_child(folium.Element(legend_html))
            st_folium(m, width=1200, height=700, returned_objects=[])

        # === 11️⃣ Evaluasi Model ===
        if silhouette_val is not None and dbi_val is not None:
            st.markdown("### 📊 Evaluasi Model")
            colm1, colm2 = st.columns(2)
            with colm1:
                st.metric("Silhouette Coefficient", f"{silhouette_val:.4f}")
            with colm2:
                st.metric("Davies–Bouldin Index", f"{dbi_val:.4f}")
        
        col4,col5= st.columns(2)
        with col4:
            
            # === Pastikan kolom tersedia ===
            if "Cluster" not in df_wide.columns or "Silhouette" not in df_wide.columns:
                st.warning("⚠️ Kolom 'Label' atau 'Silhouette' tidak ditemukan di df_wide.")
            else:
                df_sil = df_wide.copy()

                # 1️⃣ Pastikan kolom numerik
                df_sil["Silhouette"] = pd.to_numeric(df_sil["Silhouette"], errors="coerce").fillna(0.0)

                # 2️⃣ Filter label valid (hindari Undefined)
                labels_terpakai = [lbl for lbl in df_sil["Cluster"].unique() if lbl != "Undefined"]

                # 3️⃣ Buat warna cluster (ambil dari color_map jika sudah ada)
                if "color_map" not in locals():
                    base_colors = ["#2ECC71", "#E67E22", "#E74C3C", "#3498DB", "#9B59B6",
                                "#F1C40F", "#1ABC9C", "#34495E", "#7F8C8D", "#16A085"]
                    color_map = {lbl: base_colors[i % len(base_colors)] for i, lbl in enumerate(labels_terpakai)}

                # 4️⃣ Buat plot silhouette
                fig, ax = plt.subplots(figsize=(8, 6))
                y_lower = 10

                for i, cluster in enumerate(labels_terpakai):
                    vals = (
                        df_sil.loc[df_sil["Cluster"] == cluster, "Silhouette"]
                        .astype(float)
                        .sort_values()
                        .to_numpy()
                    )

                    if vals.size == 0:
                        continue

                    y_upper = y_lower + vals.size
                    y = np.arange(y_lower, y_upper)

                    ax.fill_betweenx(
                        y,
                        0.0,
                        vals,
                        facecolor=color_map[cluster],
                        edgecolor=color_map[cluster],
                        alpha=0.85
                    )
                    y_lower = y_upper + 10  # jarak antar cluster

                # 5️⃣ Garis rata-rata silhouette keseluruhan
                silhouette_avg = float(df_sil["Silhouette"].mean())
                ax.axvline(x=silhouette_avg, color="darkred", linestyle="--", linewidth=1.5)

                # 6️⃣ Legend
                legend_patches = [mpatches.Patch(color=color_map[lbl], label=lbl) for lbl in labels_terpakai]
                ax.legend(
                    handles=legend_patches,
                    title="Cluster",
                    ncol=3,
                    bbox_to_anchor=(0.5, -0.15),
                    loc='upper center',
                    frameon=True,
                    fontsize=10,
                    title_fontsize=11,
                )

                # 7️⃣ Format tampilan
                ax.set_title("Distribusi Nilai Silhouette per Cluster", fontsize=13)
                ax.set_xlabel("Nilai Silhouette", fontsize=11)
                ax.set_ylabel("")
                ax.set_yticks([])
                ax.set_xlim([-0.1, 1])
                ax.grid(axis='x', linestyle='--', alpha=0.5)

                plt.tight_layout()
                st.pyplot(plt)        
        with col5:
            # Pastikan kolom Cluster tersedia
            if "Cluster" not in df_wide.columns:
                st.warning("⚠️ Kolom 'Cluster' tidak ditemukan di df_wide.")
            else:
                plt.figure(figsize=(6, 4))

                # --- Hitung jumlah anggota per cluster ---
                cluster_counts = df_wide["Cluster"].value_counts().sort_index()
                df_counts = cluster_counts.reset_index()
                df_counts.columns = ["Cluster", "Jumlah"]

                # --- Buat color_map jika belum ada ---
                if "color_map" not in locals():
                    base_colors = ["#2ECC71", "#E67E22", "#E74C3C", "#3498DB", "#9B59B6",
                                "#F1C40F", "#1ABC9C", "#34495E", "#7F8C8D", "#16A085"]
                    unique_clusters = sorted(df_wide["Cluster"].unique())
                    color_map = {c: base_colors[i % len(base_colors)] for i, c in enumerate(unique_clusters)}

                # --- Bar Plot ---
                sns.barplot(
                    data=df_counts,
                    x="Cluster",
                    y="Jumlah",
                    hue="Cluster",
                    palette=color_map,
                    dodge=False,
                    legend=True
                )

                # --- Tambahkan angka di atas setiap batang ---
                for i, val in enumerate(cluster_counts.values):
                    plt.text(
                        i,
                        val + (max(cluster_counts.values) * 0.02),  # 2% di atas bar
                        f'{val}',
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold'
                    )

                # --- Atur ruang dan tampilan ---
                plt.ylim(0, max(cluster_counts.values) * 1.15)
                plt.title("Jumlah Anggota Tiap Cluster", fontsize=13, pad=10)
                plt.ylabel("Jumlah Kabupaten/Kota", fontsize=11)
                plt.xticks(rotation=0)
                sns.despine()
                plt.grid(axis='y', linestyle='--', alpha=0.4)

                # --- Legend dinamis ---
                legend_cols = 2 if len(df_counts) <= 5 else 3
                legend = plt.legend(
                    title_fontsize=10,
                    fontsize=10,
                    frameon=True,
                    ncol=legend_cols,
                    loc='upper center',
                    bbox_to_anchor=(0.5, -0.15)
                )
                legend.get_title().set_fontweight('bold')

                plt.tight_layout()
                st.pyplot(plt)
        # kolom_wajib = {"kab_kota", "Fitur", "Nilai", "Cluster"}
        # if not kolom_wajib.issubset(df_long.columns):
        #     st.error(f"❌ df_long tidak memiliki kolom lengkap: {kolom_wajib - set(df_long.columns)}")
        #     st.stop()

 # === Pastikan fitur tersedia ===
        fitur_tersedia = sorted(df_long["Fitur"].dropna().unique().tolist())

        if len(fitur_tersedia) < 2:
            pass
        else:
            if data_peta is not None:
            # --- Pivot dataframe (satu kabupaten = satu baris) ---
                df_scatter = df_long.pivot_table(
                    index=["kab_kota", "Cluster"],
                    columns="Fitur",
                    values="Nilai",
                    aggfunc="mean"
                ).reset_index()

            else:
                df_scatter = df_long.pivot_table(
                    index=["Label", "Cluster"],
                    columns="Fitur",
                    values="Nilai",
                    aggfunc="mean"
                ).reset_index()

            df_scatter = df_scatter.dropna(how="all", subset=fitur_tersedia)                

            if len(fitur_tersedia) == 2:
                x, y = fitur_tersedia[:2]

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    plt.figure(figsize=(7, 6))
                    sns.scatterplot(
                        data=df_scatter,
                        x=x,
                        y=y,
                        hue="Cluster" ,
                        palette=color_map,
                        s=55,
                        edgecolor="white",
                        alpha=0.85
                    )
                    plt.title(f"Sebaran {x} vs {y}", fontsize=12, pad=10)
                    plt.xlabel(x)
                    plt.ylabel(y)
                    plt.legend(title="Cluster", loc="best", fontsize=9)
                    plt.tight_layout()
                    st.pyplot(plt)
                    plt.close()

            # === KONDISI 2: jika fitur_tersedia > 2 atau 'Semua fitur_tersedia' ===
            elif len(fitur_tersedia) > 2 or fitur_tersedia == ["Semua Indikator"]:
                kombinasi = list(itertools.combinations(fitur_tersedia, 2))
                n_plots = min(len(kombinasi), 6)  # batasi 6 kombinasi biar rapi

                plt.figure(figsize=(15, 10))
                for i, (x, y) in enumerate(kombinasi[:n_plots], 1):
                    plt.subplot(2, 3, i)
                    sns.scatterplot(
                        data=df_scatter,
                        x=x,
                        y=y,
                        hue="Label" if "Label" in df_scatter.columns else "Cluster",
                        palette=color_map,
                        s=45,
                        edgecolor="white",
                        alpha=0.85
                    )
                    plt.title(f"{x} vs {y}", fontsize=11)
                    plt.xlabel(x)
                    plt.ylabel(y)
                    plt.legend(title="Cluster", loc="best", fontsize=8)

                plt.tight_layout()
                st.pyplot(plt)
                plt.close()

    status_placeholder.success("✅ Data berhasil diproses!")
