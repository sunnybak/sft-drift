"""Export ordinary Markdown through HTML/Chromium, preserving links and images.

Optional dependencies are loaded only by this command. No experiment, model or
configuration is involved. Local assets resolve relative to the source document.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import mimetypes
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata
from urllib.parse import unquote, urlsplit, urlunsplit


STYLE = """
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; line-height: 1.4; color: #18212b; }
h1 { font-size: 22pt; line-height: 1.15; margin: 0 0 16pt; }
h2 { font-size: 15pt; margin: 22pt 0 10pt; }
h3 { font-size: 11.5pt; margin: 16pt 0 8pt; overflow-wrap: anywhere; }
h1, h2, h3, h4 { break-after: avoid; }
p { margin: 7pt 0; orphans: 3; widows: 3; }
a { color: #245b8e; text-decoration: none; overflow-wrap: anywhere; }
ul, ol { padding-left: 19pt; }
li { margin: 4pt 0; break-inside: avoid; }
strong { font-weight: 600; }
code { font-family: Menlo, Consolas, monospace; font-size: 9pt; overflow-wrap: anywhere; }
pre { padding: 9pt; background: #f2f4f7; white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 9pt; line-height: 1.3; break-inside: avoid; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td { padding: 5pt 6pt; border-bottom: 0.5pt solid #d9dfe5; vertical-align: top; overflow-wrap: anywhere; }
th { text-align: left; background: #f2f4f7; font-weight: 600; }
img { max-width: 100%; max-height: 215mm; height: auto; object-fit: contain; }
.pdf-figure { break-inside: avoid; text-align: center; margin: 12pt 0; }
.pdf-figure img { display: block; margin: auto; }
.pdf-figure-intro { break-after: avoid; }
.pdf-subsection { break-inside: avoid; }
.pdf-appendix { break-before: page; }
.pdf-wide-figure { page: widefigure; break-before: page; break-after: page; }
.pdf-wide-figure img { max-height: 140mm; }
blockquote { margin-left: 0; padding-left: 12pt; border-left: 2pt solid #c5cdd5; }
"""


def heading_slug(text: str) -> str:
    """GitHub-like anchors, including the underscores in this repo's belief IDs."""
    text = unicodedata.normalize("NFKC", text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text) or "section"


class _IDs(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.ids: set[str] = set()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id" and value:
                if value in self.ids:
                    raise ValueError(f"Duplicate HTML anchor: {value}")
                self.ids.add(value)

    handle_startendtag = handle_starttag


class _Assets(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.parts: list[str] = []
        self.ids: set[str] = set()
        self.internal_links: list[str] = []
        self.local_links: list[str] = []
        self.n_images = 0

    def _url(self, value: str, *, image=False) -> str:
        url = urlsplit(value)
        if not url.path and url.fragment and not url.scheme:
            if image:
                raise ValueError(f"Image has no source: {value}")
            self.internal_links.append(unquote(url.fragment))
            return value
        if url.scheme in ("http", "https", "data", "mailto", "tel"):
            return value
        if url.scheme and url.scheme != "file":
            raise ValueError(f"Unsupported URL scheme: {url.scheme}")
        if url.netloc and url.scheme != "file":
            return "https:" + value
        path = Path(unquote(url.path))
        if not path.is_absolute():
            path = self.source.parent / path
        path = path.resolve()
        if not path.exists():
            kind = "Image" if image else "Linked file"
            raise ValueError(f"{kind} not found: {path}")
        if not image and path == self.source and url.fragment:
            self.internal_links.append(unquote(url.fragment))
            return "#" + url.fragment
        if image:
            if not path.is_file():
                raise ValueError(f"Image is not a file: {path}")
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        self.local_links.append(str(path))
        return urlunsplit((*urlsplit(path.as_uri())[:3], url.query, url.fragment))

    def _tag(self, tag, attrs, closing=False):
        attrs = list(attrs)
        for i, (key, value) in enumerate(attrs):
            if key == "id" and value:
                if value in self.ids:
                    raise ValueError(f"Duplicate HTML anchor: {value}")
                self.ids.add(value)
            if tag == "a" and key == "href" and value:
                attrs[i] = (key, self._url(value))
            if tag == "img" and key == "src" and value:
                attrs[i] = (key, self._url(value, image=True))
                self.n_images += 1
        rendered = "".join(" " + key + ("" if value is None else '=\"' + escape(value, quote=True) + '\"')
                           for key, value in attrs)
        self.parts.append("<" + tag + rendered + (" />" if closing else ">"))

    def handle_starttag(self, tag, attrs):
        self._tag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._tag(tag, attrs, closing=True)

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append("<!--" + data + "-->")


@dataclass(frozen=True)
class MarkdownDocument:
    html: str
    title: str
    n_images: int
    n_internal_links: int
    n_local_file_links: int


def markdown_document(source: Path) -> MarkdownDocument:
    """Render Markdown, inline local images, and reject broken local references."""
    try:
        from markdown_it import MarkdownIt
    except ImportError as exc:
        raise RuntimeError("Install PDF dependencies: uv sync --extra pdf") from exc
    source = source.expanduser().resolve()
    parser = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = parser.parse(source.read_text(encoding="utf-8"))
    raw_html = parser.renderer.render(tokens, parser.options, {})
    used = _IDs(raw_html).ids
    title = source.stem.replace("_", " ")
    title_found = False
    for i, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        inline = tokens[i+1]
        text = "".join(t.content for t in inline.children or [] if t.type in ("text", "code_inline"))
        slug = heading_slug(text)
        base, index = slug, 1
        while slug in used:
            slug = f"{base}-{index}"
            index += 1
        used.add(slug)
        token.attrSet("id", slug)
        if token.tag == "h2" and text.lower().startswith("appendix"):
            token.attrSet("class", "pdf-appendix")
        if token.tag == "h1" and not title_found:
            title, title_found = text, True
    assets = _Assets(source)
    assets.feed(parser.renderer.render(tokens, parser.options, {}))
    assets.close()
    missing = sorted(set(assets.internal_links) - assets.ids)
    if missing:
        raise ValueError("Internal link target(s) not found: " + ", ".join(missing))
    body = "".join(assets.parts)
    html = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>{escape(title)}</title><style>{STYLE}</style></head><body>{body}</body></html>")
    return MarkdownDocument(html, title, assets.n_images, len(assets.internal_links), len(assets.local_links))


def _system_browser():
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    for path in ("/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if Path(path).is_file():
            return path
    return None


@dataclass(frozen=True)
class PDFExport:
    path: Path
    pages: int
    images: int
    internal_links: int
    local_file_links: int


def export_markdown_pdf(source: Path, output: Path | None = None, *, browser_path: Path | None = None,
                        page_size="A4", keep_html=False, landscape_figures=False) -> PDFExport:
    """Export atomically, with clickable anchors/URLs, embedded images and bookmarks."""
    try:
        from playwright.sync_api import sync_playwright
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install PDF dependencies: uv sync --extra pdf") from exc
    source = source.expanduser().resolve()
    if page_size not in ("A4", "Letter"):
        raise ValueError("page_size must be A4 or Letter")
    output = (output or source.with_suffix(".pdf")).expanduser().resolve()
    if output == source or output.suffix.lower() != ".pdf":
        raise ValueError("Output must be a separate .pdf file")
    document = markdown_document(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".bt-pdf-", dir=output.parent) as temporary:
        html_path, pdf_path = Path(temporary)/"document.html", Path(temporary)/"document.pdf"
        page_style = f"@page {{ size: {page_size}; }} @page widefigure {{ size: {page_size} landscape; }}"
        html_path.write_text(document.html.replace("</style>", page_style+"</style>"), encoding="utf-8")
        with sync_playwright() as playwright:
            executable = str(browser_path.expanduser().resolve()) if browser_path else _system_browser()
            try:
                browser = playwright.chromium.launch(headless=True, executable_path=executable)
            except Exception as exc:
                raise RuntimeError("Chromium could not start. Run `uv run playwright install chromium`, "
                                   "or pass --browser /path/to/chromium. " + str(exc)) from exc
            try:
                page = browser.new_page(java_script_enabled=False, color_scheme="light")
                page.goto(html_path.as_uri(), wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                broken = page.locator("img").evaluate_all("imgs => imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.alt || i.src.slice(0, 100))")
                if broken:
                    raise ValueError("Image(s) failed to load: " + ", ".join(broken))
                # Keep short headed sections (e.g. individual appendix definitions) intact.
                page.evaluate("""landscapeFigures => {
                  for (const heading of [...document.querySelectorAll('h3')]) {
                    const section = document.createElement('section'); section.className='pdf-subsection';
                    heading.before(section); let next=heading;
                    while(next && (next===heading || !/^H[123]$/.test(next.tagName))) {
                      const following=next.nextElementSibling;section.append(next);next=following;
                    }
                  }
                  for (const img of document.images) {
                    if (img.parentElement.tagName==='P') {
                      const p=img.parentElement;p.classList.add('pdf-figure');
                      const before=p.previousElementSibling;
                      if(before?.tagName==='P')before.classList.add('pdf-figure-intro');
                      if(landscapeFigures && img.naturalWidth > img.naturalHeight) {
                        const section=document.createElement('section');section.className='pdf-wide-figure';
                        p.before(section);
                        if(before?.tagName==='P' && !before.querySelector('img'))section.append(before);
                        section.append(p);
                      }
                    }
                  }
                }""", landscape_figures)
                footer = ('<div style="width:100%;text-align:center;font-family:Arial;font-size:8px;color:#66717d">'
                          '<span class="pageNumber"></span> / <span class="totalPages"></span></div>')
                print_html = page.content()
                page.pdf(path=str(pdf_path), format=page_size, prefer_css_page_size=True,
                         margin={"top": "18mm", "right": "18mm", "bottom": "18mm", "left": "18mm"},
                         print_background=True, display_header_footer=True, header_template="<span></span>",
                         footer_template=footer, outline=True, tagged=True)
            finally:
                browser.close()
        reader = PdfReader(pdf_path)
        links = [a.get_object() for p in reader.pages for a in p.get("/Annots", [])
                 if a.get_object().get("/Subtype") == "/Link"]
        internal = sum("/Dest" in a or a.get("/A", {}).get("/S") == "/GoTo" for a in links)
        if document.n_internal_links and internal < document.n_internal_links:
            raise RuntimeError("PDF did not retain all internal hyperlinks")
        if not reader.pages:
            raise RuntimeError("PDF is empty")
        result = PDFExport(output, len(reader.pages), document.n_images,
                           document.n_internal_links, document.n_local_file_links)
        pdf_path.replace(output)
    if keep_html:
        output.with_suffix(".html").write_text(print_html, encoding="utf-8")
    return result
