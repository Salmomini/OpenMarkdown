#!/usr/bin/env python3

import os
import sys
from typing import Optional

from parser import OpenMarkdownError, parse_openmarkdown_v1
from render import render_html, export_pdf
from log_utils import set_steps

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI


GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_error(message: str) -> str:
    return f"\033[31m{message}\033[0m"


def prompt_path(label: str, default: Optional[str] = None) -> str:
    session = PromptSession()
    value = session.prompt(
        f"{label}: ",
        default=default or "",
        completer=PathCompleter(expanduser=True),
    ).strip()

    if os.path.isfile(value):
        print(f"{GREEN}Found:{RESET} {value}")
    else:
        print(format_error(f"Not found: {value}"))

    return value


def prompt_optional_path(label: str, default: Optional[str] = None) -> Optional[str]:
    session = PromptSession()
    value = session.prompt(
        f"{label}: ",
        default=default or "",
        completer=PathCompleter(expanduser=True),
    ).strip()

    if not value:
        return None

    if not os.path.isfile(value):
        print(format_error(f"Error: file not found: {value}"))
        sys.exit(1)

    print(f"{GREEN}Found:{RESET} {value}")
    return value


def choose_export_format(default: str = "html") -> str:
    options = ["html", "pdf"]
    index = options.index(default)

    kb = KeyBindings()

    def render() -> ANSI:
        parts = []
        for i, opt in enumerate(options):
            if i == index:
                parts.append(f"\033[7m {opt} \033[0m")  # reverse video
            else:
                parts.append(f" {DIM}{opt}{RESET} ")
        return ANSI("Export format: " + " | ".join(parts))

    @kb.add("left")
    @kb.add("up")
    def _(event):
        nonlocal index
        index = (index - 1) % len(options)
        event.app.invalidate()

    @kb.add("right")
    @kb.add("down")
    def _(event):
        nonlocal index
        index = (index + 1) % len(options)
        event.app.invalidate()

    @kb.add("enter")
    def _(event):
        event.app.exit(result=options[index])

    session = PromptSession(key_bindings=kb)
    return session.prompt(render)


def main() -> int:
    print("OpenMarkdown v1.3")
    print("Minimal renderer")
    print("-----------------")

    md_path = prompt_path("OpenMarkdown file", "example.omd")
    if not os.path.isfile(md_path):
        print(format_error(f"Error: file not found: {md_path}"), file=sys.stderr)
        return 1

    css_path = prompt_optional_path("CSS file (optional)", "style.example.css")
    css_text = None
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css_text = f.read()

    mode = choose_export_format("html")

    session = PromptSession()
    out_path = session.prompt(
        "Output file: ",
        default=f"out.{mode}",
        completer=PathCompleter(expanduser=True),
    ).strip()

    steps = [
        "Parsing your file...",
        "AST constructed.",
        "Rendering HTML...",
        "HTML rendering complete.",
    ]
    if mode == "pdf":
        steps.extend([
            "Playwright initialized.",
            "Rendering PDF...",
            "PDF export complete.",
        ])
    set_steps(steps)

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            ast = parse_openmarkdown_v1(f.read(), source_path=md_path)
    except OpenMarkdownError as exc:
        print(format_error(f"Parse error: {exc}"), file=sys.stderr)
        return 1

    html_out = render_html(
        ast,
        css=css_text,
        inline_local_images=(mode == "pdf"),
    )

    if mode == "html":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"Wrote HTML: {out_path}")
        return 0

    export_pdf(
        html_out,
        out_path,
        meta=ast.get("meta"),
        title=ast.get("title"),
    )
    print(f"Wrote PDF: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
