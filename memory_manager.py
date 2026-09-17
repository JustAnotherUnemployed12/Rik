import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        default_mem = {
            "system_instruction": "Kamu adalah AI Assistant ahli analisis sirkuit dan tugas informatika.",
            "gaya_penulisan": ["Gunakan bahasa akademis.", "Jelaskan prinsip dasar komponen."],
            "riwayat_koreksi": []
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default_mem, f, indent=2, ensure_ascii=False)
        return default_mem

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def tambah_pembelajaran(koreksi_baru):
    mem = load_memory()
    mem["riwayat_koreksi"].append(koreksi_baru)
    mem["gaya_penulisan"].append(f"Aturan tambahan: {koreksi_baru}")

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)

def build_prompt_with_memory(base_prompt):
    mem = load_memory()
    context = "=== INGATAN & PEDOMAN AI ===\n"
    for rule in mem['gaya_penulisan']:
        context += f"- {rule}\n"
    context += "\n=== TUGAS SEKARANG ===\n" + base_prompt
    return context
