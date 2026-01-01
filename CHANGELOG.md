# Changelog
Detailed changelog based on the README files for each version.

## Version 1.0 *29.12.2025*

- Core file format: `.omd` extension, YAML-style header, `OpenMarkdown-Version: 1.0`, required `#* ` title line.
- Block syntax: headings, paragraphs with soft line breaks, horizontal rules, blockquotes with nested parsing.
- Lists and tables: unordered lists, task lists, pipe tables with header + separator row.
- Blocks for code, math, and diagrams: fenced code blocks, Mermaid fences, and `$$` math blocks.
- Inline syntax: math, links, inline code, bold/italic/highlight/strikethrough.
- CLI: parse to AST and render to HTML/PDF via `parser.py` and `render.py`.
- Known limits: no nested lists, no escaping or nested inline modifiers.

## Version 1.1 *29.12.2025*

- Paragraph rules tightened: blank lines end paragraphs; fenced code blocks terminate paragraphs without a blank line.
- Callout blocks documented (blockquote header with title and color metadata).
- Inline improvements: images with optional `{60%}` width, flexible inline code fences, and escaping with `\`.
- Mermaid support clarified as a fenced code info string.
- Added code block labels for non-`mermaid` info strings.
- Known limits now include lack of lazy continuation lines for blockquotes/callouts.

## Version 1.2 *30.12.2025*

- Nested list support: two spaces per nesting level (no tabs or single spaces).
- Inline rules: markers must open/close on the same line and cannot be empty.
- Error reporting: parser emits clear syntax errors on invalid input.
- Inline code restrictions clarified (no empty/whitespace-only spans; same-line rules).

## Version 1.3 *1.1.2026*

- New header metadata: optional `author`, `date` (EU `D.M.YYYY`), and `tags`; rendered under title and embedded in PDF metadata.
- Ordered lists added with `1. ` and nesting rules.
- Inline parsing change: markers cancel when followed by a space (literal text).
- Inline comments: `<#...#>` stripped before parsing.
- Local image paths: `local:` resolution for renderers and PDF inlining.
- Horizontal rules narrowed to `---` only; code block info strings treated as language labels.
- Better `main.py` – added logs and a minimalistic TUI.
- Metadata is automatically generated for PDFs