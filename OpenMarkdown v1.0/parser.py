# parse.py

import re
import sys
import json
from typing import Dict, Any, List, Optional


class OpenMarkdownError(Exception):
    pass


# ---------------------------
# Inline parsing
# ---------------------------
INLINE_PATTERNS = [
    ("image", re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")),
    ("math_inline", re.compile(r"\$(.+?)\$")),
    ("link", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
    ("code", re.compile(r"`(.+?)`")),
    ("bold", re.compile(r"\*\*(.+?)\*\*")),
    ("italic", re.compile(r"\*(.+?)\*")),
    ("highlight", re.compile(r"==(.+?)==")),
    ("strike", re.compile(r"~(.+?)~")),
]


def parse_inline(text: str) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []

    while text:
        earliest_start = None
        earliest_match = None
        earliest_kind = None

        for kind, pat in INLINE_PATTERNS:
            m = pat.search(text)
            if m and (earliest_start is None or m.start() < earliest_start):
                earliest_start = m.start()
                earliest_match = m
                earliest_kind = kind

        if not earliest_match:
            nodes.append({"type": "text", "value": text})
            break

        if earliest_match.start() > 0:
            nodes.append({"type": "text", "value": text[:earliest_match.start()]})

        if earliest_kind == "image":
            nodes.append({
                "type": "image",
                "alt": earliest_match.group(1),
                "url": earliest_match.group(2).strip()
            })
        elif earliest_kind == "link":
            nodes.append({
                "type": "link",
                "text": earliest_match.group(1),
                "url": earliest_match.group(2).strip()
            })
        elif earliest_kind == "math_inline":
            nodes.append({
                "type": "math_inline",
                "content": earliest_match.group(1)
            })
        else:
            nodes.append({
                "type": earliest_kind,
                "value": earliest_match.group(1)
            })

        text = text[earliest_match.end():]

    return nodes


# ---------------------------
# Table helpers
# ---------------------------
def is_table_separator(line: str) -> bool:
    cells = [c.strip() for c in line.strip("|").split("|")]
    if len(cells) < 2:
        return False
    return all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def split_table_row(line: str) -> List[str]:
    return [c.strip() for c in line.strip("|").split("|")]


# ---------------------------
# Parser
# ---------------------------
def parse_blocks(lines: List[str], allow_title: bool = False) -> Dict[str, Any]:
    children: List[Dict[str, Any]] = []
    title: Optional[str] = None
    idx = 0

    while idx < len(lines):
        line = lines[idx]

        if not line.strip():
            idx += 1
            continue

        # Title
        if allow_title and line.startswith("#* "):
            title = line[3:].strip()
            idx += 1
            continue

        # Math block $$ ... $$
        if line.strip() == "$$":
            idx += 1
            math = []
            while idx < len(lines) and lines[idx].strip() != "$$":
                math.append(lines[idx])
                idx += 1
            if idx >= len(lines):
                raise OpenMarkdownError("Unterminated $$ block")
            idx += 1
            children.append({
                "type": "math_block",
                "content": "\n".join(math)
            })
            continue

        m = re.match(r"\$\$(.+?)\$\$", line)
        if m:
            children.append({
                "type": "math_block",
                "content": m.group(1)
            })
            idx += 1
            continue

        # Heading
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if m:
            children.append({
                "type": "heading",
                "level": len(m.group(1)),
                "content": parse_inline(m.group(2))
            })
            idx += 1
            continue

        # Horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line.strip()):
            children.append({"type": "hr"})
            idx += 1
            continue

        # Blockquote
        if line.lstrip().startswith(">"):
            quote_lines = []
            while idx < len(lines) and lines[idx].lstrip().startswith(">"):
                raw = lines[idx].lstrip()[1:]
                quote_lines.append(raw[1:] if raw.startswith(" ") else raw)
                idx += 1
            quote_parsed = parse_blocks(quote_lines, allow_title=False)
            children.append({
                "type": "blockquote",
                "children": quote_parsed["children"]
            })
            continue

        # Table
        if idx + 1 < len(lines) and "|" in line and is_table_separator(lines[idx + 1]):
            header_cells = split_table_row(line)
            idx += 2
            rows = []
            while idx < len(lines) and "|" in lines[idx]:
                rows.append([parse_inline(c) for c in split_table_row(lines[idx])])
                idx += 1
            children.append({
                "type": "table",
                "header": [parse_inline(c) for c in header_cells],
                "rows": rows
            })
            continue

        # List
        if line.lstrip().startswith("- "):
            items = []
            while idx < len(lines) and lines[idx].lstrip().startswith("- "):
                raw = lines[idx].lstrip()[2:].strip()
                checkbox = None
                if raw.startswith("[x] "):
                    checkbox, raw = True, raw[4:]
                elif raw.startswith("[ ] "):
                    checkbox, raw = False, raw[4:]
                items.append({
                    "checkbox": checkbox,
                    "content": parse_inline(raw)
                })
                idx += 1
            children.append({
                "type": "list",
                "items": items
            })
            continue

        # Code / Mermaid
        if line.strip().startswith("```"):
            opening = line.strip()
            ticks = len(opening) - len(opening.lstrip("`"))
            info = opening[ticks:].strip().lower()
            idx += 1
            code = []
            while idx < len(lines) and lines[idx].strip() != "`" * ticks:
                code.append(lines[idx])
                idx += 1
            idx += 1

            if info == "mermaid":
                children.append({
                    "type": "diagram",
                    "language": "mermaid",
                    "content": "\n".join(code)
                })
            else:
                children.append({
                    "type": "code_block",
                    "content": "\n".join(code)
                })
            continue

        # Paragraph (soft line breaks)
        para = [line]
        idx += 1
        while idx < len(lines) and lines[idx].strip():
            para.append(lines[idx])
            idx += 1

        nodes = []
        for i, p in enumerate(para):
            nodes.extend(parse_inline(p))
            if i < len(para) - 1:
                nodes.append({"type": "linebreak"})

        children.append({
            "type": "paragraph",
            "content": nodes
        })

    return {"children": children, "title": title}


def parse_openmarkdown_v1(text: str) -> Dict[str, Any]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    idx = 0

    # --- Header ---
    if not lines or lines[0].strip() != "---":
        raise OpenMarkdownError("Missing YAML header")

    idx += 1
    header = {}

    while idx < len(lines) and lines[idx].strip() != "---":
        if ":" not in lines[idx]:
            raise OpenMarkdownError(f"Invalid header line: {lines[idx]}")
        k, v = lines[idx].split(":", 1)
        header[k.strip()] = v.strip()
        idx += 1

    if header.get("OpenMarkdown-Version") != "1.0":
        raise OpenMarkdownError("Unsupported OpenMarkdownVersion")

    idx += 1

    parsed = parse_blocks(lines[idx:], allow_title=True)
    ast = {
        "type": "document",
        "version": "1.0",
        "title": parsed["title"],
        "children": parsed["children"],
    }

    if not ast["title"]:
        raise OpenMarkdownError("Missing document title")

    return ast


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 parse.py file.md")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        ast = parse_openmarkdown_v1(f.read())

    print(json.dumps(ast, indent=2))
