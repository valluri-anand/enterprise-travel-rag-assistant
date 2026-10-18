import logging
from typing import List, Dict, Any, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

from src.core.config import settings

logger = logging.getLogger(__name__)


class AzureSearchService:
    """
    Production-grade Azure AI Search client supporting Hybrid Search:
    combining dense vector search, BM25 keyword matching, and semantic reranking.
    """

    def __init__(self):
        self._search_client: Optional[SearchClient] = None
        self._openai_client: Optional[AzureOpenAI] = None
        self._init_clients()

    def _init_clients(self):
        try:
            if settings.azure_search_key and settings.azure_search_endpoint:
                credential = AzureKeyCredential(settings.azure_search_key)
                self._search_client = SearchClient(
                    endpoint=settings.azure_search_endpoint,
                    index_name=settings.azure_search_index_name,
                    credential=credential
                )
        except Exception as e:
            logger.warning(f"Azure Search client initialization deferred: {e}")

        try:
            if settings.azure_openai_key and settings.azure_openai_endpoint:
                self._openai_client = AzureOpenAI(
                    api_key=settings.azure_openai_key,
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint
                )
        except Exception as e:
            logger.warning(f"Azure OpenAI embedding client initialization deferred: {e}")

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generates dense vector embeddings using Azure OpenAI."""
        if not self._openai_client:
            return None
        try:
            response = self._openai_client.embeddings.create(
                input=text,
                model=settings.azure_openai_embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search across indexed travel documentation.
        Falls back to mock data if running in offline demo mode.
        """
        if not self._search_client:
            logger.info("Operating in demo/mock mode: Azure Search credentials not configured.")
            return self._get_mock_travel_chunks(query, top_k)

        try:
            vector_queries = []
            if use_hybrid:
                query_vector = self.generate_embedding(query)
                if query_vector:
                    vector_queries.append(
                        VectorizedQuery(
                            vector=query_vector,
                            k_nearest_neighbors=top_k,
                            fields="contentVector"
                        )
                    )

            results = self._search_client.search(
                search_text=query,
                vector_queries=vector_queries if vector_queries else None,
                query_type="semantic" if settings.azure_search_semantic_config else "simple",
                semantic_configuration_name=settings.azure_search_semantic_config or None,
                select=["id", "title", "content", "location", "category", "metadata_storage_path"],
                top=top_k
            )

            formatted_results = []
            for item in results:
                formatted_results.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", "Travel Document"),
                    "content": item.get("content", item.get("chunk", "")),
                    "location": item.get("location", "Global"),
                    "category": item.get("category", "Guide"),
                    "source_url": item.get("metadata_storage_path", "#"),
                    "score": getattr(item, "@search.score", 0.0),
                    "reranker_score": getattr(item, "@search.reranker_score", 0.0)
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Search execution failed: {e}. Falling back to demo data.")
            return self._get_mock_travel_chunks(query, top_k)

    def _get_mock_travel_chunks(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Sample curated travel intelligence chunks for offline demo and CI testing."""
        mock_corpus = [
            {
                "id": "doc-001",
                "title": "Kyoto Cultural & Travel Advisory Guide",
                "content": "Visitors to Kyoto can experience historical temples like Fushimi Inari and Kinkaku-ji. Peak cherry blossom season occurs between late March and early April. JR Pass enables seamless transit from Tokyo via Tokaido Shinkansen in 2 hours 15 minutes.",
                "location": "Kyoto, Japan",
                "category": "Cultural Itinerary",
                "source_url": "https://storage.travelintel.azure.com/kyoto-guide.pdf",
                "score": 0.94,
                "reranker_score": 3.85
            },
            {
                "id": "doc-002",
                "title": "Swiss Alps Hiking & Rail Pass Protocol",
                "content": "The Swiss Travel Pass covers unlimited travel on train, bus, and boat throughout Switzerland, including panoramic routes like Glacier Express. Best hiking conditions in Zermatt and Jungfrau region run from June through September.",
                "location": "Zermatt, Switzerland",
                "category": "Adventure & Transit",
                "source_url": "https://storage.travelintel.azure.com/swiss-alps.pdf",
                "score": 0.91,
                "reranker_score": 3.72
            },
            {
                "id": "doc-003",
                "title": "Iceland Ring Road Safety & Aurora Forecast",
                "content": "Navigating Iceland Route 1 (Ring Road) requires 4WD vehicles during winter months (October to April). Northern lights viewing is optimal between September and March during clear solar activity nights. Always check Vedur.is for real-time wind and avalanche warnings.",
                "location": "Reykjavik, Iceland",
                "category": "Safety & Logistics",
                "source_url": "https://storage.travelintel.azure.com/iceland-advisory.pdf",
                "score": 0.88,
                "reranker_score": 3.60
            }
        ]
        return mock_corpus[:top_k]
