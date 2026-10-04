from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path

from fpdf import FPDF


def _unicode_font_path() -> Path:
    candidates = [
        Path(os.getenv("PDF_UNICODE_FONT", "")),
        Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts" / "Nirmala.ttf",
        Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts" / "NirmalaS.ttf",
        Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf"),
    ]
    for candidate in candidates:
        if str(candidate) and candidate.is_file():
            return candidate
    raise ValueError(
        "A Unicode font is required for non-Latin PDF content. "
        "Install a Devanagari-capable font or set PDF_UNICODE_FONT."
    )


def generate_pdf(content: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if any(ord(character) > 255 for character in content):
        pdf.add_font("SangyanUnicode", fname=str(_unicode_font_path()))
        pdf.set_font("SangyanUnicode", size=11)
        pdf.set_text_shaping(use_shaping_engine=True, language="hi")
    else:
        pdf.set_font("Helvetica", size=11)
    lines = content.splitlines()
    for line in lines:
        if line.strip():
            pdf.multi_cell(0, 8, line)
        else:
            pdf.ln(5)
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
