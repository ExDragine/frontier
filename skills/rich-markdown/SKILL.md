---
name: rich-markdown
description: Use when a reply is clearer as a Mermaid diagram, numeric chart, metric summary, or timeline rendered through Frontier Markdown.
---

# Rich Markdown output

Prefer ordinary Markdown and short text. Use an enhanced fence only when it materially improves readability:

- `mermaid` for processes, architecture, and relationships.
- `chart` for numeric bar, line, or pie charts.
- `stats` for a small group of key metrics.
- `timeline` for ordered events.

The `chart`, `stats`, and `timeline` bodies must be strict JSON: double quotes, no comments, no trailing commas, and no fields outside the renderer contract described in the system rendering rules. Never emit raw HTML, CSS, JavaScript, or a render envelope.

Do not make up missing data merely to complete a visualization. If the data or schema does not fit cleanly, return a normal Markdown table or prose instead.
