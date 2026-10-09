# Message renderer

Frontier renders validated message documents with React 19, TypeScript, Tailwind
CSS 4 and shadcn/ui source components. Vite bundles the browser code and CSS into
`templates/markdown_assets/`. Production remains Python + Playwright; Node.js 24
is only needed when developing or rebuilding these checked-in assets.

## Development

```bash
npm ci --prefix renderer
uv run --locked python scripts/generate_renderer_types.py
npm run build --prefix renderer
uv run --locked python scripts/check_message_renderer.py --output-dir /tmp/frontier-ui
```

The schema generator imports only the pure Python message models. CI checks that
the generated TypeScript types and compiled assets match the sources. The browser
smoke check uses the real production screenshot path at 1000 and 390 pixels,
including charts, formulas, Mermaid, escaped text, colored cards, tables, images,
maps and sandboxed frames. Media fixtures are deterministic; optional live-media
checks exercise actual public sources separately.

## Components and styles

`src/message-ui.tsx` maps the existing `ui` tree to React. Card, Badge, Alert,
Table, Progress and Separator compose the source components under
`src/components/ui/`. These were installed with the shadcn CLI from the official
`shadcn-ui/ui` registry; they are intentionally customized for readable long
images, rather than interactive application screens. Status and card variants
belong in the component definitions, using semantic tokens from `src/theme.css`.
Keep model inputs limited to the existing validated choices, never arbitrary
HTML, class names, JavaScript or styles.

Tailwind utilities do not import Preflight, so they do not reset ordinary Markdown,
KaTeX or Mermaid. `templates/markdown_render.css` owns Markdown typography and
document layouts; `src/theme.css` maps those tokens into Tailwind and supplies a
small reset scoped to the React message. Cards retain their own accent even when
nested. Grid layouts collapse to one column below 600 pixels.

The React root commits synchronously before math, Mermaid and Prism run. ECharts
mounts in a layout effect after its container has real dimensions. Browser readiness
then waits for media decoding and two animation frames before Python captures the
PNG. Rendering errors are recorded and fall back inside the affected message block.

Only Python can supply rendered prose HTML and preloaded PNG data URLs. Maps and
remote pages still pass through the existing bounded, public-address media loader;
an iframe contains only an isolated offline image snapshot. The final document
makes no external requests. The 500-character image delivery threshold is unchanged.
