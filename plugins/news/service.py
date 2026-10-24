"""Bounded news generation with local evidence checks and draft repair."""

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
                if getattr(self.editor, "research_agent", False):
                    articles, payload = await self.editor.research_and_edit(edition)
                    if len(articles) < self.cfg.min_stories:
                        raise InsufficientEvidence(
                            f"insufficient agent evidence: eligible={len(articles)}/{self.cfg.min_stories}; "
                            f"window={edition.start.isoformat()}..{edition.scheduled_at.isoformat()}"
                        )
                    payload = await self._edited_payload(edition, articles, initial_payload=payload)
                else:
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

    async def _edited_payload(self, edition, articles, *, initial_payload=None):
        """Count the Agent draft toward the same bounded, evidence-preserving retries."""
        last = None
        for attempt in range(self.cfg.max_generation_attempts):
            try:
                if attempt == 0 and initial_payload is not None:
                    payload = initial_payload
                else:
                    payload = await self.editor.edit(
                        edition, articles, validation_error=str(last) if last else None,
                    )
                validate_evidence(payload, articles)
                if len(payload.stories) < self.cfg.min_stories:
                    raise InsufficientEvidence(
                        f"too few supported stories: {len(payload.stories)}/{self.cfg.min_stories}"
                    )
                return payload
            except (ValueError, InsufficientEvidence) as exc:
                last = exc
        raise last
