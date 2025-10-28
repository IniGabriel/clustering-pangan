import streamlit as st
from session import init_session
import os
from session import init_session
st.set_page_config(
    page_title="About",
    layout="wide",
    initial_sidebar_state="expanded"
)
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
init_session()
logged_in = st.session_state.get("logged_in", False)
username= st.session_state.get("username",False)
if logged_in:
    cols = st.columns(8)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)
    with cols[1]:
        st.page_link("home.py", label="Home")
    with cols[2]:
        st.page_link("pages/upload.py", label="Upload Dataset")
    with cols[4]:
        st.page_link("pages/visualization.py", label="Visualization")
    with cols[5]:
        st.page_link("pages/summary.py", label="Summary")
    with cols[6]:
        st.write(f"Halo, {username} 👋")
    with cols[7]:
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
        st.page_link("pages/summary.py", label="Summary")
    with cols[4]:
        st.page_link("pages/login.py", label="Login")

# === 4️⃣ Konten Utama ===
st.markdown("<h2 style='text-align:center;'>ℹ️ Tentang Website Ini</h2>", unsafe_allow_html=True)
st.write("---")

st.markdown("""
### **Deskripsi Umum**
Website ini dirancang sebagai platform interaktif untuk melakukan **analisis klasterisasi ketahanan pangan** di seluruh wilayah Indonesia.  
Melalui pendekatan _machine learning_, pengguna dapat:
- Mengunggah dataset sesuai dengan template yang disediakan.
- Melatih model dengan berbagai algoritma _clustering_ (K-Means, AHC, Spectral Bridges).  
- Melihat hasil visualisasi berupa peta, boxplot, korelasi fitur, dan evaluasi model.  

Tujuannya adalah membantu akademisi dan masyarakat umum dalam memahami pola ketahanan pangan di tingkat **kabupaten/kota** secara visual.

> ℹ️ **Catatan:**  
> Pengguna yang ingin **mengunggah dataset pribadi** wajib melakukan **login terlebih dahulu**.  

---

### **Fitur Utama**
- **Upload Dataset:** Pengguna dapat mengunggah file `.csv` atau '.xlsx dengan struktur indikator yang sesuai template.
- **Training Model:** Menjalankan proses klasterisasi dengan pilihan jumlah cluster serta algoritma yang diinginkan.
- **Visualisasi Data:**  
  - Heatmap korelasi antar indikator.  
  - Boxplot distribusi fitur per cluster.  
  - Scatterplot interaktif untuk analisis hubungan fitur.  
  - Peta interaktif berbasis Folium untuk menampilkan hasil klasterisasi spasial.  
-  **Evaluasi Model:** Sistem menampilkan metrik _Silhouette Coefficient_ dan _Davies–Bouldin Index_ secara otomatis.

---

### **Teknologi yang Digunakan**
- **Python & Streamlit** → untuk antarmuka interaktif.  
- **PostgreSQL** → untuk penyimpanan data pengguna, dataset, dan model hasil klasterisasi.  
- **Folium & GeoPandas** → untuk visualisasi peta interaktif berbasis data spasial.  
- **Seaborn & Matplotlib** → untuk visualisasi korelasi, boxplot, dan distribusi data.  
- **Scikit-learn** → untuk implementasi algoritma klasterisasi.  

---

### **Tujuan Akhir**
Website ini diharapkan dapat:
- Menjadi alat bantu analisis untuk memahami data ketahanan pangan di Indonesia
- Meningkatkan pemahaman terhadap persebaran dan perbandingan ketahanan pangan antar daerah.  
---

""")

# st.success("✨ Terima kasih telah menggunakan aplikasi ini!")

# ### 👨‍💻 **Dikembangkan oleh**
# **Gabriel Nathanael Irawan (535220142)**  
# Program Studi Informatika — Universitas Advent Indonesia  
# Sebagai bagian dari **Tugas Akhir (Skripsi)** berjudul:  
# > “Analisis Klaster Ketahanan Pangan Kabupaten/Kota di Indonesia Menggunakan K-Means, Agglomerative Hierarchical Clustering, dan Spectral Bridges”

# ---

# ### 🧭 **Tujuan Akhir**
# Website ini diharapkan dapat:
# - Menjadi alat bantu analisis berbasis data spasial bagi lembaga ketahanan pangan nasional.  
# - Meningkatkan pemahaman terhadap persebaran dan perbandingan ketahanan pangan antar daerah.  
# - Menjadi sarana pembelajaran praktis dalam penerapan *machine learning* untuk data geospasial.

# ---

# ### 💬 **Hubungi Kami**
# Jika ada pertanyaan, kritik, atau saran, silakan kirim email ke:  
# 📩 **streamlitgab@gmail.com**

# ---

# """)

# st.success("✨ Terima kasih telah menggunakan aplikasi ini!")