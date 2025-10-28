import streamlit as st
import os, sys

# ===================== IMPORT SESSION =====================
# Pastikan save_session.py ada di folder utama
sys.path.append(os.path.dirname(__file__))
from session import init_session

# Inisialisasi session
init_session()

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="Clustering Website",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== SESSION CHECK =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

logged_in = st.session_state.logged_in
username = st.session_state.username

# ===================== LOAD CSS =====================
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)




if logged_in:
    cols = st.columns(7)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)
    with cols[1]:
        st.page_link("pages/upload.py", label="Upload Dataset")
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

else:
    cols = st.columns(5)
    with cols[0]:
        st.markdown("<b>Clustering Website</b>", unsafe_allow_html=True)     
    with cols[1]:
        st.page_link("pages/visualization.py", label="Visualization")
    with cols[2]:
        st.page_link("pages/summary.py", label="Summary")
    with cols[3]:
        st.page_link("pages/about.py", label="About")
    with cols[4]:
        st.page_link("pages/login.py", label="Login")


# ===================== BODY CONTENT =====================
# st.markdown(
#     '''
# <div class="content">
#         <h4>K-Means</h4>
#         <div class="section-box">
#         <b>Cara Kerja:</b>
#         <ol>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#         </ol>
#     </div>

# <h4>Agglomerative Hierarchical Clustering</h4>
#     <div class="section-box">
#         <b>Cara Kerja:</b>
#         <ol>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#         </ol>
#     </div>

# <h4>Spectral Bridges</h4>
#     <div class="section-box">
#         <b>Cara Kerja:</b>
#         <ol>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#             <li>Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.</li>
#         </ol>
#     </div>    

# <h4>Dataset Indeks Ketahanan Pangan</h4>
#     <div class="section-box">
#         Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam.
#     </div>

# <h4>Skor Pola Pangan Harapan</h4>
#     <div class="section-box">
#         Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam.
#     </div>

# <h4>Rasio Angka Kecukupan Protien</h4>
#     <div class="section-box">
#         Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam.
#     </div>

# <h4>Rasio Angka Kecukupan Energi</h4>
#     <div class="section-box">
#         Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam.
#     </div>
# </div>
# ''', unsafe_allow_html=True)

st.markdown(
    '''
<h4>Dataset Indeks Ketahanan Pangan</h4>
    <div class="section-box">
        Indeks Ketahanan Pangan (IKP) merupakan sebuah sistem penilaian yang dirancang untuk mengukur tingkat ketahananpangan suatu wilayah.
        Nilai IKP berada dalam rentang 0 hingga 100, di mana nilai 0 merepresentasikan wilayah dengan tingkat kerentanan pangan yang sangat rendah, sedangkan nilai 100
        menunjukan wilayah dengan ketahanan pangan terbaik. 
    </div>

<h4>Skor Pola Pangan Harapan</h4>
    <div class="section-box">
        Skor Pola Pangan Harapan (PPH) merupakan sebuah ukuran untuk menilai keragaman dan komposisi konsumsi pangan penduduk. Penyusunan skor PPH dilakukan
        sebagai acuan bagi pemerintah, baik pemerintah daerah provinsi dan pemerintah daerah kabupaten/kota dalam melakukan penilaian terkait komposisi pangan.
        Skor PPH memiliki nilai maksimal 100, di mana semakin tinggi nilainya, maka konsumsi pangan masyarakat semakin beragam dan bergizi seimbang.
    </div>

<h4>Rasio Angka Kecukupan Protien</h4>
    <div class="section-box">
        Rasio Angka Kecukupan Energi (RAKP, pada dataset ini AKP), merupakan ukuran standar kecukupan konsumsi protein penduduk. Nilai rasio yang mendekati 100% menunjukkan bahwa konsumsi protein masyarakat sesuai kebutuhan,
        sedangkan nilai di bawah rentang 100% menunjukkan bahwa konsumsi protein masih kurang memenuhi standar.
    </div>

<h4>Rasio Angka Kecukupan Energi</h4>
    <div class="section-box">
        Rasio Angka Kecukupan Energi (RAKE, pada dataset ini AKE), merupakan ukuran presentase pemenuhan kebutuhan energi penduduk di satu wilayah dengan cara membandingkan konsumsi energi aktual terhadap konsumsi 
        energi ideal yang direkomendasikan oleh Widyakarya Nasional Pangan dan Gizi (WNPG). Nilai pada indikator ini semakin mendekati 100% maka semakin baik tingkat pemenuhan kebuuthan energi. Namun, nilai
        di bawah 100% menunjukkan bahwa rata-rata konsumsi energi penduduk belum memenuhi standar AKG.
    </div>
</div>
''', unsafe_allow_html=True)

