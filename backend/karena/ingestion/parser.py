"""Document parsers for enterprise formats."""

import io
from pathlib import Path


def parse_file(filename: str, content: bytes) -> str:
  ext = Path(filename).suffix.lower()
  if ext == ".pdf":
    return _parse_pdf(content)
  if ext in (".docx", ".doc"):
    return _parse_docx(content)
  if ext in (".txt", ".md", ".html"):
    return content.decode("utf-8", errors="replace")
  return content.decode("utf-8", errors="replace")


def _parse_pdf(content: bytes) -> str:
  from pypdf import PdfReader

  reader = PdfReader(io.BytesIO(content))
  return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(content: bytes) -> str:
  from docx import Document

  doc = Document(io.BytesIO(content))
  return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
