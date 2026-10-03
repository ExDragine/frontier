"""Single-shot news generation with local evidence checks; delivery is a separate concern."""

import asyncio

from .schemas import eligible, validate_evidence


class GenerationBusy(RuntimeError):
    pass


class InsufficientEvidence(RuntimeError):
    pass


class NewsService:
    def __init__(self, repo, sources, editor, cfg):
        self.repo = repo
        self.sources = sources
        self.editor = editor
        self.cfg = cfg

    async def generate_report(self, edition):
        old = await self.repo.get(edition.report_id)
        if old and old["status"] in {"ready", "degraded"}:
            return old
        token = await self.repo.claim(edition, ttl=self.cfg.generation_timeout + 30)
        if not token:
            raise GenerationBusy(edition.report_id)
        try:
            async with asyncio.timeout(self.cfg.generation_timeout):
                articles = eligible(await self.sources.collect(edition, set()), edition)
                if len(articles) < self.cfg.min_stories:
                    stats = getattr(self.sources, "stats", {})
                    errors = getattr(self.sources, "errors", [])
                    raise InsufficientEvidence(
                        f"insufficient dated evidence: eligible={len(articles)}/{self.cfg.min_stories}; "
                        f"received={stats.get('received', 0)}, undated={stats.get('undated', 0)}, "
                        f"outside_window={stats.get('outside_window', 0)}; "
                        f"window={edition.start.isoformat()}..{edition.scheduled_at.isoformat()}; "
                        f"sources={','.join(errors) or 'ok'}"
                    )
                payload = await self._edited_payload(edition, articles)
                status = "ready" if len(payload.stories) >= self.cfg.target_stories else "degraded"
                await self.repo.complete(edition.report_id, token, status, articles, payload)
            return await self.repo.get(edition.report_id)
        except asyncio.CancelledError:
            await asyncio.shield(self.repo.fail(edition.report_id, token, "cancelled"))
            raise
        except Exception as exc:
            await self.repo.fail(edition.report_id, token, type(exc).__name__)
            raise

    async def _edited_payload(self, edition, articles):
        """Edit with local evidence checks; content rejections retry with a fresh draft."""
        last = None
        for _ in range(self.cfg.max_generation_attempts):
            try:
                payload = await self.editor.edit(edition, articles)
                validate_evidence(payload, articles)
                if len(payload.stories) < self.cfg.min_stories:
                    raise InsufficientEvidence("too few supported stories")
                return payload
            except (ValueError, InsufficientEvidence) as exc:
                last = exc
        raise last
