"""Dynamic prompt engineering with context compression."""

from karena.rag.hybrid_retriever import RetrievedDocument

SYSTEM_INSTRUCTIONS = """You are Karena AI, an enterprise knowledge intelligence assistant.
- Synthesize answers ONLY from the provided context.
- Cite sources using [Source: title] notation.
- If context is insufficient, state what is missing and suggest escalation.
- Maintain compliance: never fabricate regulatory claims.
- Be concise, authoritative, and actionable."""

FEW_SHOT_EXAMPLES = """
Example:
User: What is our data retention policy for APAC customers?
Assistant: Per [Source: APAC Data Governance Policy], customer records are retained for 7 years post-account closure, with encrypted archival after 24 months of inactivity.
"""


class PromptBuilder:
    def build(
        self,
        *,
        question: str,
        context_docs: list[RetrievedDocument],
        history: list[dict],
        max_context_chars: int = 12000,
    ) -> str:
        context_block = self._compress_context(context_docs, max_context_chars)
        history_block = self._format_history(history)

        return f"""{SYSTEM_INSTRUCTIONS}
{FEW_SHOT_EXAMPLES}

## Conversation History
{history_block}

## Retrieved Context
{context_block}

## User Question
{question}

## Instructions
Provide a synthesized answer with source citations. Include a confidence assessment (high/medium/low) at the end.
"""

    def _compress_context(self, docs: list[RetrievedDocument], max_chars: int) -> str:
        lines: list[str] = []
        total = 0
        for doc in docs:
            line = f"- [{doc.source_title}] (score={doc.score:.3f}): {doc.text[:600]}"
            if total + len(line) > max_chars:
                break
            lines.append(line)
            total += len(line)
        return "\n".join(lines) if lines else "(No relevant documents retrieved)"

    def _format_history(self, history: list[dict]) -> str:
        if not history:
            return "(New session)"
        return "\n".join(f"{m['role'].upper()}: {m['content'][:400]}" for m in history[-4:])
