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
                        stats = getattr(self.sources, "stats", {})
                        errors = getattr(self.sources, "errors", [])
                        raise InsufficientEvidence(
                            f"insufficient dated evidence: eligible={len(articles)}/{self.cfg.min_stories}; "
                            f"received={stats.get('received', 0)}, undated={stats.get('undated', 0)}, "
                            f"outside_window={stats.get('outside_window', 0)}; "
                            f"window={edition.start.isoformat()}..{edition.scheduled_at.isoformat()}; "
                            f"sources={','.join(errors) or 'ok'}"
                        )
                    await self.repo.checkpoint(edition.report_id, token, "edit", articles=articles)
                stage = "edit"
                row = await self.repo.get(edition.report_id)
                stage = "edit/validate"
                payload, verified = await self._validated_payload(
                    edition, token, articles, row["payload"]
                )
                status = (
                    "ready"
                    if verified and len(payload.stories) >= self.cfg.target_stories
                    else "degraded"
                )
                await self.repo.checkpoint(
                    edition.report_id, token, "complete", payload=payload, status=status
                )
            return await self.repo.get(edition.report_id)
        except TimeoutError:
            # A draft is checkpointed before the independent verification call. If
            # verification outlives the overall generation budget, publish that
            # evidence-validated draft as degraded instead of losing the edition.
            row = await self.repo.get(edition.report_id)
            if stage == "edit/validate" and row and row["payload"]:
                payload = NewsPayload.model_validate(row["payload"])
                await self.repo.checkpoint(
                    edition.report_id, token, "complete", payload=payload, status="degraded"
                )
                return await self.repo.get(edition.report_id)
            await self.repo.fail(edition.report_id, token, f"{stage}:TimeoutError")
            raise
        except asyncio.CancelledError:
            await asyncio.shield(self.repo.fail(edition.report_id, token, f"{stage}:cancelled"))
            raise
        except Exception as exc:
            await self.repo.fail(edition.report_id, token, f"{stage}:{type(exc).__name__}")
            raise

    async def _validated_payload(self, edition, token, articles, cached_payload):
        for attempt in range(self.cfg.max_generation_attempts):
            try:
                payload = (
                    NewsPayload.model_validate(cached_payload)
                    if cached_payload else await self.editor.edit(edition, articles)
                )
                validate_evidence(payload, articles)
                await self.repo.checkpoint(edition.report_id, token, "validate", payload=payload)
                try:
                    payload = await self.editor.verify(payload, articles)
                    validate_evidence(payload, articles)
                except TimeoutError:
                    # Verification is an extra support pass. The draft has already
                    # passed deterministic evidence checks, so keep it deliverable
                    # when the verifier's provider is slow or temporarily stuck.
                    return payload, False
                if len(payload.stories) < self.cfg.min_stories:
                    raise InsufficientEvidence("too few supported stories")
                return payload, True
            except (ValueError, InsufficientEvidence):
                # Content rejection must not permanently pin a bad draft.
                # Transport errors instead preserve the draft for recovery.
                cached_payload = None
                await self.repo.checkpoint(
                    edition.report_id, token, "edit", clear_payload=True,
                )
                if attempt + 1 == self.cfg.max_generation_attempts:
                    raise
