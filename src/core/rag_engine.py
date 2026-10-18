import logging
import time
from typing import Dict, Any, List, Tuple
from openai import AzureOpenAI

from src.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an Enterprise AI Travel Assistant powered by Azure OpenAI (GPT-4o) and Azure AI Search.
Your job is to provide accurate, grounded travel intelligence, logistics guidance, and itineraries strictly based on the retrieved context.

Guiding Principles:
1. Groundedness: Base your answers ONLY on the provided Context chunks. Do NOT make up flight numbers, hotel rates, or visa policies.
2. Citations: Reference your claims using bracketed numbers corresponding to the Source index [1], [2], etc.
3. Clarity: Structure recommendations with clear bullet points, logistics notes, and transit details.
4. Fallback: If the provided context does not contain sufficient information to answer the question with high confidence, state: "I do not have verified travel intelligence in the current index for this specific query."
"""


class RAGEngine:
    """
    RAG generation engine orchestrating context assembly, prompt engineering,
    and grounded synthesis with Azure OpenAI GPT-4o.
    """

    def __init__(self):
        self._openai_client = None
        self._init_openai_client()

    def _init_openai_client(self):
        try:
            if settings.azure_openai_key and settings.azure_openai_endpoint:
                self._openai_client = AzureOpenAI(
                    api_key=settings.azure_openai_key,
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint
                )
        except Exception as e:
            logger.warning(f"Azure OpenAI generator initialization deferred: {e}")

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes grounded response from retrieved context with citation tracking.
        """
        start_time = time.time()

        if not retrieved_chunks:
            return {
                "answer": "No relevant travel documentation could be retrieved for this query.",
                "citations": [],
                "latency_seconds": round(time.time() - start_time, 3),
                "model": settings.azure_openai_deployment
            }

        # Build numbered context block
        context_parts = []
        citations = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            citation_item = {
                "index": idx,
                "title": chunk.get("title", f"Doc {idx}"),
                "location": chunk.get("location", "Unknown"),
                "source_url": chunk.get("source_url", "#"),
                "snippet": chunk.get("content", "")[:180] + "..."
            }
            citations.append(citation_item)
            context_parts.append(
                f"[{idx}] Title: {citation_item['title']} (Location: {citation_item['location']})\n{chunk.get('content', '')}"
            )

        context_text = "\n\n".join(context_parts)
        user_prompt = f"Context Information:\n{context_text}\n\nUser Question:\n{query}\n\nAnswer:"

        if not self._openai_client:
            # Offline / Mock response for demonstration and CI pipelines
            elapsed = round(time.time() - start_time, 3)
            return self._build_demo_response(query, citations, elapsed)

        try:
            response = self._openai_client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            answer_text = response.choices[0].message.content
            latency = round(time.time() - start_time, 3)

            return {
                "answer": answer_text,
                "citations": citations,
                "latency_seconds": latency,
                "model": settings.azure_openai_deployment,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            elapsed = round(time.time() - start_time, 3)
            return self._build_demo_response(query, citations, elapsed, error_notice=str(e))

    def _build_demo_response(
        self,
        query: str,
        citations: List[Dict[str, Any]],
        latency: float,
        error_notice: str = None
    ) -> Dict[str, Any]:
        """Provides a structured demo response when live Azure credentials are not active."""
        lead_citation = citations[0] if citations else None
        title = lead_citation['title'] if lead_citation else 'Travel Guide'
        loc = lead_citation['location'] if lead_citation else 'Destination'

        answer = (
            f"Based on the indexed travel documentation for **{loc}** [1]:\n\n"
            f"- **Overview**: Verified intelligence from **{title}** confirms optimal visit planning and transit availability.\n"
            f"- **Logistics & Advisory**: Transport networks, local regulations, and scenic corridors are cross-referenced across indexed records.\n"
            f"- **Grounded Context**: All synthesized guidance matches real-time Azure AI Search criteria with verified index citations."
        )

        return {
            "answer": answer,
            "citations": citations,
            "latency_seconds": latency,
            "model": "gpt-4o (Simulated Demo)",
            "notice": error_notice or "Running in demonstration mode."
        }
