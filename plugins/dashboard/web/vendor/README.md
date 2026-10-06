# Vendored Dashboard assets

These files are pinned copies of the third-party scripts the Dashboard loads.
`plugins/dashboard/web/index.html` requests the local copy first and only falls
back to the same pinned CDN version when a file is missing, so a deployment
that keeps these files makes no CDN request at all.

| File | Version | Source | SHA-256 |
|------|---------|--------|---------|
| `tailwindcss.js` | Tailwind Play CDN 3.4.17 | <https://cdn.tailwindcss.com/3.4.17> | `176e894661aa9cdc9a5cba6c720044cbbf7b8bd80d1c9a142a7c24b1b6c50d15` |
| `vue.global.prod.js` | Vue 3.5.13 | <https://unpkg.com/vue@3.5.13/dist/vue.global.prod.js> | `c459ba7cc8db65c982589fa5d64c7ff478877e8e5b0fd75683207cec6a4e89e8` |
| `vue-router.global.prod.js` | Vue Router 4.5.0 | <https://unpkg.com/vue-router@4.5.0/dist/vue-router.global.prod.js> | `a2755cf2acf83df38132e204cd21ade913a216658014a631716d795e9ea49c83` |

Licences: Vue and Vue Router are MIT licensed; the Tailwind Play CDN build is
MIT licensed. Files are stored unmodified.

Refresh or verify them with:

```bash
uv run python scripts/vendor_dashboard_assets.py          # download what is missing
uv run python scripts/vendor_dashboard_assets.py --check  # report status, never touches the network
```

The script prints the SHA-256 of every file it writes; the hashes above are the
committed copies. `cdn.tailwindcss.com` answers 403 to the default Python
user agent, so the script sends an explicit `User-Agent` header.
