import streamlit as st
import psycopg2
import os, sys
import time
from utils.db import get_conn
from session import init_session

# === 1️⃣ Inisialisasi sesi ===
init_session()
email = st.session_state.get("email", False)

# === 2️⃣ Validasi hanya admin ===
if email != "admin@email.com":
    st.warning("⚠️ Hanya admin yang dapat masuk ke halaman ini.")
    time.sleep(1.5)
    st.switch_page("home.py")
    st.stop()

# === 3️⃣ Load CSS ===
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === 4️⃣ Konfigurasi halaman ===
st.set_page_config(page_title="👥 Kelola Pengguna", layout="wide")
st.markdown("<h2 style='text-align:center;'>👥 Kelola Pengguna</h2>", unsafe_allow_html=True)
st.write("---")

# === 5️⃣ Koneksi database ===
conn = get_conn()
cur = conn.cursor()

try:
    cur.execute("SELECT user_id, username, email FROM Pengguna ORDER BY user_id ASC;")
    pengguna = cur.fetchall()

    if not pengguna:
        st.info("Belum ada pengguna yang terdaftar.")
        st.stop()

    st.write("### 📋 Daftar Pengguna")
    st.caption("Klik 🗑️ untuk menghapus akun pengguna beserta semua file dataset dan model-nya dari folder path dan database (cascade).")

    col1, col2, col3, col4 = st.columns([1, 3, 4, 2])
    with col1: st.markdown("**ID**")
    with col2: st.markdown("**Username**")
    with col3: st.markdown("**Email**")
    with col4: st.markdown("**Aksi**")
    st.divider()

    tabel_model = ["model_kmeans", "model_ahc", "model_sb"]

    for uid, uname, uemail in pengguna:
        col1, col2, col3, col4 = st.columns([1, 3, 4, 2])
        with col1: st.write(uid)
        with col2: st.write(uname)
        with col3: st.write(uemail)

        with col4:
            if uemail == "admin@email.com":
                st.button("👑 Admin", disabled=True, key=f"admin_{uid}")
                continue

            hapus_btn = st.button("🗑️ Hapus Pengguna", key=f"hapus_{uid}")
            if hapus_btn:
                st.session_state["confirm_delete_user"] = uid
                st.rerun()

        # === Konfirmasi hapus ===
        if st.session_state.get("confirm_delete_user") == uid:
            st.warning(f"Apakah Anda yakin ingin menghapus pengguna **{uname}** beserta seluruh dataset dan model-nya?")
            c1, c2 = st.columns(2)

            with c1:
                if st.button("✅ Ya, Hapus Pengguna Ini", key=f"confirm_{uid}"):
                    try:
                        total_dataset_files = 0
                        total_model_files = 0
                        missing_dataset = 0
                        missing_model = 0

                        # === 🔹 Ambil semua path dataset user ===
                        cur.execute("SELECT dataset_id, path_dataset FROM Dataset WHERE user_id = %s;", (uid,))
                        datasets = cur.fetchall()

                        for dataset_id, path_dataset in datasets:
                            # --- Hapus file dataset ---
                            if path_dataset and os.path.exists(path_dataset):
                                try:
                                    os.remove(path_dataset)
                                    total_dataset_files += 1
                                except Exception as e:
                                    st.warning(f"Gagal hapus dataset: {path_dataset} ({e})")
                            else:
                                missing_dataset += 1

                            # --- Hapus file model terkait ---
                            for tabel in tabel_model:
                                cur.execute(f"SELECT path_model FROM {tabel} WHERE dataset_id = %s;", (dataset_id,))
                                model_files = cur.fetchall()
                                for (path_model,) in model_files:
                                    if path_model and os.path.exists(path_model):
                                        try:
                                            os.remove(path_model)
                                            total_model_files += 1
                                        except Exception as e:
                                            st.warning(f"Gagal hapus model: {path_model} ({e})")
                                    else:
                                        missing_model += 1

                        # === 🔹 Hapus user (otomatis cascade hapus dataset & model di DB)
                        cur.execute("DELETE FROM Pengguna WHERE user_id = %s;", (uid,))
                        conn.commit()

                        st.success(
                            f"✅ Pengguna '{uname}' berhasil dihapus dari database.\n\n"
                            f"🗑️ {total_dataset_files} file dataset & {total_model_files} file model dihapus dari folder path.\n"
                            f"⚠️ {missing_dataset} dataset & {missing_model} model tidak ditemukan (mungkin sudah dihapus sebelumnya)."
                        )

                        time.sleep(2)
                        st.session_state.pop("confirm_delete_user", None)
                        st.rerun()

                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Gagal menghapus pengguna {uname}: {e}")

            with c2:
                if st.button("❌ Batal", key=f"cancel_{uid}"):
                    st.session_state.pop("confirm_delete_user", None)
                    st.rerun()

except psycopg2.Error as e:
    st.error(f"Kesalahan saat mengambil data pengguna: {e}")

finally:
    cur.close()
    conn.close()

# === CSS Tombol ===
st.markdown("""
<style>
div[data-testid="stButton"][key^="hapus_"] > button {
    background-color: #e63946 !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
}
div[data-testid="stButton"][key^="confirm_"] > button {
    background-color: #d62828 !important;
    color: white !important;
    border-radius: 8px;
}
div[data-testid="stButton"][key^="cancel_"] > button {
    background-color: #adb5bd !important;
    color: black !important;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)
