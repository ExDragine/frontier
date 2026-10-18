"""Keep local recognition and synthesis from loading models simultaneously."""

import asyncio

speech_inference_lock = asyncio.Lock()
