"""Agent orchestration layer — ADK-ready with enterprise extensions.

Designed for Google Agent Development Kit integration. When ADK is configured,
swap `generate` implementation to delegate to ADK agents. MVP uses direct LLM calls.
"""

from karena.config import get_settings


class AgentOrchestrator:
    """Primary orchestrator: intent routing, retrieval delegation, synthesis."""

    async def generate(self, prompt: str, question: str, web_search: bool = False) -> tuple[str, float]:
        settings = get_settings()

        # ── Web search augmentation ───────────────────────────
        if web_search:
            try:
                from karena.search.web_search import get_web_search
                svc = get_web_search()
                web_results = await svc.search(question, max_results=4)
                if web_results:
                    web_context = svc.format_for_llm(web_results, question)
                    prompt = web_context + "\n\nKNOWLEDGE BASE CONTEXT:\n" + prompt
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Web search failed: %s", e)

        if settings.llm_provider == "openai" and settings.openai_api_key:
            return await self._generate_openai(prompt)
        if settings.llm_provider == "google" and settings.google_api_key:
            return await self._generate_google(prompt)

        return self._generate_mock(prompt, question), 0.75

    async def _generate_openai(self, prompt: str) -> tuple[str, float]:
        from openai import AsyncOpenAI

        settings = get_settings()
        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or "https://api.groq.com/openai/v1")
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are Karena AI, an enterprise knowledge assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = response.choices[0].message.content or ""
        return text, 0.85

    async def _generate_google(self, prompt: str) -> tuple[str, float]:
        from google import genai

        settings = get_settings()
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model=settings.google_model,
            contents=prompt,
        )
        return response.text or "", 0.85

    def _generate_mock(self, prompt: str, question: str) -> str:
        context_start = prompt.find("## Retrieved Context")
        context_snippet = ""
        if context_start != -1:
            ctx = prompt[context_start : context_start + 800]
            lines = [line.strip() for line in ctx.split("\n") if line.strip().startswith("-")]
            if lines:
                context_snippet = lines[0][:200]

        if context_snippet:
            return (
                f"Based on the retrieved knowledge for your question about **{question[:80]}**, "
                f"here is a synthesized answer:\n\n"
                f"{context_snippet.replace('- ', '')}\n\n"
                f"*Configure `LLM_PROVIDER=openai` or `google` with API keys for full "
                f"generative synthesis. Retrieval and citation pipeline are active.*"
            )

        return (
            f"I received your question: **{question}**\n\n"
            "No matching documents were found in the knowledge base yet. "
            "Upload documents via the ingestion API (`POST /api/v1/ingest`) to enable "
            "retrieval-augmented answers."
        )

    def classify_intent(self, question: str) -> str:
        q = question.lower()
        if any(w in q for w in ("policy", "compliance", "regulation", "gdpr")):
            return "compliance"
        if any(w in q for w in ("deploy", "kubernetes", "architecture", "api")):
            return "technical"
        if any(w in q for w in ("escalate", "human", "support ticket")):
            return "escalation"
        return "knowledge_search"
