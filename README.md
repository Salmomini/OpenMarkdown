<p align="left">
  <img src=".readme_assets/logo-light.png#gh-light-mode-only" alt="OpenMarkdown logo" width="600">
  <img src=".readme_assets/logo-dark.png#gh-dark-mode-only" alt="OpenMarkdown logo" width="600">
</p>

**OpenMarkdown** — the Markdown we were promised.  
*A versioned Markdown standard for fast, stable document writing.*

---

Tired of juggling five different Markdown flavors?  
And every time you send someone a document, having to explain:

> “It’s GitHub-flavored Markdown with LaTeX and Mermaid support, plus some inline HTML…”

Yeah. Same.

That frustration is exactly why I built **OpenMarkdown**.  
*(If something has annoyed you about Markdown, it has probably annoyed me too.)*

I’m a student, and I love Markdown because it lets me write **fast** and stay
focused on the content instead of formatting.  
But over time, the cracks became impossible to ignore:
different flavors, unclear rules, broken rendering, and the constant question:

**“Will this even work on their machine?”**

Writing was fast — but trusting the result wasn’t.

So I decided to fix that.



## What is OpenMarkdown?

OpenMarkdown is a **versioned Markdown specification** designed for  
**fast writing and long-term stability**.

Each version defines:
- **one single, official syntax**
- **one authoritative reference parser**
- **deterministic, stable rendering**

No flavors.  
No guesswork.  
No “works on my machine.”

> **TL;DR:**  
> *If your document works today, it will work forever.*

Documents explicitly declare the OpenMarkdown version they target.  
Once a version is released, its syntax and parser are **frozen**. A file written
for v1.2 will always be parsed by a v1.2-compatible engine and render the same way on
every machine — now and in the future.

This means you can write quickly **without worrying** whether your document will
break, change meaning, or render differently later.

---

## What OpenMarkdown is (and isn’t)

**OpenMarkdown is:**
- A single, versioned Markdown standard
- Optimized for **fast, distraction-free writing**
- Deterministic and reproducible
- Very stable by design

**OpenMarkdown is not:**
- Another Markdown flavor
- A renderer lottery
- A “best practices” document

The goal is simple: make Markdown reliable enough for documents you actually care
about — notes, specs, papers, and archives — while keeping the speed that made
Markdown great in the first place.



> **Don’t believe me?**  
> Try it yourself.

## How to use it

### Quickstart

1. Pick a version (preferrably the latest version)
2. Open its folder
3. Install dependencies from `requirements.txt`
4. Run `main.py`

### Repository structure

- `main.py` — Helper script for rendering files
- `parser.py` — Parses `.omd` files into an AST
- `render.py` — Renders output (PDF / HTML) from `ast.json`



## License

The OpenMarkdown reference implementation is licensed under the MIT License.

The name “OpenMarkdown” and compatibility claims are governed by the  
[Trademark & Naming Policy](TRADEMARK.md).

<p align="center">
  <img src="./.readme_assets/platformer.png" alt="Platformer" width="96" />
</p>
