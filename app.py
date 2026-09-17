import streamlit as st
import os
import json
from agent_core import ReportAgent, send_telegram_notification
from memory_manager import load_memory, tambah_pembelajaran

st.set_page_config(page_title="AI Report Agent", page_icon="🤖", layout="wide")

st.title("🤖 AI Report Generator & Auto-Learner Agent")

with st.sidebar:
    st.header("⚙️ Konfigurasi")
    gemini_key = st.text_input("Gemini API Key", type="password")
    
    # Mengganti File Uploader dengan Text Area
    json_text = st.text_area("Paste Isi File credentials.json di Sini:", height=150)
    
    telegram_token = st.text_input("Bot Token (Opsional)", type="password")
    telegram_chat_id = st.text_input("Chat ID (Opsional)")

# Menyimpan isi JSON ke file temporary secara otomatis
if json_text.strip():
    try:
        cred_dict = json.loads(json_text)
        with open("credentials.json", "w", encoding="utf-8") as f:
            json.dump(cred_dict, f)
    except Exception as e:
        st.sidebar.error("Format JSON tidak valid!")

tab1, tab2 = st.tabs(["🚀 Jalankan Agent", "🧠 Pusat Pembelajaran AI"])

with tab1:
    folder_id = st.text_input("Masukkan ID Folder Google Drive:")
    report_title = st.text_input("Judul Laporan", value="Laporan Tugas Sirkuit Arduino")
    
    if st.button("Jalankan Agent Otomatis", type="primary"):
        if not gemini_key or not os.path.exists("credentials.json") or not folder_id:
            st.error("Lengkapi API Key, Paste credentials.json, dan masukkan ID Folder!")
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
