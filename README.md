<p align="left">
  <img src=".readme_assets/logo-light.png#gh-light-mode-only" alt="OpenMarkdown logo" width="600">
  <img src=".readme_assets/logo-dark.png#gh-dark-mode-only" alt="OpenMarkdown logo" width="600">
</p>

**OpenMarkdown:** the Markdown we were promised.

---

Tired of having to juggle five different Markdown flavors?  
And every time you send someone a document, you have to add:

> “Here is my file — it’s GitHub-flavored Markdown with LaTeX and Mermaid support, including inline HTML5!”

Yeah. Same.

That frustration is exactly why I made **OpenMarkdown**.  
*(Trust me — if something has annoyed you about Markdown, it has probably annoyed me too.)*

I’m a student, and I *love* Markdown for writing fast and efficiently.  
But over time, more and more things started to *seriously* annoy me:
different flavors, unclear rules, broken rendering, and the constant question of  
*“Will this even work on their machine?”*

So I built **OpenMarkdown** to fix that.

OpenMarkdown is versioned.  
Each version has **one single, official syntax** and **one authoritative parser**.
No flavors. No guesswork. No surprises. (Except you asking yourself why you didn’t find this earlier 👍)

**TL;DR:**  
*If your file works today, it will work forever.*

Each version defines a fixed set of features and parsing rules. Once released,
a version’s parser remains **stable, deterministic, and unchanged**. Documents
explicitly declare the version they target, ensuring that a file written for v1
is always parsed by a v1-compatible engine and renders the same way on every
machine, now and in the future.

The goal of OpenMarkdown is to make Markdown more stable and standardized within
a single, versioned specification and an authoritative reference parser.


---

> **Don’t believe me?**  
> Try it yourself.

---

## How to use it

### Simple quickstart

1. Pick a version 
2. Open it's folder
3. Install the dependencies from the requirements.txt file
4. Run `main.py`

### Which file does what?

- `main.py` – Simple script that makes makes rendering a file easier
- `parser.py` – Parses the .omd
- `render.py` – Makes a PDF/HTML from the ast.json ->  Final product!

---
## License

The OpenMarkdown reference implementation is licensed under the MIT License.

The name “OpenMarkdown” and compatibility claims are governed by the
[Trademark & Naming Policy](TRADEMARK.md).

<p align="center">
  <img src="./.readme_assets/platformer.png" alt="Platformer" width="96" />
</p>
