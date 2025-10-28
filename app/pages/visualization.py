import os, sys, pickle
import streamlit as st
from streamlit_folium import st_folium
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np 
import itertools
import time
import folium
from folium.features import GeoJson, GeoJsonTooltip
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples, davies_bouldin_score
from sklearn.cluster import AgglomerativeClustering
# Spectral Bridges
from spectralbridges import SpectralBridges
import plotly.figure_factory as ff
from scipy.cluster.hierarchy import linkage

from fungsi import *

# --- Page Config ---
st.set_page_config(
    page_title="Visualisasi Klasterisasi Ketahanan Pangan",
    layout="wide",
    initial_sidebar_state="expanded"
)
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")

with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
from session import init_session
init_session()
logged_in = st.session_state.get("logged_in", False)
username= st.session_state.get("username",False)


if logged_in:
    cols = st.columns(7)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)
    with cols[1]:
        st.page_link("home.py", label="Home")
    with cols[2]:
        st.page_link("pages/upload.py", label="Upload Dataset")
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

else:
    cols = st.columns(5)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)     
    with cols[1]:
        st.page_link("home.py", label="Home")
    with cols[2]:
        st.page_link("pages/summary.py", label="Summary")
    with cols[3]:
        st.page_link("pages/about.py", label="About")
    with cols[4]:
        st.page_link("pages/login.py", label="Login")

# === Input Control ===
algoritma = st.selectbox("Pilih Algoritma:", ["K-Means", "Agglomerative (AHC)", "Spectral Bridges"])
tahun_opsi = ["2021", "2022", "2023", "2021–2022", "2022–2023", "Semua Tahun"]
tahun = st.selectbox("Pilih Tahun:", tahun_opsi, index=5)
indikator_opsi = ["IKP", "PPH", "AKE", "AKP", "Semua Indikator"]
indikator = st.multiselect("Pilih Indikator:", indikator_opsi, default=["Semua Indikator"])
jumlah_cluster = st.slider("Pilih Jumlah Cluster:", 2, 7, 2, 1)
tampilkan = st.button("🟩 Tampilkan Visualisasi")

invalid = False
if len(indikator) == 0:
    st.warning("⚠️ Minimal harus memilih satu indikator.")
    invalid = True
if "Semua Indikator" in indikator and len(indikator) > 1:
    st.warning("⚠️ Jika memilih 'Semua Indikator', jangan pilih indikator lain.")
    invalid = True

# st.markdown("### ⚙️ Pelatihan Massal Semua Algoritma")

# col1, col2, col3 = st.columns(3)
# with col1:
#     if st.button("🚀 Jalankan Semua K-Means"):
#         from fungsi import train_all_kmeans_excel
#         train_all_kmeans_excel()

# with col2:
#     if st.button("🧬 Jalankan Semua AHC"):
#         from fungsi import train_all_ahc_excel
#         train_all_ahc_excel()

# with col3:
#     if st.button("🌉 Jalankan Semua Spectral Bridges"):
#         from fungsi import train_all_sb_excel
#         train_all_sb_excel()


# === LOGIC ===
if tampilkan and not invalid:
    status_placeholder = st.empty()
    with st.spinner("⏳ Sedang memproses data..."):
            kolom_fitur = get_kolom_fitur(indikator, tahun, tahun)  
            color_map = get_color(jumlah_cluster)
            # hasil_kmeans_path = f"../Dataset/model/summary/hasil_kmeans_all_all.pkl"
            # hasil_ahc_path = f"../Dataset/model/summary/hasil_ahc_all_all.pkl"
            # hasil_sb_path = f"../Dataset/model/summary/hasil_sb_all_all.pkl"
            # scaler_path = f"../Dataset/model/scaler.pkl"   
            hasil_kmeans_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_kmeans_all_all.pkl")
            hasil_ahc_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_ahc_all_all.pkl")
            hasil_sb_path = os.path.join(current_dir,"..","..","Dataset","model","summary","hasil_sb_all_all.pkl")
            scaler_path = os.path.join(current_dir,"..","..","Dataset","model","scaler.pkl")  

            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)

            df_scaled_path = "..\Dataset\pre\data_scaled.geojson"
            df_scaled = gpd.read_file(df_scaled_path)
            df_scaled_null_path = "..\Dataset\pre\data_scaled_null.geojson"
            df_scaled_null = gpd.read_file(df_scaled_null_path)
            df_inverse= inverse(df_scaled,scaler)
            data_pivot_awal = data_pivot_awal(df_inverse, kolom_fitur)

            if algoritma == "K-Means":
                kmeans_result, data_kmeans_final = train_kmeans(
                    data_scaled=df_scaled,
                    data_scaled_null=df_scaled_null,
                    kolom_fitur=kolom_fitur,
                    hasil_kmeans_path=hasil_kmeans_path,
                    jumlah_cluster=jumlah_cluster,
                    data_inverse=df_inverse,
                    tahun=tahun
                )
            
            elif algoritma =="Agglomerative (AHC)":
                kmeans_result, data_kmeans_final = train_ahc(
                    data_scaled=df_scaled,
                    data_scaled_null=df_scaled_null,
                    kolom_fitur=kolom_fitur,
                    hasil_ahc_path=hasil_ahc_path,
                    jumlah_cluster=jumlah_cluster,
                    data_inverse=df_inverse,
                    tahun=tahun
                )

            elif algoritma =="Spectral Bridges":
                kmeans_result,data_kmeans_final = train_sb(
                    data_scaled=df_scaled,
                    data_scaled_null = df_scaled_null,
                    kolom_fitur=kolom_fitur,
                    hasil_sb_path = hasil_sb_path,
                    jumlah_cluster=jumlah_cluster,
                    data_inverse = df_inverse,
                    tahun=tahun
                )
            data_boxplot = buat_data_boxplot(
                data_kmeans_final=data_kmeans_final,
                kolom_fitur=kolom_fitur,
            )
            data_boxplot_final = data_boxplot.copy()

            col1, col2 = st.columns(2)
            with col1:
                # --- 1️⃣ Pivot hasil data untuk korelasi ---
                df_korelasi = data_pivot_awal.pivot_table(
                    index=['kab_kota', 'Tahun'],
                    columns='Fitur',
                    values='Nilai',
                    aggfunc='mean'
                ).reset_index()

                # --- 2️⃣ Filter tahun sesuai input user ---
                # Ambil daftar tahun yang aktif (2021, 2022, dst)
                if tahun == "Semua Tahun":
                    tahun_dipakai = ['2021', '2022', '2023']
                elif tahun == "2021–2022":
                    tahun_dipakai = ['2021', '2022']
                elif tahun == "2022–2023":
                    tahun_dipakai = ['2022', '2023']
                else:
                    tahun_dipakai = [tahun]

                df_korelasi = df_korelasi[df_korelasi["Tahun"].astype(str).isin(tahun_dipakai)] 


                # --- 3️⃣ Tentukan kolom fitur sesuai indikator user ---
                indikator_semua = ['PPH', 'IKP', 'AKE', 'AKP']
                if "Semua Indikator" in indikator or len(indikator) == 0:
                    fitur_dipakai = indikator_semua
                else:
                    fitur_dipakai = indikator
                # Pastikan hanya kolom yang memang ada di df
                fitur_tersedia = [f for f in fitur_dipakai if f in df_korelasi.columns]
                
                if not fitur_tersedia:
                    st.warning("⚠️ Tidak ada kolom indikator yang cocok untuk data ini.")
                else:
                    # --- 4️⃣ Normalisasi per tahun (Z-score) ---
                    df_korelasi[fitur_tersedia] = df_korelasi.groupby("Tahun")[fitur_tersedia].transform(
                        lambda x: (x - x.mean()) / x.std(ddof=0)
                    )

                    # --- 5️⃣ Hitung matriks korelasi ---
                    korelasi_kmeans = df_korelasi[fitur_tersedia].corr().round(2)

                    # --- 6️⃣ Plot heatmap ---
                    plt.figure(figsize=(5, 4))
                    sns.heatmap(
                        korelasi_kmeans,
                        annot=True,
                        cmap="RdYlGn",
                        fmt=".2f",
                        vmin=-1,
                        vmax=1,
                        square=True
                    )
                    plt.title(f"Korelasi Antar Indikator")
                    plt.tight_layout()
                    st.pyplot(plt)


        # ================== (2) BOX PLOT ===================================
            indikator_list = [col.split("_")[0] for col in kolom_fitur]
            tahun_list = [col.split("_")[1] for col in kolom_fitur]

            box_df = data_boxplot_final.copy()
            box_df = box_df[box_df["Cluster"] != "Undefined"]
            box_df = box_df[
                (box_df["Tahun"].astype(str).isin(tahun_list)) &
                (box_df["Fitur"].isin(indikator_list))
            ]
            rata2_per_cluster = box_df.groupby("Cluster").mean(numeric_only=True)

            box_df = box_df[box_df["Cluster"] != "Undefined"]
            box_df = box_df.dropna(subset=["Cluster"])
            box_df["Cluster"] = box_df["Cluster"].astype(int)         

            data_peta = data_kmeans_final.copy()
    
            with col2:
                plt.figure(figsize=(6, 5))
                sns.set_style("whitegrid")
                sns.boxplot(
                    data=box_df,
                    x="Fitur",
                    y="Nilai",
                    hue='Cluster',
                    palette=color_map,
                    linewidth=0.8
                )
                plt.title("Distribusi Nilai Tiap Fitur per Cluster")
                plt.xlabel("Fitur Ketahanan Pangan")
                plt.ylabel("Nilai Indikator")
                if jumlah_cluster <= 4:
                    col = 2
                elif jumlah_cluster < 8:
                    col =4
                plt.legend(
                    title="Cluster",
                    loc='upper center',
                    bbox_to_anchor=(0.5, -0.15),
                    ncol=col,
                    frameon=True
                )

                plt.tight_layout()
                st.pyplot(plt)

        #================ (3) PETA (HTML FOLIUM) =====================================
            # df_scatter=data_boxplot_final.copy()
            df_scatter=box_df.copy()

            df_scatter = df_scatter.pivot_table(
                index=['kab_kota', 'Tahun', 'Cluster'],
                columns='Fitur',
                values='Nilai',
                aggfunc='mean'
            ).reset_index()

            kolom_cluster = "Cluster"
            kolom_silhouette = "Silhouette"
            kolom_kabupaten = "kab_kota"
            data_peta = data_peta.merge(
                df_scatter[["kab_kota"] + fitur_dipakai],
                on="kab_kota",
                how="left"
            )

            data_peta[kolom_silhouette] = data_peta[kolom_silhouette].fillna("Undefined")
            data_peta[kolom_kabupaten] = data_peta[kolom_kabupaten].fillna(data_peta["name"])
            data_peta[fitur_dipakai] = data_peta[fitur_dipakai].fillna("Undefined")

            center_lat = data_peta.geometry.centroid.y.mean()
            center_lon = data_peta.geometry.centroid.x.mean()
            
            duplikat_geom = data_peta[data_peta.duplicated(subset="geometry", keep=False)]

            print(f"Jumlah data sebelum: {len(data_peta)}")
            data_peta = data_peta.drop_duplicates(subset="geometry", keep="first")
            print(f"Jumlah data sesudah hapus duplikat: {len(data_peta)}")
            if not duplikat_geom.empty:
                print("⚠️ Ada geometry yang duplikat!")
                print(f"Jumlah baris duplikat: {len(duplikat_geom)}")
                print(duplikat_geom[["kab_kota", "geometry"]])
            else:
                print("✅ Tidak ada duplikat geometry.")

            # excel_path = "Plisbiwsa.xlsx"
            # data_peta.drop(columns='geometry').to_excel(excel_path, index=False)
            # print(f"✅ File Excel berhasil disimpan ke: {excel_path}")

            # # === 2️⃣ Simpan GeoDataFrame hanya kab_kota dan geometry ===
            # geo_simplified = data_peta[["kab_kota", "geometry"]]
            # geojson_path = "Plisbiwsa.geojson"
            # geo_simplified.to_file(geojson_path, driver="GeoJSON")
            # print(f"🌍 File GeoJSON berhasil disimpan ke: {geojson_path}")
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=5,
                tiles="CartoDB Voyager"
            )

            # === 8. Tambahkan layer GeoJSON ===
            style_function = lambda feature: {
                "fillColor": color_map.get(feature["properties"][kolom_cluster], "gray"),
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 1,
            }
            tooltip = GeoJsonTooltip(
                fields=["kab_kota", kolom_cluster, kolom_silhouette]+fitur_dipakai,
                aliases=["Kabupaten/Kota:", "Cluster:", "Silhouette:"]+ [f"{f}:" for f in fitur_dipakai],
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

            # === 9. Legenda (pakai label teks, bukan angka) ===
            legend_html = """
            <div style="
                position: fixed;
                bottom: 30px; left: 30px; width: 240px;
                background-color: white; border:2px solid gray;
                z-index:9999; font-size:14px; border-radius:8px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                padding: 10px;">
            <b>Cluster</b><br>
            """
            for label, color in color_map.items():
                legend_html += f'<i style="background:{color};width:15px;height:15px;float:left;margin-right:8px;"></i>{label}<br>'
            legend_html += "</div>"

            m.get_root().html.add_child(folium.Element(legend_html))
            st_folium(m, width=1200, height=700, returned_objects=[])
            
            if kmeans_result is not None:
                st.markdown("### 📊 Evaluasi Model K-Means")
                colm1, colm2 = st.columns(2)
                with colm1:
                    st.metric("Silhouette Coefficient", f"{kmeans_result['silhouette_avg']:.4f}")
                with colm2:
                    st.metric("Davies–Bouldin Index", f"{kmeans_result['dbi']:.4f}")

#=================================== (4) SILHOUETTE PLOT & BAR PLOT ===================================
            col4,col5=st.columns(2)
            with col4:
            # Pastikan numeric & bersihkan nilai invalid
                df_sil = data_peta.copy()

                # 1) Jadikan kolom Silhouette numerik
                df_sil[kolom_silhouette] = pd.to_numeric(df_sil[kolom_silhouette], errors="coerce")

                # 2) Isi NaN dengan 0.0 (atau kalau mau, bisa dropna)
                df_sil[kolom_silhouette] = df_sil[kolom_silhouette].fillna(0)
                df_sil = df_sil.dropna(subset=["Cluster"])
                df_sil["Cluster"] = df_sil["Cluster"].astype(int)


                # 3) (Opsional) kalau ada label yang tidak ada warnanya, filter dulu
                labels_terpakai = [lbl for lbl in df_sil["Cluster"].unique() if lbl in color_map and lbl != "Undefined"]
                # 4) Plot
                fig, ax = plt.subplots(figsize=(8, 6))
                y_lower = 10

                for i, cluster in enumerate(labels_terpakai):
                    # ambil & urutkan nilai silhouette cluster tsb sebagai float
                    vals = (
                        df_sil.loc[df_sil["Cluster"] == cluster, kolom_silhouette]
                        .astype(float)
                        .sort_values()
                        .to_numpy()
                    )

                    # kalau kosong, lanjutkan
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
                    y_lower = y_upper + 10  # spasi antar cluster

                # Garis rata-rata silhouette keseluruhan
                silhouette_avg = float(df_sil[kolom_silhouette].mean())
                ax.axvline(x=silhouette_avg, color="darkred", linestyle="--", linewidth=1.5)

                # Legend
                legend_patches = [mpatches.Patch(color=color_map[lbl], label=lbl) for lbl in labels_terpakai]
                ax.legend(handles=legend_patches, 
                          title="Cluster",
                          ncol=col,
                          bbox_to_anchor=(0.5,-0.15),
                          loc='upper center', 
                          frameon=True, 
                          fontsize=11, 
                          title_fontsize=11,
                          )
                # Tampilan
                ax.set_title("Distribusi Nilai Silhouette per Cluster", fontsize=13)
                ax.set_xlabel("Nilai Silhouette", fontsize=11)
                ax.set_ylabel("")
                ax.set_yticks([])
                ax.set_xlim([-0.1, 1])
                ax.grid(axis='x', linestyle='--', alpha=0.5)

                plt.tight_layout()
                st.pyplot(plt)
# =================== BAR PLOT  =================================================
            with col5:
                plt.figure(figsize=(6, 4))
                cluster_counts = df_sil.loc[df_sil["Cluster"] != "Undefined", "Cluster"].value_counts().sort_index()
                df_counts = cluster_counts.reset_index()
                df_counts.columns = ["Cluster", "Jumlah"]
                sns.barplot(
                    data=df_counts,
                    x="Cluster",
                    y="Jumlah",
                    hue=df_counts['Cluster'].astype(int),
                    palette=color_map,
                    dodge=False,                 # biar warnanya tetap satu per label
                    legend=True                  # aktifkan legend
                )

                # --- Tambahkan angka di atas tiap batang ---
                for i, val in enumerate(cluster_counts.values):
                    plt.text(
                        i,
                        val + (max(cluster_counts.values) * 0.02),  # 2% di atas bar
                        f'{val}',
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold'
                    )

                # --- Tambahkan ruang atas biar tidak mepet ---
                plt.ylim(0, max(cluster_counts.values) * 1.15)  # +15% ruang

                # --- Label & Judul ---
                plt.title("Jumlah Anggota Tiap Cluster", fontsize=13, pad=10)
                plt.xlabel("Cluster", fontsize=11)
                legend = plt.legend(
                    title="Cluster",          # judul legend
                    title_fontsize=10,         # ukuran font judul legend
                    fontsize=10,               # ukuran font item legend
                    frameon=True,
                    ncol=col,
                    loc='upper center',
                    bbox_to_anchor=(0.5, -0.15)
                )
                legend.get_title().set_fontweight('bold')  # opsional: judul legend tebal                
                plt.ylabel("Jumlah Kabupaten/Kota", fontsize=11)
                plt.xticks([])                 
                # --- Tampilan lebih bersih ---
                sns.despine()
                plt.grid(axis='y', linestyle='--', alpha=0.4)
                

                # --- Tampilkan ---
                plt.tight_layout()      
                st.pyplot(plt)      

#-------------- TOP 10 anggota cluster 
            df_top = df_scatter.copy()
            df_top = (
                df_scatter
                .groupby(["kab_kota", "Cluster"], as_index=False)[fitur_dipakai]
                .mean()
            )


            # --- Loop tiap cluster
            for c in sorted(df_top["Cluster"].unique()):
                with st.expander(f"Cluster {int(c)}"):
                    total_fitur = len(fitur_dipakai)

                    # --- Tentukan layout kolom otomatis
                    if total_fitur == 1:
                        # buat 3 kolom tapi isi di kolom ke-2 biar rapi di tengah
                        fitur_groups = [fitur_dipakai]
                        layout_mode = "single"
                    elif total_fitur == 2:
                        fitur_groups = [fitur_dipakai]
                        layout_mode = "double"
                    elif total_fitur == 3:
                        # dua di atas, satu di tengah bawah
                        fitur_groups = [fitur_dipakai[:2], [fitur_dipakai[2]]]
                        layout_mode = "triple"
                    elif total_fitur == 4:
                        fitur_groups = [fitur_dipakai[:2], fitur_dipakai[2:]]
                        layout_mode = "multi"
                    else:
                        fitur_groups = [fitur_dipakai[i:i+3] for i in range(0, total_fitur, 3)]
                        layout_mode = "multi"

                    # --- Loop tiap grup fitur (per baris)
                    for group in fitur_groups:
                        if layout_mode == "single":
                            cols = st.columns([1, 2, 1])
                            target_col = cols[1]
                        elif layout_mode == "triple" and len(group) == 1:
                            cols = st.columns([1, 2, 1])
                            target_col = cols[1]
                        else:
                            cols = st.columns(len(group))
                            target_col = None

                        for idx, fitur in enumerate(group):
                            container = target_col if target_col else cols[idx]

                            with container:
                                st.markdown(f"##### {fitur}")

                                data_cluster = df_top[df_top["Cluster"] == c]
                                n_top = min(10, len(data_cluster))
                                if n_top == 0:
                                    st.warning(f"Tidak ada data untuk Cluster {c} – {fitur}")
                                    continue

                                topN = (
                                    data_cluster.nlargest(n_top, fitur)[["kab_kota", fitur, "Cluster"]]
                                    .sort_values(by=fitur, ascending=False)
                                )

                                plt.figure(figsize=(6.5, 8))
                                ax = sns.barplot(
                                    data=topN,
                                    x="kab_kota",
                                    y=fitur,
                                    order=topN["kab_kota"],
                                    color=color_map.get(int(c), "#888"),
                                    errorbar=None,
                                )

                                sns.despine(top=True, right=True)
                                ax.set_xlim(-0.5, len(topN) - 0.5)
                                ymax = topN[fitur].max()
                                for i, val in enumerate(topN[fitur]):
                                    ax.text(
                                        i, val + (ymax * 0.04),
                                        f"{val:.2f}",
                                        ha="center", va="bottom",
                                        fontsize=8, fontweight="bold", clip_on=False
                                    )
                                plt.ylim(0, ymax * 1.18)
                                plt.xlabel("")
                                plt.ylabel(fitur)
                                plt.title(f"{n_top} kab/kota dengan nilai {fitur} tertinggi", fontsize=10, pad=5)
                                plt.xticks(rotation=40, ha="right")
                                plt.subplots_adjust(bottom=0.28, top=0.9, left=0.1, right=0.98)
                                st.pyplot(plt)
                                plt.close()






# === (5) SCATTER PLOT PAIR PLOT ===================================
            if len(indikator) == 2:
                # --- Layout 3 kolom, tampil di tengah
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    x, y = fitur_tersedia[:2]

                    plt.figure(figsize=(7, 6))
                    sns.scatterplot(
                        data=df_scatter,
                        x=x,
                        y=y,
                        hue=df_scatter["Cluster"].astype(int),
                        palette=color_map,
                        s=55,
                        edgecolor="white",
                        alpha=0.85
                    )

                    plt.title(f'Sebaran {x} vs {y}', fontsize=12, pad=10)
                    plt.xlabel(x)
                    plt.ylabel(y)
                    plt.legend(title='Cluster', loc='best', fontsize=9)
                    plt.tight_layout()
                    st.pyplot(plt)
                    plt.close()

            elif len(indikator) > 2 or indikator == ["Semua Indikator"]:
                # --- Kombinasi semua pasangan fitur
                kombinasi = list(itertools.combinations(fitur_tersedia, 2))

                plt.figure(figsize=(15, 10))
                for i, (x, y) in enumerate(kombinasi, 1):
                    plt.subplot(2, 3, i)
                    sns.scatterplot(
                        data=df_scatter,
                        x=x,
                        y=y,
                        hue=df_scatter["Cluster"].astype(int),
                        palette=color_map,
                        s=45,
                        edgecolor="white",
                        alpha=0.8
                    )
                    plt.title(f'{x} & {y}', fontsize=11)
                    plt.xlabel(x)
                    plt.ylabel(y)
                    plt.legend(title='Cluster', loc='best', fontsize=8)

                plt.tight_layout()
                st.pyplot(plt)
                plt.close()
#             if algoritma == "Agglomerative (AHC)":

# # --- Pastikan index sinkron ---
#                 datanum = df_scaled.copy()
#                 datanum = datanum.drop_duplicates(keep='first', inplace= True)

#                 # datanum = df_scaled.select_dtypes(include=[np.number])
#                 # --- 2️⃣ Hitung linkage untuk dendrogram ---
#                 linked = linkage(datanum, method="ward")

#                 # --- 3️⃣ Buat dendrogram interaktif dengan label ---
#                 fig = ff.create_dendrogram(
#                     linked,
#                     orientation="bottom",
#                     labels=data_peta["alt_name"],         
#                     color_threshold=0
#                 )

#                 # --- 4️⃣ Atur tampilan dan interaksi ---
#                 fig.update_layout(
#                     width=1200,
#                     height=700,
#                     showlegend=False,
#                     template="plotly_white",
#                     title={
#                         "text": f"🧬 Dendrogram AHC (Cluster = {jumlah_cluster})",
#                         "x": 0.5,
#                         "xanchor": "center",
#                         "yanchor": "top"
#                     },
#                     xaxis=dict(
#                         tickangle=45,
#                         tickfont=dict(size=9),
#                     )
#                 )

#                     # --- 5️⃣ (Opsional) Tambahkan garis horizontal sebagai batas cluster ---
#                 import plotly.graph_objects as go
#                 from scipy.cluster.hierarchy import fcluster

#                 # Tentukan threshold berdasarkan jumlah cluster
#                 cluster_labels = fcluster(linked, jumlah_cluster, criterion="maxclust")
#                 # Ambil tinggi pemotongan (optional untuk tampilan)
#                 threshold = sorted(linked[:, 2], reverse=True)[jumlah_cluster - 1]
#                 fig.add_shape(
#                     type="line",
#                     x0=-0.5,
#                     x1=len()-0.5,
#                     y0=threshold,
#                     y1=threshold,
#                     line=dict(color="red", width=2, dash="dash"),
#                 )

#                 # --- 6️⃣ Tampilkan ke Streamlit ---
#                 st.plotly_chart(fig, use_container_width=True)
    
    status_placeholder.success("✅ Data berhasil diproses!")

# --- Tombol Kembali ---
if st.button("⬅️Kembali ke home"):
    st.switch_page("home.py")