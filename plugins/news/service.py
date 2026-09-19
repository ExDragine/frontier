"""Resumable news generation; delivery is a separate concern."""

import asyncio

from .schemas import Article, NewsPayload, eligible, validate_evidence


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
        stage = "collect"
        try:
            async with asyncio.timeout(self.cfg.generation_timeout):
                row = await self.repo.get(edition.report_id)
                articles = [Article.model_validate(item) for item in (row["evidence"] or [])]
                if not articles:
                    articles = eligible(await self.sources.collect(edition, set()), edition)
                    if len(articles) < self.cfg.min_stories:
                        raise InsufficientEvidence("insufficient dated evidence")
                    await self.repo.checkpoint(edition.report_id, token, "edit", articles=articles)
                stage = "edit"
                row = await self.repo.get(edition.report_id)
                payload = (
                    NewsPayload.model_validate(row["payload"])
                    if row["payload"]
                    else await self.editor.edit(edition, articles)
                )
                validate_evidence(payload, articles)
                await self.repo.checkpoint(edition.report_id, token, "validate", payload=payload)
                stage = "validate"
                payload = await self.editor.verify(payload, articles)
                if len(payload.stories) < self.cfg.min_stories:
                    raise InsufficientEvidence("too few supported stories")
                status = "ready" if len(payload.stories) >= self.cfg.target_stories else "degraded"
                await self.repo.checkpoint(
                    edition.report_id, token, "complete", payload=payload, status=status
                )
            return await self.repo.get(edition.report_id)
        except asyncio.CancelledError:
            await asyncio.shield(self.repo.fail(edition.report_id, token, f"{stage}:cancelled"))
            raise
        except Exception as exc:
            await self.repo.fail(edition.report_id, token, f"{stage}:{type(exc).__name__}")
            raise
