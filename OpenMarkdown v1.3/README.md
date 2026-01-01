# OpenMarkdown v1.3
*by salmomini*

OpenMarkdown v1.3 is a small Markdown-like format with a required header and a
focused set of blocks and inline syntax, including ordered lists. This README lists every supported
syntax rule implemented by the parser in `parser.py`.

## Recent additions
- Optional header metadata: `author` and `date` (EU `D.M.YYYY`).
- Local image paths using `local:` and PDF inlining.
- Inline markers cancel when followed by a space.
- Inline comments using `<#...#>`.

## File format requirements
- OpenMarkdown files use the `.omd` extension.
- Files must start with a YAML-style header delimited by `---` lines.
- The header must include `OpenMarkdown-Version: 1.3`.
- Optional header fields: `author`, `date` (date format `D.M.YYYY`, e.g. `1.1.2026`), and `tags` (comma-separated).
- Immediately after the header, the document must include a title line using `#* `.
- If the header or title is missing, parsing fails.

Example header + title:
```
---
OpenMarkdown-Version: 1.3
author: Ada Lovelace
date: 1.1.2026
tags: rain, city, umbrellas
---
#* Document Title
```
When `author` or `date` are present, the renderer displays them below the title
as `Author · Date` and includes them in PDF metadata. `tags` are included in PDF
metadata as keywords.

## Block syntax
### Headings
- `#` through `######` followed by a space.

### Paragraphs
- One or more consecutive non-empty lines.
- Soft line breaks are preserved inside a paragraph.
- Paragraphs only break on a completely blank line.
- A fenced code block starting on the next line ends the paragraph even if
  there is no blank line.
Example:
```
1. I'm a paragraph.
2. I'm still in the same paragraph, but with a soft line break.
3.
4. Now, I'm in the next paragraph.
```

### Horizontal rules
- A line that is exactly `---`.

### Blockquotes
- Lines starting with `>` (optional single space after `>`).
- Nested parsing is supported inside the quote.

### Callouts
- Callout blocks start with a blockquote header line:
  - `> [Title]{colour:blue}` or `> [Title]{color:blue}`
- The header title becomes the callout title.
- The color value is free-form and used for the callout accent.
- The following quoted lines become the callout body.

### Lists and task lists
- Unordered lists using `- `.
- Ordered lists using `1. ` (any number is allowed).
- Ordered lists may be nested using indentation rules below.
- Nested lists use two spaces before the list marker per nesting level (no tabs or single spaces).
- Task lists use `- [ ] ` or `- [x] `.

### Tables
- Pipe-delimited header row.
- A separator row using `---`, `:---`, `---:`, or `:---:` per column.
- Subsequent pipe rows are table body rows.

### Code blocks
- Triple backtick fences.
- Optional info string after opening fence (programming lang.).
- Closed by matching number of backticks.
- If the info string is `mermaid`, the block is treated as a diagram.
- Any other info string becomes the code block label.

### Mermaid diagrams
- Use fenced code blocks with the `mermaid` info string.

### Math blocks
- Multiline:
  - A line with `$$`, followed by content, ending with a line with `$$`.
- Single-line:
  - `$$...$$` on one line.

## Inline syntax
Inline parsing runs inside paragraphs, headings, list items, table cells,
and blockquotes.

- Inline markers must open and close on the same line.
- Inline markers cannot be empty (e.g. `****` is invalid).
- Inline markers must not be followed by a space; otherwise they are treated as literal text.
  - Example: `* not italic*` and `** bold**` render as plain text.
- Inline math: `$...$`
- Images: `![alt](url)` or `![alt](local:images/pic.png){60%}` to set width as a percent of
  the content width.
  - `local:` paths are resolved relative to the `.omd` file location when rendering.
  - Local images are inlined for PDF export to ensure they render correctly.
- Links: `[text](url)`
- Inline code: use one or more backticks (e.g. `` `code` ``).
  - Inline syntax must open and close on the same line.
  - Inline syntax cannot be empty or whitespace-only between markers.
  - Use a longer fence to include backticks inside the code span.
  - Newlines inside inline code are normalized to spaces.
  - If the code span starts and ends with a space and is not all spaces, one
    leading and trailing space is trimmed.
- Bold: `**bold**`
- Italic: `*italic*`
- Highlight: `==highlight==`
- Strikethrough: `~strike~`
- Escaping: `\` escapes the next character, preventing inline parsing.
  - Example: `\*not italic*` renders literal asterisks.
- Comments: `<#...#>` are stripped before parsing and never rendered.

## Error reporting
- The parser reports clear syntax errors when it encounters invalid input.

## Known limitations
- Tables require a header + separator row.
- Blockquotes and callouts do not support lazy continuation lines.

## CLI usage

### Simple way:
```bash
python3 main.py
```
---

### More *manual* way

Parse:
```bash
python3 parser.py example.omd
python3 parser.py example.omd > ast.json # Add it to the file
```

Render:
```bash
python3 render.py ast.json --html out.html [--css style.example.css]
python3 render.py ast.json --pdf out.pdf   [--css style.example.css]
```
