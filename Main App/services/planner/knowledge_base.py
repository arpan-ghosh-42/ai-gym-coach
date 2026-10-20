"""RAG knowledge base: loads PDFs/Markdown/TXT, chunks them and serves BM25 retrieval.

PDFs are treated as the coach's own guides ("guide") and are always preferred over the
curated reference notes in knowledge_base/docs ("reference").
"""
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
CACHE_DIR = KB_DIR / ".cache"
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

CHUNK_CHARS = 1100
CHUNK_OVERLAP = 200

_STOPWORDS = set("""
a an and are as at be been being but by can could did do does for from had has have how i if in into is it
its just may more most much my no not of on or our out over per should so some such than that the their them
then there these they this those to too up us very was we were what when where which while who why will with
would you your about also any each other only own same both few after before between during above below
""".split())


@dataclass
class Chunk:
    text: str
    source: str
    section: str
    kind: str = "reference"  # "guide" (coach's PDFs) or "reference" (curated notes)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for t in tokens:
        if t in _STOPWORDS or len(t) < 2:
            continue
        # Light suffix stemming so "squats"/"squat", "training"/"train" match.
        for suffix in ("ing", "es", "s"):
            if len(t) > 4 and t.endswith(suffix):
                t = t[: -len(suffix)]
                break
        out.append(t)
    return out


def _window(text: str, source: str, section: str, kind: str = "reference") -> list[Chunk]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= CHUNK_CHARS:
        return [Chunk(text, source, section, kind)]
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + CHUNK_CHARS)
        # Prefer to break on a sentence boundary.
        if end < len(text):
            cut = text.rfind(". ", start + CHUNK_CHARS // 2, end)
            if cut != -1:
                end = cut + 1
        chunks.append(Chunk(text[start:end].strip(), source, section, kind))
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def _chunk_markdown(path: Path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    chunks: list[Chunk] = []
    section, buf = path.stem, []
    for line in raw.splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        if heading:
            if "".join(buf).strip():
                chunks += _window(f"{section}. " + " ".join(buf), path.name, section)
            section, buf = heading.group(1).strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        chunks += _window(f"{section}. " + " ".join(buf), path.name, section)
    return chunks


_REPEAT = re.compile(r"([A-Za-z0-9·•][^\n]{5,}?)\1+")


def _clean_pdf_page(text: str) -> str:
    """Designed PDFs often layer text (shadows/outlines), so extraction repeats phrases:
    'Muscle PlanMuscle PlanMuscle Plan'. Collapse those and drop lines repeated on the same page."""
    seen, out = set(), []
    for line in text.splitlines():
        prev = None
        while prev != line:
            prev, line = line, _REPEAT.sub(r"\1", line)
        key = line.strip().lower()
        if len(key) >= 25 and key in seen:
            continue
        seen.add(key)
        out.append(line)
    return "\n".join(out)


def _pdf_pages(path: Path) -> list[str]:
    """Extracted + cleaned page texts, cached on disk because large PDFs take a while to parse."""
    # Keyed on content (size + first/last MiB), not mtime: the Docker image pre-builds this cache and
    # mtimes don't survive image export exactly, which made every lookup miss on Render.
    size = path.stat().st_size
    digest = hashlib.sha1(f"{path.name}|{size}|v3".encode())
    with path.open("rb") as fh:
        digest.update(fh.read(1 << 20))
        if size > 1 << 20:
            fh.seek(max(size - (1 << 20), 1 << 20))
            digest.update(fh.read())
    cache_file = CACHE_DIR / f"{path.stem[:40]}-{digest.hexdigest()[:16]}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    print(f"[knowledge_base] parsing {path.name} (no cache) - this is slow on small CPUs", flush=True)
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
    except Exception:
        return []
    pages = []
    for page in reader.pages:
        try:
            pages.append(_clean_pdf_page(page.extract_text() or ""))
        except Exception:
            pages.append("")
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        for old in CACHE_DIR.glob(f"{path.stem[:40]}-*.json"):
            old.unlink()
        cache_file.write_text(json.dumps(pages), encoding="utf-8")
    except OSError:
        pass
    return pages


def _chunk_pdf(path: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page_no, text in enumerate(_pdf_pages(path), start=1):
        chunks += _window(text, path.name, f"page {page_no}", kind="guide")
    return chunks


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.doc_tokens = [Counter(_tokenize(c.section + " " + c.text)) for c in chunks]
        self.doc_len = [sum(t.values()) for t in self.doc_tokens]
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0.0
        df: Counter = Counter()
        for toks in self.doc_tokens:
            df.update(toks.keys())
        n = len(chunks)
        self.idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    def search(self, query: str, top_k: int = 4, kind: str | None = None) -> list[tuple[float, Chunk]]:
        q_terms = _tokenize(query)
        scores = []
        for i, toks in enumerate(self.doc_tokens):
            if kind and self.chunks[i].kind != kind:
                continue
            score = 0.0
            for term in q_terms:
                tf = toks.get(term)
                if not tf:
                    continue
                norm = tf + self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avgdl or 1))
                score += self.idf.get(term, 0.0) * tf * (self.k1 + 1) / norm
            if score > 0:
                scores.append((score, self.chunks[i]))
        scores.sort(key=lambda s: s[0], reverse=True)
        return scores[:top_k]


def _kb_files() -> list[Path]:
    if not KB_DIR.exists():
        return []
    return sorted(
        p for p in KB_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and p.name.lower() != "readme.md"
    )


def _kb_fingerprint() -> tuple:
    return tuple((str(p), p.stat().st_mtime, p.stat().st_size) for p in _kb_files())


@st.cache_resource(show_spinner=False)
def _build_index(fingerprint: tuple) -> BM25Index:
    chunks: list[Chunk] = []
    for path in _kb_files():
        if path.suffix.lower() == ".pdf":
            chunks += _chunk_pdf(path)
        else:
            chunks += _chunk_markdown(path)
    return BM25Index(chunks)


def get_index() -> BM25Index:
    """Returns the index, rebuilding automatically when files in knowledge_base/ change."""
    return _build_index(_kb_fingerprint())


def retrieve_context(queries: list[str], max_guide: int = 7, max_reference: int = 5) -> list[Chunk]:
    """Round-robins over the queries, filling a quota from the coach's own guides first,
    then topping up with curated reference notes."""
    index = get_index()
    seen, results = set(), []
    for kind, quota in (("guide", max_guide), ("reference", max_reference)):
        ranked = [index.search(q, top_k=quota * 2, kind=kind) for q in queries]
        # Cap each source so one huge PDF can't crowd out the others.
        n_sources = len({c.source for c in index.chunks if c.kind == kind}) or 1
        per_source_cap = max(2, math.ceil(quota / n_sources) + 1)
        per_source: Counter = Counter()
        taken, depth = 0, 0
        while taken < quota and any(depth < len(r) for r in ranked):
            for r in ranked:
                if depth >= len(r) or taken >= quota:
                    continue
                chunk = r[depth][1]
                key = (chunk.source, chunk.section, chunk.text[:80])
                if key in seen or per_source[chunk.source] >= per_source_cap:
                    continue
                seen.add(key)
                per_source[chunk.source] += 1
                results.append(chunk)
                taken += 1
            depth += 1
    return results


def knowledge_base_stats() -> dict:
    files = _kb_files()
    index = get_index()
    return {
        "documents": len(files),
        "pdfs": sum(1 for f in files if f.suffix.lower() == ".pdf"),
        "chunks": len(index.chunks),
        "guide_chunks": sum(1 for c in index.chunks if c.kind == "guide"),
    }
