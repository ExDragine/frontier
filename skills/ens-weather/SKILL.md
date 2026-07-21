---
name: ens-weather
description: Use for ENS weather, ocean, coral bleaching, BAA, multi-location forecasts, and ENS video requests.
---

# ENS weather workflow

Use this workflow whenever the request needs ENS data or refers back to an earlier ENS result.

1. For new data, call `ens_normal(no_video=True)`. Put up to three locations in `queries`; ask the user to narrow a larger list.
2. For a follow-up, comparison, or evaluation of data already shown in chat, delegate to `memory-agent` first. Reuse the translated values in history instead of calling ENS again. Only fetch again when history has no usable result.
3. For video, delegate to `memory-agent` to recover the previous parameters, then call `ens_normal(no_video=False)`.
4. If a place name is unsupported, resolve its longitude and latitude and retry with `lon` and `lat`; do not ask the user to do that conversion.
5. A request prefixed with `vep` uses `ens_professional`. A capability question should point the user to `/vehelp`.

Do not mention the upstream data provider in the final reply. Do not invent absent values or silently substitute a different place.
