import os
import requests
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from memory_manager import build_prompt_with_memory

class ReportAgent:
    def __init__(self, gemini_api_key, credentials_path):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        SCOPES = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents'
        ]
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)

    def get_files_from_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.drive_service.files().list(
            q=query, fields="files(id, name, mimeType)"
        ).execute()
        return results.get('files', [])

    def make_file_public(self, file_id):
        permission = {'type': 'anyone', 'role': 'reader'}
        self.drive_service.permissions().create(
            fileId=file_id, body=permission
        ).execute()

    def analyze_image_with_gemini(self, image_bytes, image_mime, prompt_soal):
        final_prompt = build_prompt_with_memory(
            f"Analisis gambar sirkuit ini dan jawab pertanyaan berikut:\n{prompt_soal}"
        )
        contents = [
            {'mime_type': image_mime, 'data': image_bytes},
            final_prompt
        ]
        response = self.model.generate_content(contents)
        return response.text

    def create_doc_with_inline_images(self, title, list_analisis, parent_folder_id=None):
        doc_body = {'title': title}
        doc = self.docs_service.documents().create(body=doc_body).execute()
        doc_id = doc.get('documentId')

        if parent_folder_id:
            file = self.drive_service.files().get(fileId=doc_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=parent_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

        requests_batch = []
        current_idx = 1

        header = f"{title}\n\n"
        requests_batch.append({'insertText': {'location': {'index': current_idx}, 'text': header}})
        current_idx += len(header)

        for item in list_analisis:
            section_text = f"📌 Pertanyaan: {item['soal']}\n\n🔍 Hasil Analisis:\n{item['jawaban']}\n\n"
            requests_batch.append({'insertText': {'location': {'index': current_idx}, 'text': section_text}})
            current_idx += len(section_text)

            if item.get('image_id'):
                self.make_file_public(item['image_id'])
                img_url = f"https://drive.google.com/thumbnail?id={item['image_id']}&sz=w1000"

                requests_batch.append({
                    'insertInlineImage': {
                        'location': {'index': current_idx},
                        'uri': img_url,
                        'objectSize': {
                            'height': {'magnitude': 220, 'unit': 'PT'},
                            'width': {'magnitude': 380, 'unit': 'PT'}
                        }
                    }
                })
                current_idx += 1

            divider = "\n\n" + ("=" * 40) + "\n\n"
            requests_batch.append({'insertText': {'location': {'index': current_idx}, 'text': divider}})
            current_idx += len(divider)

        self.docs_service.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests_batch}
        ).execute()

        self.make_file_public(doc_id)
        return f"https://docs.google.com/document/d/{doc_id}/edit"

def send_telegram_notification(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Gagal kirim notif: {e}")
