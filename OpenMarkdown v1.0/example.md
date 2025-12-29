---
OpenMarkdown-Version: 1.0
---
#* OpenMarkdown v1.0 Example

This file showcases every supported block and inline syntax.
It also demonstrates soft line breaks in paragraphs.

# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6

---

Inline formatting: **bold**, *italic*, ==highlight==, ~strikethrough~, `inline code`, and a [link](https://example.com).
Inline math: $a^2 + b^2 = c^2$.

![Mountains at dusk](https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimages.pexels.com%2Fphotos%2F1526713%2Fpexels-photo-1526713.jpeg%3Fcs%3Dsrgb%26dl%3Dpexels-francesco-ungaro-1526713.jpg%26fm%3Djpg&f=1&nofb=1&ipt=253124065c11a7c3599b7481c89beec4e62608efd1e574c8b3b70444fc0d63ce)

> Blockquote line one.
> Blockquote line two with **bold** and `code`.
> 
> > Nested blockquote.

- Basic list item
- Another item with a [link](https://openmarkdown.example)
- [ ] Task list item unchecked
- [x] Task list item checked

| Column A | Column B | Column C |
| --- | :---: | ---: |
| left | centered | right |
| **bold** | `code` | ==mark== |

```text
Plain code block
Line two
```

```mermaid
graph TD
  A[Start] --> B{Decision}
  B -->|Yes| C[Do thing]
  B -->|No| D[Other thing]
```

$$
E = mc^2
\int_0^1 x^2 dx
$$

$$a^2 + b^2 = c^2$$
