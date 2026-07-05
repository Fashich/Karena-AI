"""Document parsers with async progress tracking."""

import asyncio
import io
from pathlib import Path
from typing import Callable, Awaitable, Optional


ProgressCb = Optional[Callable[[str, int, int, str], Awaitable[None]]]


async def parse_file_async(
    filename: str,
    content: bytes,
    progress_cb: ProgressCb = None,
) -> str:
    """Parse a document file and extract plain text, with optional progress callbacks."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await _parse_pdf_async(content, progress_cb)
    if ext in (".docx", ".doc"):
        return _parse_docx(content)
    return content.decode("utf-8", errors="replace")


def parse_file(filename: str, content: bytes) -> str:
    """Sync wrapper — used by legacy callers."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called inside async context, run via thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, parse_file_async(filename, content))
                return future.result()
        return loop.run_until_complete(parse_file_async(filename, content))
    except RuntimeError:
        return asyncio.run(parse_file_async(filename, content))


async def _parse_pdf_async(content: bytes, progress_cb: ProgressCb = None) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    total_pages = len(reader.pages)

    if progress_cb:
        await progress_cb("detect", 0, total_pages, f"Detected {total_pages} pages")

    # ── Try native text extraction ────────────────────────
    texts = []
    for i, page in enumerate(reader.pages):
        texts.append(page.extract_text() or "")
        if progress_cb and (i % 5 == 0 or i == total_pages - 1):
            await progress_cb(
                "reading", i + 1, total_pages,
                f"Reading page {i+1} of {total_pages}..."
            )

    text = "\n\n".join(texts).strip()

    # ── Fallback to OCR if no text found ─────────────────
    if len(text) < 50 and total_pages > 0:
        ocr_limit = total_pages  # Process all pages

        if progress_cb:
            await progress_cb(
                "ocr_start", 0, ocr_limit,
                f"Scanned PDF detected — OCR on {ocr_limit} of {total_pages} pages..."
            )

        loop = asyncio.get_event_loop()

        # Convert PDF → images in thread (cpu-bound)
        images = await loop.run_in_executor(
            None,
            lambda: _pdf_to_images(content, ocr_limit),  # All pages
        )

        texts = []
        for i, img in enumerate(images):
            if progress_cb:
                await progress_cb(
                    "ocr", i + 1, ocr_limit,
                    f"OCR: page {i+1} of {ocr_limit} (total {total_pages} pages)"
                )
            page_text = await loop.run_in_executor(None, lambda img=img: _ocr_image(img))
            texts.append(page_text)

        text = "\n\n".join(texts).strip()

    return text


def _pdf_to_images(content: bytes, last_page: int):
    from pdf2image import convert_from_bytes
    return convert_from_bytes(content, dpi=100, last_page=last_page)


def _ocr_image(img) -> str:
    import pytesseract
    import os
    # Windows path
    tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tess):
        pytesseract.pytesseract.tesseract_cmd = tess
    return pytesseract.image_to_string(img, lang="eng")


def _parse_docx(content: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(content))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
