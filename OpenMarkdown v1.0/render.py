# render.py

import sys
import json
import html
import os
import shutil
import tempfile
from typing import Dict, Any, List, Optional


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
            out.append(f'<img src="{esc(n["url"])}" alt="{alt}">')
        elif t == "math_inline":
            # Use MathJax default delimiters and keep TeX unescaped.
            out.append(f'<span class="math">\\({n["content"]}\\)</span>')
        elif t == "linebreak":
            out.append("<br>")

    return "".join(out)


# ---------------------------
# Block renderer
# ---------------------------
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
            style = f' style="--callout-color: {esc(color)};"' if color else ""
            inner = ""
            if n.get("children"):
                inner = "\n".join(render_blocks(n["children"]))
                inner = f"<div class=\"callout-body\">{inner}</div>"
            body.append(
                f"<div class=\"callout\"{style}>"
                f"<div class=\"callout-title\">{title_html}</div>"
                f"{inner}</div>"
            )

        elif t == "list":
            items = []
            for it in n["items"]:
                if it["checkbox"] is True or it["checkbox"] is False:
                    checked = " checked" if it["checkbox"] else ""
                    items.append(
                        "<li class=\"task-list-item\">"
                        f"<input type=\"checkbox\" disabled{checked}> "
                        f"{render_inline(it['content'])}"
                        "</li>"
                    )
                else:
                    items.append(f"<li>{render_inline(it['content'])}</li>")
            body.append(f"<ul>{''.join(items)}</ul>")

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


def render_html(ast: Dict[str, Any], css: Optional[str] = None) -> str:
    body = [f"<h1>{esc(ast['title'])}</h1>"]
    body.extend(render_blocks(ast["children"]))

    css_block = f"<style>{css}</style>" if css else ""

    doc_title = "OpenMarkdown1.0 \u2013 By Salmomini"

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{esc(doc_title)}</title>
<meta name="author" content="Salmomini">
<meta name="generator" content="OpenMarkdown1.0 \u2013 By Salmomini">

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


# ---------------------------
# Chromium PDF export
# ---------------------------
def export_pdf(html_content: str, out_path: str) -> None:
    from playwright.sync_api import sync_playwright

    def set_pdf_metadata(pdf_path: str) -> None:
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except Exception:
            print(
                "Warning: PyPDF2 not installed; skipping PDF metadata update.",
                file=sys.stderr,
            )
            return

        meta_title = "OpenMarkdown1.0 \u2013 By Salmomini"
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata(
            {
                "/Title": meta_title,
                "/Author": "Salmomini",
                "/Creator": "",
                "/Producer": "",
                "/Subject": "",
            }
        )

        out_dir = os.path.dirname(pdf_path)
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, dir=out_dir if out_dir else None
        ) as tmp:
            writer.write(tmp)
            tmp_path = tmp.name
        shutil.move(tmp_path, pdf_path)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.wait_for_load_state("networkidle")
        try:
            page.evaluate("() => (window.MathJax ? MathJax.typesetPromise() : null)")
        except Exception:
            pass
        page.pdf(
            path=out_path,
            format="A4",
            print_background=True,
            margin={"top": "0.75in", "right": "0.75in", "bottom": "0.75in", "left": "0.75in"},
        )
        browser.close()
        set_pdf_metadata(out_path)


# ---------------------------
# CLI
# ---------------------------
def usage() -> None:
    print(
        "Usage:\n"
        "  python3 render.py ast.json --html out.html [--css style.css]\n"
        "  python3 render.py ast.json --pdf out.pdf   [--css style.css]"
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

    html_out = render_html(ast, css=css_text)

    if mode == "--html":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"Wrote HTML: {out_path}")

    elif mode == "--pdf":
        export_pdf(html_out, out_path)
        print(f"Wrote PDF: {out_path}")

    else:
        usage()
        sys.exit(1)
