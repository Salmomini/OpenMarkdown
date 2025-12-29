# OpenMarkdown v1.1
*by salmomini*

OpenMarkdown v1.1 is a small Markdown-like format with a required header and a
focused set of blocks and inline syntax. This README lists every supported
syntax rule implemented by the parser in `parser.py`.

## File format requirements
- Files must start with a YAML-style header delimited by `---` lines.
- The header must include `OpenMarkdown-Version: 1.1`.
- After the header, the document must include a title line using `#* `.
- If the header or title is missing, parsing fails.

Example header + title:
```
---
OpenMarkdown-Version: 1.1
---
#* Document Title
```

## Block syntax
### Headings
- `#` through `######` followed by a space.

### Paragraphs
- One or more consecutive non-empty lines.
- Soft line breaks are preserved inside a paragraph.
- Paragraphs only break on a completely blank line.
- A fenced code block starting on the next line ends the paragraph even if
  there is no blank line.

### Horizontal rules
- A line that is exactly `---`, `***`, or `___` (3 or more of the same char).

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
- Unordered lists only, using `- `.
- Task lists use `- [ ] ` or `- [x] `.

### Tables
- Pipe-delimited header row.
- A separator row using `---`, `:---`, `---:`, or `:---:` per column.
- Subsequent pipe rows are table body rows.

### Code blocks
- Triple backtick fences.
- Optional info string after opening fence.
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

- Inline math: `$...$`
- Images: `![alt](url)` or `![alt](url){60%}` to set width as a percent of
  the content width.
- Links: `[text](url)`
- Inline code: use one or more backticks (e.g. `` `code` ``).
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

## Known limitations
- Only unordered lists are supported.
- Nested lists are not supported.
- Tables require a header + separator row.
- Blockquotes and callouts do not support lazy continuation lines.

## CLI usage

Simple:
```bash
python3 main.py
```

Parse:
```bash
python3 parser.py example.md
python3 parser.py example.md > ast.json # Add it to the file
```

Render:
```bash
python3 render.py ast.json --html out.html [--css style.css]
python3 render.py ast.json --pdf out.pdf   [--css style.css]
```
