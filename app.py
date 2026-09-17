import streamlit as st
import os
from agent_core import ReportAgent, send_telegram_notification
from memory_manager import load_memory, tambah_pembelajaran

st.set_page_config(page_title="AI Report Agent", page_icon="🤖", layout="wide")

st.title("🤖 AI Report Generator & Auto-Learner Agent")

with st.sidebar:
    st.header("⚙️ Konfigurasi")
    gemini_key = st.text_input("Gemini API Key", type="password")
    uploaded_cred = st.file_uploader("Upload credentials.json", type=["json"])
    telegram_token = st.text_input("Bot Token (Opsional)", type="password")
    telegram_chat_id = st.text_input("Chat ID (Opsional)")

if uploaded_cred:
    with open("credentials.json", "wb") as f:
        f.write(uploaded_cred.getbuffer())

tab1, tab2 = st.tabs(["🚀 Jalankan Agent", "🧠 Pusat Pembelajaran AI"])

with tab1:
    folder_id = st.text_input("Masukkan ID Folder Google Drive:")
    report_title = st.text_input("Judul Laporan", value="Laporan Tugas Sirkuit Arduino")

    if st.button("Jalankan Agent Otomatis", type="primary"):
        if not gemini_key or not os.path.exists("credentials.json") or not folder_id:
            st.error("Lengkapi API Key, Credentials, dan ID Folder!")
        else:
            try:
                st.info("🔄 Agent sedang bekerja...")
                agent = ReportAgent(gemini_key, "credentials.json")
                files = agent.get_files_from_folder(folder_id)
                image_files = [f for f in files if 'image' in f['mimeType']]

                list_analisis = []
                for img_file in image_files:
                    request = agent.drive_service.files().get_media(fileId=img_file['id'])
                    img_bytes = request.execute()
                    prompt = f"Analisis sirkuit {img_file['name']}."
                    jawaban = agent.analyze_image_with_gemini(img_bytes, img_file['mimeType'], prompt)

                    list_analisis.append({
                        'soal': f"Analisis {img_file['name']}",
                        'jawaban': jawaban,
                        'image_id': img_file['id']
                    })

                doc_url = agent.create_doc_with_inline_images(report_title, list_analisis, folder_id)
                st.success("✅ Laporan Berhasil Dibuat!")
                st.markdown(f"### 📄 [Buka Google Docs]({doc_url})")

                if telegram_token and telegram_chat_id:
                    send_telegram_notification(telegram_token, telegram_chat_id, f"✅ Laporan Selesai: {doc_url}")

            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.header("🧠 Ajari AI")
    current_mem = load_memory()
    st.write("Aturan saat ini:", current_mem["gaya_penulisan"])
    koreksi = st.text_area("Tambah aturan/koreksi baru:")
    if st.button("Simpan Ingatan"):
        if koreksi.strip():
            tambah_pembelajaran(koreksi)
            st.success("Tersimpan!")
