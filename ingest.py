#!/usr/bin/env python3
"""
ingest.py — Document ingestion, cleaning, and chunking
SJSU Financial Aid & Scholarships RAG system

Stage 1  Fetch: download HTML pages and PDFs from the 10 sources in planning.md
Stage 2  Raw:   extract all text (tags removed, no content filtering); save to documents/raw/
Stage 3  Clean: remove nav, header, footer, cookie banners, boilerplate; fix entities
Stage 4  Chunk: semantic splits — h2/h3 boundaries for HTML, section headers for PDF
Output:  documents/chunks/all_chunks.json

Chunk spec (from planning.md):
  size    400–500 tokens  → 1,600–2,000 chars (using 4 chars ≈ 1 token)
  overlap  50–75 tokens   → 200–300 chars
  target   chunk_size=450 tokens, overlap=60 tokens
"""

import json
import re
import time
from pathlib import Path

import requests
import pdfplumber
from bs4 import BeautifulSoup

# ── output directories ─────────────────────────────────────────────────────────
RAW_DIR   = Path("documents/raw")
CHUNK_DIR = Path("documents/chunks")
RAW_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

# ── chunking constants (planning.md §Chunking Strategy) ───────────────────────
CHARS_PER_TOKEN  = 4         # 1 token ≈ 4 chars (planning.md: 400t ≈ 1,800c)
CHUNK_SIZE_TOK   = 450       # mid-point of 400–500 token target
OVERLAP_TOK      = 60        # mid-point of 50–75 token target
CHUNK_SIZE_CHARS = CHUNK_SIZE_TOK * CHARS_PER_TOKEN   # 1,800 chars
OVERLAP_CHARS    = OVERLAP_TOK    * CHARS_PER_TOKEN   # 240 chars
MIN_CHUNK_CHARS  = 250       # discard near-empty fragments (~62 tokens)
                             # removes PDF cover/contact-page/sidebar fragments

# ── source registry (planning.md §Documents) ──────────────────────────────────
SOURCES = [
    {"id": 1,  "name": "faso_main",                "type": "html",
     "url": "https://www.sjsu.edu/faso/"},
    {"id": 2,  "name": "faso_types_of_aid",        "type": "html",
     "url": "https://www.sjsu.edu/faso/types-of-aid/"},
    {"id": 3,  "name": "faso_seven_steps",         "type": "html",
     "url": "https://www.sjsu.edu/faso/process/seven-steps.php"},
    {"id": 4,  "name": "faso_scholarships",        "type": "html",
     "url": "https://www.sjsu.edu/faso/types-of-aid/scholarships/index.php"},
    {"id": 5,  "name": "faso_scholarship_resources", "type": "html",
     "url": "https://www.sjsu.edu/faso/types-of-aid/scholarships/scholarship-resources.php"},
    {"id": 6,  "name": "faso_eop_grant",           "type": "html",
     "url": "https://www.sjsu.edu/faso/types-of-aid/grants/eop-grant.php"},
    {"id": 7,  "name": "faso_brochure_pdf",        "type": "pdf",
     "url": "https://www.sjsu.edu/enrollmentmanagement/docs/fall2025/FinancialAid2025-26.pdf"},
    {"id": 8,  "name": "as_scholarships",          "type": "html",
     "url": "https://www.sjsu.edu/as/departments/government/scholarships.php"},
    {"id": 9,  "name": "faso_verification",         "type": "html",
     "url": "https://www.sjsu.edu/faso/process/verification.php"},
     # Note: the original fraud PDF URL (faso/docs/Avoid_Financial_Aid_Fraud.pdf)
     # returned 404 as of 2026-06. Replaced with the FASO Verification page, which
     # covers verification requirements — equally important for students.
    {"id": 10, "name": "undocuspartan_finaid",     "type": "html",
     "url": "https://www.sjsu.edu/undocuspartan/paying-for-college/fin-aid-resources.php"},
    {"id": 11, "name": "faso_loans",               "type": "html",
     "url": "https://www.sjsu.edu/faso/types-of-aid/loans/index.php"},
    {"id": 12, "name": "faso_work_study",          "type": "html",
     "url": "https://www.sjsu.edu/faso/types-of-aid/work-study/index.php"},
]

# ── boilerplate patterns to strip during HTML cleaning ────────────────────────
_STRIP_TAGS = {"script", "style", "noscript", "iframe", "svg"}
_BOILERPLATE = re.compile(
    r"\b(nav|menu|breadcrumb|cookie|banner|sidebar|footer|header|"
    r"search|share|social|advertisement|skip|utility|masthead|"
    r"alert|notification|promo|cta|modal|overlay|back-to-top|"
    r"flyout|mega-menu|top-bar|site-header|site-footer)\b",
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — FETCH
# ══════════════════════════════════════════════════════════════════════════════

_HEADERS = {"User-Agent": "Mozilla/5.0 (SJSU AI class research bot)"}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_pdf(url: str, dest: Path) -> None:
    resp = requests.get(url, headers=_HEADERS, timeout=60, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            fh.write(chunk)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — RAW TEXT EXTRACTION  (all content, no filtering)
# ══════════════════════════════════════════════════════════════════════════════

def extract_raw_html_text(raw_html: str) -> str:
    """Minimal extraction: remove script/style tags but keep all other text."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup.find_all(list(_STRIP_TAGS)):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF page-by-page."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n\n".join(pages)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — CLEANING
# ══════════════════════════════════════════════════════════════════════════════

def _has_boilerplate_attr(tag) -> bool:
    # attrs can be None on detached tags — guard defensively
    attrs = getattr(tag, "attrs", None)
    if attrs is None:
        return False
    joined = " ".join(attrs.get("class") or []) + " " + (attrs.get("id") or "")
    return bool(_BOILERPLATE.search(joined))


def clean_html(raw_html: str) -> str:
    """
    Remove nav, header, footer, cookie banners, share buttons, and other
    boilerplate from raw HTML. Convert h2/h3 headings to ## markers so the
    chunker can split on semantic section boundaries.
    Keep: article body, eligibility text, deadlines, amounts, step descriptions.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    # Drop script / style / non-visible tags
    for tag in soup.find_all(list(_STRIP_TAGS)):
        tag.decompose()

    # Drop structural chrome regardless of class/id
    for tag in list(soup.find_all(["nav", "header", "footer", "aside"])):
        tag.decompose()

    # Drop any element whose class or id signals it is boilerplate.
    # Collect first, then decompose — modifying the tree while iterating
    # over find_all() detaches child nodes and sets their .attrs to None.
    boilerplate = [t for t in soup.find_all(True) if _has_boilerplate_attr(t)]
    for tag in boilerplate:
        tag.decompose()

    # Prefer <main> or <article> for content; fall back to <body>
    content = soup.find("main") or soup.find("article") or soup.find("body") or soup

    # Replace h2/h3 with ## markers so chunk_text() can split at topic boundaries
    for h in content.find_all(["h2", "h3"]):
        h.replace_with(f"\n\n## {h.get_text(strip=True)}\n\n")

    text = content.get_text(separator="\n", strip=True)

    # Fix common HTML entities that survive BeautifulSoup
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    text = text.replace("&gt;", ">").replace("&lt;", "<").replace("&quot;", '"')

    # Remove in-page anchor nav blocks ("Jump to:\nFoo\nBar\nBaz") that survive
    # as plain text because they're inside <main> but not caught by class patterns.
    text = re.sub(r"(?m)^Jump to:\n(?:.+\n){1,8}", "", text)

    # Normalise whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_pdf_text(raw_text: str) -> str:
    """
    Light cleaning for PDF-extracted text: drop stray page numbers and
    repeated header lines; normalise whitespace.
    """
    lines = raw_text.splitlines()
    # Remove lines that are just page numbers (1–3 digit numbers alone on a line)
    lines = [ln for ln in lines if not re.fullmatch(r"\s*\d{1,3}\s*", ln)]
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — CHUNKING
# ══════════════════════════════════════════════════════════════════════════════

def _char_window_split(text: str, size: int, overlap: int) -> list[str]:
    """
    Sliding-window fallback. Breaks at the nearest sentence end before the limit
    to avoid cutting mid-sentence.
    """
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # prefer breaking at a sentence boundary in the latter half
            boundary = text.rfind(".", start + size // 2, end)
            if boundary != -1:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break           # reached the end — stop to avoid infinite loop from overlap
        start = end - overlap
    return chunks


def _split_section(section: str, size: int, overlap: int) -> list[str]:
    """
    Split a section that exceeds the size limit.
    Tries paragraph breaks first; falls back to character windowing.
    """
    if len(section) <= size:
        return [section]

    paras = re.split(r"\n\n+", section)
    result, current = [], ""
    for para in paras:
        candidate = (current + "\n\n" + para).strip() if current else para
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                result.append(current)
                # carry overlap into the next window
                tail = current[-overlap:].strip()
                current = (tail + "\n\n" + para).strip() if tail else para
            else:
                # single paragraph exceeds limit → character window
                result.extend(_char_window_split(para, size, overlap))
                current = ""
    if current:
        result.append(current)
    return result or _char_window_split(section, size, overlap)


def chunk_text(
    text: str,
    source_type: str,
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = OVERLAP_CHARS,
) -> list[str]:
    """
    Split cleaned document text into overlapping chunks at semantic boundaries.

    HTML  — splits on ## heading markers injected during clean_html(); each
            heading starts a new topic section (e.g. "Federal Pell Grant",
            "Cal Grant A and B"). Sections longer than chunk_size are
            subdivided at paragraph boundaries.

    PDF   — splits on ALL-CAPS or Title-Case short lines that act as bold
            section headers in the brochure; falls back to paragraph splits.
    """
    raw_sections: list[str] = []

    if source_type == "html":
        raw_sections = re.split(r"\n\n##\s+", text)

    else:  # pdf
        # Heuristic: a PDF section header is a short line (≤ 80 chars) that is
        # either ALL CAPS or Title Case and stands alone on its line.
        header_re = re.compile(
            r"(?m)^([A-Z][A-Za-z\s\-&/:,]{3,79})\n(?=[A-Z\s])"
        )
        parts = header_re.split(text)
        # parts: [pre, header1, body1, header2, body2, ...]
        if len(parts) == 1:
            raw_sections = [text]
        else:
            if parts[0].strip():
                raw_sections.append(parts[0])
            for i in range(1, len(parts) - 1, 2):
                header = parts[i].strip()
                body   = parts[i + 1] if i + 1 < len(parts) else ""
                raw_sections.append(f"{header}\n\n{body}".strip())

    chunks: list[str] = []
    for section in raw_sections:
        section = section.strip()
        if not section:
            continue
        for sub in _split_section(section, chunk_size, overlap):
            if len(sub.strip()) >= MIN_CHUNK_CHARS:
                chunks.append(sub.strip())

    return chunks


def build_chunk_dicts(
    text_chunks: list[str],
    source: dict,
) -> list[dict]:
    """Wrap raw text chunks in metadata dicts."""
    return [
        {
            "text":        chunk,
            "source_url":  source["url"],
            "source_name": source["name"],
            "source_id":   source["id"],
            "source_type": source["type"],
            "chunk_index": idx,
            "token_est":   len(chunk) // CHARS_PER_TOKEN,
        }
        for idx, chunk in enumerate(text_chunks)
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def process_source(source: dict) -> list[dict]:
    name    = source["name"]
    url     = source["url"]
    sid     = source["id"]
    stype   = source["type"]
    is_short = source.get("is_short", False)

    print(f"\n[{sid:02d}] {name}  ({stype})")

    # ── Stage 1 + 2: Fetch & extract raw text ─────────────────────────────────
    raw_txt_path = RAW_DIR / f"{name}_raw.txt"

    if stype == "html":
        html_cache = RAW_DIR / f"{name}.html"
        if not html_cache.exists():
            print(f"     fetching {url}")
            raw_html = fetch_html(url)
            html_cache.write_text(raw_html, encoding="utf-8")
            time.sleep(1)   # polite crawl delay
        else:
            print(f"     using cached HTML")
            raw_html = html_cache.read_text(encoding="utf-8")

        if not raw_txt_path.exists():
            raw_txt = extract_raw_html_text(raw_html)
            raw_txt_path.write_text(raw_txt, encoding="utf-8")

        # ── Stage 3: Clean ────────────────────────────────────────────────────
        clean_text = clean_html(raw_html)

    else:  # pdf
        pdf_cache = RAW_DIR / f"{name}.pdf"
        if not pdf_cache.exists():
            print(f"     downloading PDF {url}")
            fetch_pdf(url, pdf_cache)
            time.sleep(1)
        else:
            print(f"     using cached PDF")

        if not raw_txt_path.exists():
            raw_txt = extract_pdf_text(pdf_cache)
            raw_txt_path.write_text(raw_txt, encoding="utf-8")
        else:
            raw_txt = raw_txt_path.read_text(encoding="utf-8")

        # ── Stage 3: Clean ────────────────────────────────────────────────────
        clean_text = clean_pdf_text(raw_txt)

    char_count = len(clean_text)
    print(f"     clean text: {char_count:,} chars  (~{char_count // CHARS_PER_TOKEN:,} tokens)")

    # ── Stage 4: Chunk ────────────────────────────────────────────────────────
    # Short PDFs (Source 9 — fraud handout ~600 tokens) kept as a single chunk
    if is_short:
        text_chunks = [clean_text]
    else:
        text_chunks = chunk_text(clean_text, stype)

    chunk_dicts = build_chunk_dicts(text_chunks, source)
    sizes = [c["token_est"] for c in chunk_dicts]
    print(f"     {len(chunk_dicts)} chunks  |  tokens: {min(sizes)}–{max(sizes)}, avg {sum(sizes)//len(sizes)}")

    return chunk_dicts


def main() -> None:
    all_chunks: list[dict] = []

    for source in SOURCES:
        try:
            chunks = process_source(source)
            all_chunks.extend(chunks)
        except Exception as exc:
            print(f"     ERROR on source {source['id']}: {exc}")

    out_path = CHUNK_DIR / "all_chunks.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(all_chunks, fh, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Total chunks produced: {len(all_chunks)}")
    print(f"Saved to:              {out_path}")

    # ── print one sample chunk so you can visually inspect the output ─────────
    if all_chunks:
        sample = all_chunks[0]
        print(f"\n── Sample chunk  (source {sample['source_id']}, chunk #{sample['chunk_index']}) ──")
        print(f"source : {sample['source_name']}")
        print(f"tokens : ~{sample['token_est']}")
        print(f"text   :\n{sample['text'][:800]}")
        if len(sample["text"]) > 800:
            print("  [... truncated for display ...]")


if __name__ == "__main__":
    main()
