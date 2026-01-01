# parse.py

import re
import sys
import json
import os
from typing import Dict, Any, List, Optional

from log_utils import log_step


class OpenMarkdownError(Exception):
    pass


def syntax_error(message: str, line_no: Optional[int] = None) -> OpenMarkdownError:
    if line_no is None:
        return OpenMarkdownError(f"Syntax error: {message}")
    return OpenMarkdownError(f"Syntax error on line {line_no}: {message}")

def strip_comments(text: str) -> str:
    def repl(match: re.Match) -> str:
        return "\n" * match.group(0).count("\n")
    return re.sub(r"<#.*?#>", repl, text, flags=re.S)


# ---------------------------
# Inline parsing
# ---------------------------
INLINE_PATTERNS = [
    ("image", re.compile(r"!\[([^\]]*)\]\(([^)]+)\)(?:\{([0-9]+(?:\.[0-9]+)?)%\})?")),
    ("math_inline", re.compile(r"\$(?!\s)(.+?)\$")),
    ("link", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
    ("bold", re.compile(r"\*\*(?!\s)(.+?)\*\*")),
    ("italic", re.compile(r"\*(?![\s*])(.+?)\*")),
    ("highlight", re.compile(r"==(?!\s)(.+?)==")),
    ("strike", re.compile(r"~(?!\s)(.+?)~")),
]


def find_code_span(text: str) -> Optional[Dict[str, Any]]:
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "`":
            i += 1
            continue
        run_len = 1
        while i + run_len < n and text[i + run_len] == "`":
            run_len += 1
        j = i + run_len
        while j < n:
            if text[j] == "`":
                close_len = 1
                while j + close_len < n and text[j + close_len] == "`":
                    close_len += 1
                if close_len == run_len:
                    content = text[i + run_len:j]
                    if "\n" in content:
                        content = content.replace("\n", " ")
                    if (
                        len(content) >= 2
                        and content.startswith(" ")
                        and content.endswith(" ")
                        and content.strip() != ""
                    ):
                        content = content[1:-1]
                    return {
                        "start": i,
                        "end": j + close_len,
                        "content": content,
                    }
                j += close_len
            else:
                j += 1
        i += run_len
    return None


def is_escaped(text: str, pos: int) -> bool:
    count = 0
    i = pos - 1
    while i >= 0 and text[i] == "\\":
        count += 1
        i -= 1
    return count % 2 == 1


def find_next_unescaped(text: str, token: str, start: int) -> int:
    idx = text.find(token, start)
    while idx != -1 and is_escaped(text, idx):
        idx = text.find(token, idx + 1)
    return idx


def validate_inline_syntax(text: str, line_no: Optional[int]) -> None:
    if line_no is None:
        return
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`" and not is_escaped(text, i):
            run_len = 1
            while i + run_len < n and text[i + run_len] == "`":
                run_len += 1
            token = "`" * run_len
            close_idx = find_next_unescaped(text, token, i + run_len)
            if close_idx == -1:
                raise syntax_error("Unclosed code span", line_no)
            if text[i + run_len:close_idx].strip() == "":
                raise syntax_error("Empty code span", line_no)
            i = close_idx + run_len
            continue
        if text.startswith("**", i) and not is_escaped(text, i):
            if i + 2 < n and text[i + 2].isspace():
                i += 2
                continue
            close_idx = find_next_unescaped(text, "**", i + 2)
            if close_idx == -1:
                raise syntax_error("Unclosed bold", line_no)
            if text[i + 2:close_idx].strip() == "":
                raise syntax_error("Empty bold", line_no)
            i = close_idx + 2
            continue
        if text.startswith("==", i) and not is_escaped(text, i):
            if i + 2 < n and text[i + 2].isspace():
                i += 2
                continue
            close_idx = find_next_unescaped(text, "==", i + 2)
            if close_idx == -1:
                raise syntax_error("Unclosed highlight", line_no)
            if text[i + 2:close_idx].strip() == "":
                raise syntax_error("Empty highlight", line_no)
            i = close_idx + 2
            continue
        if text[i] == "~" and not is_escaped(text, i):
            if i + 1 < n and text[i + 1].isspace():
                i += 1
                continue
            close_idx = find_next_unescaped(text, "~", i + 1)
            if close_idx == -1:
                raise syntax_error("Unclosed strikethrough", line_no)
            if text[i + 1:close_idx].strip() == "":
                raise syntax_error("Empty strikethrough", line_no)
            i = close_idx + 1
            continue
        if text[i] == "*" and not is_escaped(text, i):
            if i + 1 < n and text[i + 1] == "*":
                i += 1
                continue
            if i + 1 < n and text[i + 1].isspace():
                i += 1
                continue
            close_idx = find_next_unescaped(text, "*", i + 1)
            if close_idx == -1:
                raise syntax_error("Unclosed italic", line_no)
            if text[i + 1:close_idx].strip() == "":
                raise syntax_error("Empty italic", line_no)
            i = close_idx + 1
            continue
        if text[i] == "$" and not is_escaped(text, i):
            if i + 1 < n and text[i + 1] == "$":
                i += 2
                continue
            if i + 1 < n and text[i + 1].isspace():
                i += 1
                continue
            close_idx = find_next_unescaped(text, "$", i + 1)
            if close_idx == -1:
                raise syntax_error("Unclosed inline math", line_no)
            if text[i + 1:close_idx].strip() == "":
                raise syntax_error("Empty inline math", line_no)
            i = close_idx + 1
            continue
        i += 1


def parse_inline(text: str, line_no: Optional[int] = None) -> List[Dict[str, Any]]:
    validate_inline_syntax(text, line_no)
    nodes: List[Dict[str, Any]] = []

    while text:
        escape_idx = text.find("\\")
        code_span = find_code_span(text)
        code_start = code_span["start"] if code_span else None
        earliest_start = None
        earliest_match = None
        earliest_kind = None

        for kind, pat in INLINE_PATTERNS:
            m = pat.search(text)
            if m and (earliest_start is None or m.start() < earliest_start):
                earliest_start = m.start()
                earliest_match = m
                earliest_kind = kind

        if (
            escape_idx != -1
            and (earliest_start is None or escape_idx < earliest_start)
            and (code_start is None or escape_idx < code_start)
        ):
            if escape_idx > 0:
                nodes.append({"type": "text", "value": text[:escape_idx]})
            if escape_idx + 1 < len(text):
                nodes.append({"type": "text", "value": text[escape_idx + 1]})
                text = text[escape_idx + 2:]
            else:
                nodes.append({"type": "text", "value": "\\"})
                text = ""
            continue

        if code_span and (earliest_start is None or code_start < earliest_start):
            if code_start > 0:
                nodes.append({"type": "text", "value": text[:code_start]})
            nodes.append({"type": "code", "value": code_span["content"]})
            text = text[code_span["end"]:]
            continue

        if not earliest_match:
            nodes.append({"type": "text", "value": text})
            break

        if earliest_match.start() > 0:
            nodes.append({"type": "text", "value": text[:earliest_match.start()]})

        if earliest_kind == "image":
            nodes.append({
                "type": "image",
                "alt": earliest_match.group(1),
                "url": earliest_match.group(2).strip(),
                "width_percent": (
                    float(earliest_match.group(3))
                    if earliest_match.group(3)
                    else None
                ),
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
# List helpers
# ---------------------------
def parse_list_line(line: str, line_no: Optional[int] = None) -> Optional[Dict[str, Any]]:
    if not line:
        return None
    leading = re.match(r"[ \t]*", line).group(0)
    indent = len(leading)
    stripped = line[indent:]
    list_type = None
    content_start = None
    if stripped.startswith("-"):
        if not stripped.startswith("- "):
            raise syntax_error("List items must use '- '", line_no)
        list_type = "unordered"
        content_start = 2
    else:
        m = re.match(r"(\d+)\.", stripped)
        if m:
            if len(stripped) <= m.end() or stripped[m.end()] != " ":
                raise syntax_error("Ordered list items must use '1. '", line_no)
            list_type = "ordered"
            content_start = m.end() + 1
        else:
            return None
    if "\t" in leading:
        raise syntax_error("List indentation must use spaces only (two spaces per level)", line_no)
    if indent % 2 != 0:
        raise syntax_error("List indentation must use two spaces per level", line_no)
    raw = stripped[content_start:].strip()
    checkbox = None
    if list_type == "unordered":
        if raw.startswith("[x] "):
            checkbox, raw = True, raw[4:]
        elif raw.startswith("[ ] "):
            checkbox, raw = False, raw[4:]
    return {
        "indent": indent,
        "checkbox": checkbox,
        "content": raw,
        "list_type": list_type,
        "line_no": line_no,
    }


def parse_list(
    lines: List[str],
    idx: int,
    base_indent: int,
    start_line: int,
    list_type: str,
) -> (List[Dict[str, Any]], int):
    items = []
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            break
        info = parse_list_line(line, start_line + idx)
        if not info:
            break
        if info["list_type"] != list_type and info["indent"] == base_indent:
            break
        indent = info["indent"]
        if indent < base_indent:
            break
        if indent > base_indent:
            if not items:
                break
            nested_items, idx = parse_list(
                lines,
                idx,
                indent,
                start_line,
                info["list_type"],
            )
            if nested_items:
                items[-1].setdefault("children", []).append({
                    "type": "list",
                    "list_type": info["list_type"],
                    "items": nested_items
                })
            continue
        items.append({
            "checkbox": info["checkbox"],
            "content": parse_inline(info["content"], info["line_no"])
        })
        idx += 1
    return items, idx


# ---------------------------
# Parser
# ---------------------------
def parse_blocks(
    lines: List[str],
    allow_title: bool = False,
    start_line: int = 1,
) -> Dict[str, Any]:
    children: List[Dict[str, Any]] = []
    title: Optional[str] = None
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        line_no = start_line + idx

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
                raise syntax_error("Unterminated $$ block", line_no)
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
                "content": parse_inline(m.group(2), line_no)
            })
            idx += 1
            continue

        # Horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line.strip()):
            children.append({"type": "hr"})
            idx += 1
            continue

        # Blockquote / Callout
        if line.lstrip().startswith(">"):
            quote_lines = []
            while idx < len(lines) and lines[idx].lstrip().startswith(">"):
                raw = lines[idx].lstrip()[1:]
                quote_lines.append(raw[1:] if raw.startswith(" ") else raw)
                idx += 1
            quote_start = line_no
            header = quote_lines[0].strip() if quote_lines else ""
            callout_match = re.match(r"\[([^\]]+)\]\s*\{([^}]+)\}\s*$", header)
            if callout_match:
                meta = callout_match.group(2)
                color_match = re.search(
                    r"(?:^|[;\s])(?:colour|color)\s*:\s*([^;]+)\s*",
                    meta,
                    re.IGNORECASE,
                )
                if color_match:
                    title = callout_match.group(1).strip()
                    color = color_match.group(1).strip()
                    body_lines = quote_lines[1:]
                    if body_lines and not body_lines[0].strip():
                        body_lines = body_lines[1:]
                    body_start = quote_start + 1
                    callout_parsed = parse_blocks(
                        body_lines,
                        allow_title=False,
                        start_line=body_start,
                    )
                    children.append({
                        "type": "callout",
                        "title": parse_inline(title, quote_start),
                        "color": color,
                        "children": callout_parsed["children"],
                    })
                    continue

            quote_parsed = parse_blocks(
                quote_lines,
                allow_title=False,
                start_line=quote_start,
            )
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
                rows.append([
                    parse_inline(c, start_line + idx)
                    for c in split_table_row(lines[idx])
                ])
                idx += 1
            children.append({
                "type": "table",
                "header": [parse_inline(c, line_no) for c in header_cells],
                "rows": rows
            })
            continue

        # List
        list_info = parse_list_line(line, line_no)
        if list_info:
            items, idx = parse_list(
                lines,
                idx,
                list_info["indent"],
                start_line,
                list_info["list_type"],
            )
            children.append({
                "type": "list",
                "list_type": list_info["list_type"],
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
            if idx >= len(lines):
                raise syntax_error("Unterminated code block", line_no)
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
                    "language": info if info else None,
                    "content": "\n".join(code)
                })
            continue

        # Paragraph (soft line breaks)
        para = [line]
        idx += 1
        while idx < len(lines) and lines[idx].strip():
            if lines[idx].strip().startswith("```"):
                break
            para.append(lines[idx])
            idx += 1
        tight_after = idx < len(lines) and lines[idx].strip().startswith("```")

        nodes = []
        for i, p in enumerate(para):
            nodes.extend(parse_inline(p, line_no + i))
            if i < len(para) - 1:
                nodes.append({"type": "linebreak"})

        children.append({
            "type": "paragraph",
            "content": nodes,
            "tight_after": tight_after,
        })

    return {"children": children, "title": title}


def parse_openmarkdown_v1(text: str, source_path: Optional[str] = None) -> Dict[str, Any]:
    log_step("Parsing your file...")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = strip_comments(text)
    lines = text.splitlines()
    idx = 0

    # --- Header ---
    if not lines or lines[0].strip() != "---":
        raise syntax_error("Missing YAML header", 1)

    idx += 1
    header = {}

    while idx < len(lines) and lines[idx].strip() != "---":
        if ":" not in lines[idx]:
            raise syntax_error(f"Invalid header line: {lines[idx]}", idx + 1)
        k, v = lines[idx].split(":", 1)
        header[k.strip()] = v.strip()
        idx += 1

    if header.get("OpenMarkdown-Version") != "1.3":
        raise syntax_error("Unsupported OpenMarkdownVersion")

    author = header.get("author")
    date = header.get("date")
    tags = header.get("tags")
    if author is not None and author.strip() == "":
        raise syntax_error("Header author cannot be empty")
    if date is not None and not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", date):
        raise syntax_error("Header date must use D.M.YYYY format (e.g. 1.1.2026)")
    tag_list = None
    if tags is not None:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if not tag_list:
            raise syntax_error("Header tags cannot be empty")

    idx += 1
    if idx >= len(lines):
        raise syntax_error("Missing document title", idx + 1)

    title_line = lines[idx]
    if not title_line.startswith("#* "):
        raise syntax_error("Document title must be the first line after the header", idx + 1)
    title = title_line[3:].strip()
    idx += 1

    parsed = parse_blocks(lines[idx:], allow_title=False, start_line=idx + 1)
    ast = {
        "type": "document",
        "version": "1.3",
        "title": title,
        "children": parsed["children"],
    }
    meta = {}
    if author is not None:
        meta["author"] = author
    if date is not None:
        meta["date"] = date
    if tag_list is not None:
        meta["tags"] = tag_list
    if source_path:
        meta["base_dir"] = os.path.dirname(os.path.abspath(source_path))
    if meta:
        ast["meta"] = meta

    if not ast["title"]:
        raise syntax_error("Missing document title", idx)

    log_step("AST constructed.")
    return ast


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 parse.py file.omd")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            ast = parse_openmarkdown_v1(f.read(), source_path=sys.argv[1])
        print(json.dumps(ast, indent=2))
    except OpenMarkdownError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        sys.exit(1)
