"""Turn uploaded files into plain text for the knowledge base."""
from __future__ import annotations

import io
import re
from pathlib import PurePosixPath

ALLOWED_EXTENSIONS = (".pdf", ".md", ".txt", ".csv")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class DocumentError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def safe_name(filename: str) -> str:
    name = PurePosixPath(filename.replace("\\", "/")).name.strip()
    name = re.sub(r"[^\w.\- ]", "_", name)[:100].strip(" .")
    return name or "document.txt"


def extract_text(filename: str, data: bytes) -> str:
    ext = PurePosixPath(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentError("unsupported_type", f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentError("too_large", "File is larger than 5 MB.")
    if ext == ".pdf":
        text = _pdf_text(data)
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
    text = text.strip()
    if not text:
        raise DocumentError("empty", "No text found in this file (scanned PDFs are not supported).")
    return text


def _pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentError("pdf_missing", "PDF support needs pypdf: pip install pypdf") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise DocumentError("pdf_unreadable", "Could not read this PDF.") from exc
