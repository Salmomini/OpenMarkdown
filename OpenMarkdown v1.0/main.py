#!/usr/bin/env python3

import os
import sys
from typing import Optional

from parser import parse_openmarkdown_v1
from render import render_html, export_pdf


def prompt(label: str, default: Optional[str] = None) -> str:
    if default:
        value = input(f"{label} [{default}]: ").strip()
        return value or default
    return input(f"{label}: ").strip()


def main() -> int:
    print("OpenMarkdown v1.0")
    print("Minimal renderer")
    print("-----------------")

    md_path = prompt("OpenMarkdown file", "example.omd")
    if not os.path.isfile(md_path):
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        return 1

    css_path = prompt("CSS file (optional)", "style.example.css")
    css_text = None
    if css_path:
        if not os.path.isfile(css_path):
            print(f"Error: CSS file not found: {css_path}", file=sys.stderr)
            return 1
        with open(css_path, "r", encoding="utf-8") as f:
            css_text = f.read()

    mode = prompt("Export format (html/pdf)", "html").lower()
    if mode not in {"html", "pdf"}:
        print("Error: format must be 'html' or 'pdf'", file=sys.stderr)
        return 1

    out_path = prompt("Output file", f"out.{mode}")

    with open(md_path, "r", encoding="utf-8") as f:
        ast = parse_openmarkdown_v1(f.read())

    html_out = render_html(ast, css=css_text)

    if mode == "html":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"Wrote HTML: {out_path}")
        return 0

    export_pdf(html_out, out_path)
    print(f"Wrote PDF: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
