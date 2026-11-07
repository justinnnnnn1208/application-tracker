import io
import re
import zipfile
from xml.etree import ElementTree

from pypdf import PdfReader
from app.services.errors import NeedsInput

HEADINGS = {
    "education": "education", "academic qualifications": "education",
    "experience": "experience", "work experience": "experience", "employment": "experience",
    "projects": "project", "personal projects": "project",
    "skills": "skill", "technical skills": "skill",
}
CONTACT = re.compile(r"@|https?://|\b(?:date of birth|nationality|right to work|visa|sponsorship|gender|disability|convictions|address|consent)\b", re.I)


def extract_text(data: bytes, format: str) -> str:
    try:
        if format == "txt":
            text = data.decode("utf-8-sig")
        elif format == "pdf":
            if not data.startswith(b"%PDF-"):
                raise ValueError("Not PDF")
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted or len(reader.pages) > 30:
                raise ValueError("Unsupported PDF")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif format == "docx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                total = sum(item.file_size for item in archive.infolist())
                if total > 20_000_000 or len(archive.infolist()) > 2000:
                    raise ValueError("Oversized document archive")
                raw = archive.read("word/document.xml")
                if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
                    raise ValueError("Unsupported XML")
                tree = ElementTree.fromstring(raw)
                namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                text = "\n".join("".join(p.itertext()) for p in tree.iter(f"{namespace}p"))
        else:
            raise ValueError("Unsupported format")
        if not text.strip() or len(text) > 200_000:
            raise ValueError("No readable text or too much text")
        return text
    except Exception:
        # Do not leak filenames, text, XML, PDF contents or library exceptions.
        raise NeedsInput("The CV could not be read. Use a text-based PDF, DOCX or UTF-8 TXT file (up to 30 pages).") from None


def candidates(text: str):
    category = None
    result = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("•-*").strip()
        heading = line.lower().rstrip(":")
        if heading in HEADINGS:
            category = HEADINGS[heading]
            continue
        # These are verbatim candidates, not inferred claims. No legal/contact fields.
        if 8 <= len(line) <= 5000 and not CONTACT.search(line) and not re.fullmatch(r"[\d\s()+.-]+", line):
            result.append({"content": line, "category": category})
        if len(result) >= 200:
            break
    return result
