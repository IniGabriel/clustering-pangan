# Clustering Pangan (Skripsi) — Streamlit App
## Deskripsi Aplikasi

Aplikasi ini merupakan **website berbasis Streamlit** yang dikembangkan untuk mendukung kebutuhan skripsi dengan fokus pada **clustering indikator ketahanan pangan kabupaten/kota di Indonesia**.  
Aplikasi ini digunakan untuk mengelompokkan wilayah berdasarkan karakteristik ketahanan pangan menggunakan beberapa indikator gizi dan pangan yang relevan.

## Indikator Ketahanan Pangan

Indikator yang digunakan dalam perancangan ini untuk menggambarkan kondisi ketahanan pangan suatu wilayah adalah sebagai berikut:

### 1. Indeks Ketahanan Pangan (IKP)
Indeks Ketahanan Pangan (IKP) merupakan sistem penilaian yang dirancang untuk mengukur tingkat ketahanan pangan suatu wilayah secara komprehensif. Nilai IKP berada pada rentang **0 hingga 100**, di mana nilai **0** merepresentasikan wilayah dengan tingkat kerentanan pangan yang sangat tinggi, sedangkan nilai **100** menunjukkan wilayah dengan kondisi ketahanan pangan terbaik.

### 2. Skor Pola Pangan Harapan (PPH)
Skor Pola Pangan Harapan (PPH) merupakan indikator yang digunakan untuk menilai **keragaman dan komposisi konsumsi pangan penduduk**. Penyusunan skor PPH digunakan sebagai acuan bagi pemerintah, baik pemerintah provinsi maupun kabupaten/kota, dalam mengevaluasi kesesuaian pola konsumsi pangan masyarakat. Skor PPH memiliki nilai maksimal **100**, di mana semakin tinggi nilainya, maka konsumsi pangan masyarakat semakin beragam dan mendekati pola gizi seimbang.

### 3. Rasio Angka Kecukupan Energi (AKE)
Rasio Angka Kecukupan Energi (AKE) menggambarkan tingkat pemenuhan kebutuhan energi penduduk di suatu wilayah dengan membandingkan konsumsi energi aktual terhadap konsumsi energi ideal yang direkomendasikan oleh **Widyakarya Nasional Pangan dan Gizi (WNPG)**. Nilai rasio yang mendekati **100%** menunjukkan bahwa kebutuhan energi penduduk telah terpenuhi, sedangkan nilai di bawah **100%** mengindikasikan bahwa rata-rata konsumsi energi masih belum memenuhi standar Angka Kecukupan Gizi (AKG).

### 4. Rasio Angka Kecukupan Protein (AKP)
Rasio Angka Kecukupan Protein (AKP) merupakan indikator yang menunjukkan tingkat kecukupan konsumsi protein penduduk. Nilai rasio AKP yang mendekati **100%** menunjukkan bahwa konsumsi protein masyarakat telah sesuai dengan kebutuhan, sedangkan nilai di bawah **100%** mengindikasikan bahwa konsumsi protein masih berada di bawah standar yang dianjurkan.


User dapat **upload dataset**, menjalankan **clustering** dengan beberapa algoritma, lalu melihat **visualisasi** (peta/plot) dan **ringkasan evaluasi** (Silhouette & Davies–Bouldin Index).

---

## Fitur Utama

- **Autentikasi pengguna**
  - Registrasi + verifikasi email (OTP via SMTP)
  - Login/Logout
  - Admin page (email admin dikunci di kode: `admin@email.com`)
- **Proses clustering**
  - Pilihan algoritma: **K-Means**, **Agglomerative Hierarchical Clustering (AHC/Ward)**, **Spectral Bridges**
  - Pilihan jumlah cluster (slider, default 2; range 2–7)
  - Hitung metrik evaluasi: **Silhouette Score** & **Davies–Bouldin Index (DBI)**
- **Visualisasi**
  - Peta (Folium/GeoJSON) + tooltip
  - Grafik/plot pendukung (Matplotlib/Seaborn/Plotly)
- **Summary**
  - Ringkasan hasil (format Excel di `app/summary/*` dan/atau hasil per model)

---

## Struktur Folder

```
clustering-pangan-main/
├─ app/                          # Source utama Streamlit
│  ├─ home.py                    # Landing / navbar / routing
│  ├─ fungsi.py                  # Helper clustering & evaluasi
│  ├─ session.py                 # Inisialisasi session state
│  ├─ utils/
│  │  ├─ db.py                   # Koneksi PostgreSQL via st.secrets
│  │  ├─ auth_utils.py           # hash/verify password + OTP generator
│  │  └─ email_utils.py          # kirim OTP via SMTP SSL
│  ├─ pages/                     # Halaman Streamlit (multipage)
│  │  ├─ login.py, register.py, verify_email.py, forgot_password.py, logout.py
│  │  ├─ upload.py               # Upload dataset
│  │  ├─ dataset.py              # List dataset & housekeeping
│  │  ├─ train.py                # Proses/training clustering
│  │  ├─ visualization.py        # Peta/plot hasil
│  │  ├─ summary.py, about.py, admin.py, template.py, visual_dataset.py
│  └─ .streamlit/
│     └─ python-version          # 3.12.0
│
├─ Dataset/                      # Contoh geojson/model bawaan (opsional)
│  └─ model/                     # contoh pkl/geojson/scaler/summary
│
├─ Hasil Eksperimen/             # Artefak hasil eksperimen (pickle)
├─ requirements.txt
```
---

## Cara Instalasi 
### 1. Clone Github
Lakukan import github dengan melakukan hal berikut di terminal:
```bash
git clone https://github.com/IniGabriel/clustering-pangan.git
```
### 2. Install Dependencies
Melakukan instalasi library dengan melakukan hal berikut di terminal:
```bash
pip install -r requirements.txt
```

### 3. Siapkan Tabel PostgreSQL
Di kode, tabel `Pengguna` dibuat otomatis saat verifikasi email (jika belum ada).  
Namun tabel **dataset** dan **model** perlu kamu siapkan di database (karena dipakai di `upload.py`, `dataset.py`, `train.py`).


Berikut contoh query untuk membuat tabel tabel yang diperlukan:
```sql
-- 1) Tabel pengguna
CREATE TABLE IF NOT EXISTS pengguna (
  user_id   SERIAL PRIMARY KEY,
  username  VARCHAR(50) NOT NULL,
  email     VARCHAR(50) NOT NULL,
  password  VARCHAR(255) NOT NULL
);

-- 2) Tabel dataset
CREATE TABLE IF NOT EXISTS dataset (
  dataset_id     SERIAL PRIMARY KEY,
  nama_dataset   VARCHAR(100) NOT NULL,
  path_dataset   vARCHAR(200) NOT NULL,
  sudah_dilatih BOOLEAN DEFAULT FALSE,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES pengguna (user_id) ON DELETE CASCADE
);

-- 3) Tabel model (hasil proses metode clustering)
CREATE TABLE IF NOT EXISTS model (
  model_id         SERIAL PRIMARY KEY,
  nama_model       VARCHAR(100) NOT NULL,
  path_model       VARCHAR(250) NOT NULL,
  jumlah_cluster   INTEGER NOT NULL,
  silhouette       NUMERIC(6,4),
  dbi              NUMERIC(6,4),
  waktu_komputasi  NUMERIC(10,4),
  user_id INTEGER NOT NULL,
  dataset_id INTEGER NOT NULL,
  algoritma VARCHAR(10),

  FOREIGN KEY (user_id) REFERENCES pengguna(user_id) ON DELETE CASCADE,
  FOREIGN KEY (dataset_id) REFERENCES dataset(dataset_id) ON DELETE CASCADE
);
```

### 4. Konfigurasi PostgreSQL dan SMTP
Aplikasi ini menggunakan Streamlit Secrets untuk menyimpan konfigurasi database dan email OTP. 
Buat file berikut:
```bash
app/.streamlit/secrets.toml
```
Kemudian lakukan konfigurasi PostgreSQL dan SMTP pada file `secrets.toml` sebagai berikut:
```
# ===== PostgreSQL =====
db_host = "YOUR_HOST"
db_dbname = "YOUR_DBNAME"
db_user = "YOUR_USER"
db_password = "YOUR_PASSWORD"
db_port = "5432"

# ===== SMTP (untuk OTP email) =====
smtp = "smtp.gmail.com"
port = 465
email = "YOUR_SENDER_EMAIL"
password = "YOUR_APP_PASSWORD"
```
> Catatan: Jika menggunakan Gmail, pastikan menggunakan App Password, bukan password email utama.

### 5. Menjalankan Aplikasi
Ketikan perintah berikut pada terminal:
```bash
cd app 
python -m streamlit run home.py
```
---

## Manual 
Untuk penggunaan, silakan baca [Buku Manual (PDF)](./BukuManual.pdf).
