# render.py

import sys
import json
import base64
import html
import mimetypes
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, unquote

from log_utils import log_step


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ---------------------------
# Inline renderer
# ---------------------------
def render_inline(nodes: List[Dict[str, Any]]) -> str:
    out: List[str] = []

    for n in nodes:
        t = n["type"]

        if t == "text":
            out.append(esc(n["value"]))
        elif t == "bold":
            out.append(f"<strong>{esc(n['value'])}</strong>")
        elif t == "italic":
            out.append(f"<em>{esc(n['value'])}</em>")
        elif t == "highlight":
            out.append(f"<mark>{esc(n['value'])}</mark>")
        elif t == "strike":
            out.append(f"<del>{esc(n['value'])}</del>")
        elif t == "code":
            out.append(f"<code>{esc(n['value'])}</code>")
        elif t == "link":
            out.append(f'<a href="{esc(n["url"])}">{esc(n["text"])}</a>')
        elif t == "image":
            alt = esc(n.get("alt", ""))
            width_percent = n.get("width_percent")
            style = ""
            if isinstance(width_percent, (int, float)):
                style = f' style="width: {width_percent}%; height: auto;"'
            out.append(f'<img src="{esc(n["url"])}" alt="{alt}"{style}>')
        elif t == "math_inline":
            # Use MathJax default delimiters and keep TeX unescaped.
            out.append(f'<span class="math">\\({n["content"]}\\)</span>')
        elif t == "linebreak":
            out.append("<br>")

    return "".join(out)


# ---------------------------
# Block renderer
# ---------------------------
def render_list_items(items: List[Dict[str, Any]], list_type: str) -> str:
    rendered_items = []
    for it in items:
        content = render_inline(it["content"])
        nested = ""
        if it.get("children"):
            nested = "".join(render_blocks(it["children"]))
        if it["checkbox"] is True or it["checkbox"] is False:
            checked = " checked" if it["checkbox"] else ""
            rendered_items.append(
                "<li class=\"task-list-item\">"
                f"<input type=\"checkbox\" disabled{checked}> "
                f"{content}"
                f"{nested}</li>"
            )
        else:
            rendered_items.append(f"<li>{content}{nested}</li>")
    tag = "ol" if list_type == "ordered" else "ul"
    return f"<{tag}>{''.join(rendered_items)}</{tag}>"


def resolve_local_images(nodes: List[Dict[str, Any]], base_dir: Optional[str]) -> None:
    if not base_dir:
        return
    for n in nodes:
        n_type = n.get("type")
        if n_type == "image":
            url = n.get("url", "")
            if isinstance(url, str) and url.startswith("local:"):
                rel = url[len("local:"):].strip()
                if rel:
                    if os.path.isabs(rel):
                        path = rel
                    else:
                        path = os.path.normpath(os.path.join(base_dir, rel))
                    n["url"] = Path(path).as_uri()
        if n_type in {"paragraph", "heading"}:
            resolve_local_images(n.get("content", []), base_dir)
        elif n_type == "blockquote":
            resolve_local_images(n.get("children", []), base_dir)
        elif n_type == "callout":
            resolve_local_images(n.get("title", []), base_dir)
            resolve_local_images(n.get("children", []), base_dir)
        elif n_type == "list":
            for item in n.get("items", []):
                resolve_local_images(item.get("content", []), base_dir)
                for child in item.get("children", []):
                    resolve_local_images([child], base_dir)
        elif n_type == "table":
            for cell in n.get("header", []):
                resolve_local_images(cell, base_dir)
            for row in n.get("rows", []):
                for cell in row:
                    resolve_local_images(cell, base_dir)

def inline_file_images(nodes: List[Dict[str, Any]]) -> None:
    for n in nodes:
        n_type = n.get("type")
        if n_type == "image":
            url = n.get("url", "")
            if isinstance(url, str) and url.startswith("file://"):
                path = unquote(urlparse(url).path)
                if os.path.isfile(path):
                    mime, _ = mimetypes.guess_type(path)
                    if mime:
                        with open(path, "rb") as f:
                            data = base64.b64encode(f.read()).decode("ascii")
                        n["url"] = f"data:{mime};base64,{data}"
        if n_type in {"paragraph", "heading"}:
            inline_file_images(n.get("content", []))
        elif n_type == "blockquote":
            inline_file_images(n.get("children", []))
        elif n_type == "callout":
            inline_file_images(n.get("title", []))
            inline_file_images(n.get("children", []))
        elif n_type == "list":
            for item in n.get("items", []):
                inline_file_images(item.get("content", []))
                for child in item.get("children", []):
                    inline_file_images([child])
        elif n_type == "table":
            for cell in n.get("header", []):
                inline_file_images(cell)
            for row in n.get("rows", []):
                for cell in row:
                    inline_file_images(cell)


def render_blocks(nodes: List[Dict[str, Any]]) -> List[str]:
    body: List[str] = []

    for n in nodes:
        t = n["type"]

        if t == "heading":
            lvl = min(n["level"] + 1, 6)
            body.append(f"<h{lvl}>{render_inline(n['content'])}</h{lvl}>")

        elif t == "paragraph":
            extra_class = " class=\"tight-after\"" if n.get("tight_after") else ""
            body.append(f"<p{extra_class}>{render_inline(n['content'])}</p>")

        elif t == "blockquote":
            if "children" in n:
                inner = "\n".join(render_blocks(n["children"]))
                body.append(f"<blockquote>{inner}</blockquote>")
            else:
                body.append(f"<blockquote>{render_inline(n['content'])}</blockquote>")

        elif t == "callout":
            title_html = render_inline(n.get("title", []))
            color = n.get("color", "").strip()
            classes = ["md-alert"]
            if color:
                color_key = color.strip().lower()
                color_map = {
                    "info": "md-alert-info",
                    "note": "md-alert-note",
                    "tip": "md-alert-tip",
                    "warning": "md-alert-warning",
                    "danger": "md-alert-danger",
                    "important": "md-alert-important",
                    "caution": "md-alert-caution",
                }
                if color_key in color_map:
                    classes.append(color_map[color_key])
            style = ""
            if color and len(classes) == 1:
                style = f' style="--callout-color: {esc(color)};"'
            inner = ""
            if n.get("children"):
                inner = "\n".join(render_blocks(n["children"]))
            body.append(
                f"<div class=\"{' '.join(classes)}\"{style}>"
                f"<p><strong>{title_html}</strong></p>"
                f"{inner}</div>"
            )

        elif t == "list":
            body.append(render_list_items(n["items"], n.get("list_type", "unordered")))

        elif t == "table":
            head = "".join(f"<th>{render_inline(c)}</th>" for c in n["header"])
            rows = []
            for r in n["rows"]:
                rows.append("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>")
            body.append(f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>")

        elif t == "code_block":
            lang = n.get("language")
            lang_attr = f' lang="{esc(lang)}"' if lang else ""
            body.append(f"<pre class=\"md-fences\"{lang_attr}><code>{esc(n['content'])}</code></pre>")

        elif t == "math_block":
            # Use MathJax default display delimiters and keep TeX unescaped.
            body.append(f"<div class='math'>\\[{n['content']}\\]</div>")

        elif t == "diagram":
            body.append(f"<pre class='mermaid'>{esc(n['content'])}</pre>")

        elif t == "hr":
            body.append("<hr>")

    return body


def render_html(
    ast: Dict[str, Any],
    css: Optional[str] = None,
    inline_local_images: bool = False,
) -> str:
    log_step("Rendering HTML...")
    meta = ast.get("meta") or {}
    author = meta.get("author")
    date = meta.get("date")
    tags = meta.get("tags") or []
    resolve_local_images(ast.get("children", []), meta.get("base_dir"))
    if inline_local_images:
        inline_file_images(ast.get("children", []))

    body = [f"<h1>{esc(ast['title'])}</h1>"]
    meta_parts = [p for p in (author, date) if p]
    if meta_parts:
        body.append(f"<i class=\"doc-meta\">{esc(' · '.join(meta_parts))}</i>")
    body.extend(render_blocks(ast["children"]))

    css_block = f"<style>{css}</style>" if css else ""

    doc_title = ast.get("title") or "OpenMarkdown1.3"
    meta_author = author if author else "Salmomini"
    meta_author_tag = f'<meta name="author" content="{esc(meta_author)}">'
    meta_date_tag = f'<meta name="date" content="{esc(date)}">' if date else ""
    meta_keywords_tag = (
        f'<meta name="keywords" content="{esc(", ".join(tags))}">' if tags else ""
    )

    html_out = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{esc(doc_title)}</title>
{meta_author_tag}
{meta_date_tag}
{meta_keywords_tag}
<meta name="generator" content="OpenMarkdown1.3 \u2013 By Salmomini">

<!-- MathJax -->
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<!-- Mermaid -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{ startOnLoad: true }});</script>

{css_block}
</head>
<body>
<div id="write">
{chr(10).join(body)}
</div>
</body>
</html>
"""
    log_step("HTML rendering complete.")

    return html_out


# ---------------------------
# Chromium PDF export
# ---------------------------
def export_pdf(
    html_content: str,
    out_path: str,
    meta: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
) -> None:
    from playwright.sync_api import sync_playwright
    def pdf_date_from_eu(date_str: str) -> Optional[str]:
        try:
            day_str, month_str, year_str = date_str.split(".")
            day = int(day_str)
            month = int(month_str)
            year = int(year_str)
        except (ValueError, AttributeError):
            return None
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return None
        return f"D:{year:04d}{month:02d}{day:02d}000000Z"

    def set_pdf_metadata(
        pdf_path: str,
        meta: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> None:
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except Exception:
            print(
                "Warning: PyPDF2 not installed; skipping PDF metadata update.",
                file=sys.stderr,
            )
            return

        meta_title = title or "OpenMarkdown1.3 \u2013 By Salmomini"
        meta = meta or {}
        meta_author = meta.get("author") or "Salmomini"
        meta_date = meta.get("date")
        meta_tags = meta.get("tags") or []
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        meta_dict = {
            "/Title": meta_title,
            "/Author": meta_author,
        }
        creator = meta.get("creator")
        subject = meta.get("subject")
        if creator:
            meta_dict["/Creator"] = creator
        if subject:
            meta_dict["/Subject"] = subject
        meta_dict["/Producer"] = (
            "Made using OpenMarkdown \u2013 by Leon D. | "
            "Check it out on GitHub! https://github.com/Salmomini/OpenMarkdown"
        )
        if meta_tags:
            meta_dict["/Keywords"] = ", ".join(meta_tags)
        pdf_date = pdf_date_from_eu(meta_date) if meta_date else None
        if pdf_date:
            meta_dict["/CreationDate"] = pdf_date
        writer.add_metadata(meta_dict)

        out_dir = os.path.dirname(pdf_path)
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, dir=out_dir if out_dir else None
        ) as tmp:
            writer.write(tmp)
            tmp_path = tmp.name
        shutil.move(tmp_path, pdf_path)

    with sync_playwright() as p:
        log_step("Playwright initialized.")
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.wait_for_load_state("networkidle")
        try:
            page.evaluate("() => (window.MathJax ? MathJax.typesetPromise() : null)")
        except Exception:
            pass
        log_step("Rendering PDF...")
        page.pdf(
            path=out_path,
            format="A4",
            print_background=True,
            margin={"top": "0.75in", "right": "0.75in", "bottom": "0.75in", "left": "0.75in"},
        )
        browser.close()
        set_pdf_metadata(out_path, meta=meta, title=title)
        log_step("PDF export complete.")


# ---------------------------
# CLI
# ---------------------------
def usage() -> None:
    print(
        "Usage:\n"
        "  python3 render.py ast.json --html out.html [--css style.example.css]\n"
        "  python3 render.py ast.json --pdf out.pdf   [--css style.example.css]"
    )


if __name__ == "__main__":
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)

    ast_path = sys.argv[1]
    mode = sys.argv[2]
    out_path = sys.argv[3]

    css_text: Optional[str] = None

    if "--css" in sys.argv:
        css_idx = sys.argv.index("--css")
        if css_idx + 1 >= len(sys.argv):
            print("Error: --css requires a file path")
            sys.exit(1)
        with open(sys.argv[css_idx + 1], "r", encoding="utf-8") as f:
            css_text = f.read()

    with open(ast_path, "r", encoding="utf-8") as f:
        ast = json.load(f)

    html_out = render_html(ast, css=css_text, inline_local_images=(mode == "--pdf"))

    if mode == "--html":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"Wrote HTML: {out_path}")

    elif mode == "--pdf":
        export_pdf(html_out, out_path, meta=ast.get("meta"), title=ast.get("title"))
        print(f"Wrote PDF: {out_path}")

    else:
        usage()
        sys.exit(1)
