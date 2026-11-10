"""
Modul Safety & Guardrails — IT Helpdesk Assistant.
Mengimplementasikan pertahanan terhadap:
1. Instruction Override Resistance (Prompt Injection)
2. Information Boundary Protection (System Prompt & Credential Leakage)
3. Scope Consistency (Out-of-Scope / Sensitive Topics)
4. Malformed / Unexpected Input Handling
"""

import re
from typing import Optional, Tuple

# Pola untuk mendeteksi Instruction Override / Prompt Injection
INJECTION_PATTERNS = [
    r"\b(abaikan|lupakan|hapus)\s+(semua\s+)?(instruksi|aturan|batasan|perintah)\b",
    r"\b(ignore|forget|override)\s+(all\s+)?(instructions|rules|prompts|system)\b",
    r"\bkamu\s+sekarang\s+(adalah|menjadi|berperan)\b",
    r"\b(act\s+as|pretend\s+to\s+be|you\s+are\s+now)\b",
    r"\b(jailbreak|dan\s+mode|unrestricted|tanpa\s+aturan)\b",
    r"\b(bypass\s+filter|tuliskan\s+pesan\s+kasar)\b",
]

# Pola untuk mendeteksi pembocoran informasi internal (Information Boundary)
LEAKAGE_PATTERNS = [
    r"\b(system\s+prompt|instruksi\s+internal|instruksi\s+sistem)\b",
    r"\b(api[-_ ]?key|kredensial|secret[-_ ]?key|token\s+rahasia)\b",
    r"\b(bocorkan|tampilkan|cetak)\s+(seluruh\s+)?(prompt|instruksi|rahasia|konfigurasi)\b",
    r"\b(database\s+credentials|password\s+admin|connection\s+string)\b",
]

# Pola untuk mendeteksi topik sensitif / di luar domain (Scope Consistency)
OUT_OF_SCOPE_PATTERNS = [
    r"\b(partai\s+politik|calon\s+presiden|capres|cawapres|pemilu|pilpres|politik\s+di\s+indonesia)\b",
    r"\b(partai\s+mana\s+yang\s+paling\s+korup|siapa\s+yang\s+harus\s+saya\s+pilih)\b",
    r"\b(membuat\s+bom|senjata\s+tajam|narkoba|obat\s+terlarang)\b",
]


def check_input_guardrails(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Memeriksa input query terhadap seluruh kebijakan guardrail.
    Mengembalikan: (is_safe: bool, reason: str, response_override: str)
    """
    if query is None:
        return False, "empty_input", "Permintaan Anda tidak valid (null). Mohon masukkan pertanyaan yang jelas."

    cleaned = query.strip()

    # 1. Malformed / Empty Input
    if len(cleaned) == 0:
        return False, "empty_input", (
            "Pertanyaan Anda kosong. Silakan tuliskan pertanyaan seputar kebijakan HR, "
            "panduan IT, atau sebutkan nomor tiket Anda (contoh: TICKET-0001)."
        )

    # 2. Buffer Stress / Excessive Length
    if len(cleaned) > 2000:
        return False, "buffer_stress", (
            "Pertanyaan yang Anda masukkan melebihi batas panjang maksimum (2000 karakter). "
            "Harap persingkat pertanyaan Anda agar dapat kami proses dengan baik."
        )

    # 3. Instruction Override Resistance (Prompt Injection)
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, "prompt_injection", (
                "Maaf, saya diprogram khusus sebagai asisten IT Helpdesk internal perusahaan dan "
                "harus mematuhi panduan operasional resmi. Saya tidak dapat mengubah peran atau "
                "mengabaikan instruksi sistem. Silakan tanyakan hal seputar operasional IT atau HR."
            )

    # 4. Information Boundary Protection
    for pattern in LEAKAGE_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, "information_leakage", (
                "Maaf, informasi konfigurasi internal, system prompt, dan kredensial sistem dilindungi "
                "oleh kebijakan keamanan perusahaan dan tidak dapat dibagikan. "
                "Ada hal lain terkait layanan IT/HR yang bisa saya bantu?"
            )

    # 5. Scope Consistency (Sensitif / Politik)
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, "scope_violation", (
                "Maaf, sebagai asisten IT Helpdesk internal perusahaan, saya hanya dapat membantu "
                "pertanyaan seputar kebijakan HR, operasional kantor, dan kendala teknis IT. "
                "Saya tidak memiliki kapasitas untuk membahas opini pribadi atau isu politik."
            )

    return True, None, None


def sanitize_output(output: str) -> str:
    """
    Memastikan output tidak secara tidak sengaja membocorkan token, API Key, atau traceback internal.
    """
    if not output:
        return output

    # Sensor jika ada pola API key Gemini (misal AIzaSy... atau AQ.Ab8...)
    sanitized = re.sub(r"AIzaSy[A-Za-z0-9_-]{33}", "[REDACTED_API_KEY]", output)
    sanitized = re.sub(r"AQ\.[A-Za-z0-9_-]{40,}", "[REDACTED_API_KEY]", sanitized)

    return sanitized
