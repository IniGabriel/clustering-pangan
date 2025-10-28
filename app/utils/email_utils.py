import smtplib, ssl, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# === Konfigurasi SMTP ===
SMTP_SERVER = st.secrets['smtp']
SMTP_PORT = st.secrets["port"]
SENDER_EMAIL = st.secrets["email"]
SENDER_PASSWORD = st.secrets["password"]

def send_verification_email(receiver_email, otp):
    print(f"📤 Mengirim email ke: {receiver_email} ...")

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = "Kode Verifikasi Akun Kamu"
    body = f"Halo! 👋\n\nKode verifikasi kamu adalah: {otp}\n\nJangan berikan kode ini ke siapa pun."
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    time.sleep(1.5)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.set_debuglevel(1)  # tampilkan log detail di terminal
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("✅ Email OTP berhasil dikirim!")
    except Exception as e:
        print(f"❌ Error SMTP: {e}")
        raise e
