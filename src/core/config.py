from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application and Azure Service Configuration loaded from environment variables
    with type-safe validation and sane defaults.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Azure AI Search
    azure_search_endpoint: str = Field(
        default="https://localhost.search.windows.net",
        description="Azure AI Search service endpoint URL"
    )
    azure_search_key: str = Field(
        default="",
        description="Azure AI Search query or admin key"
    )
    azure_search_index_name: str = Field(
        default="travel-intelligence-index",
        description="Target index name containing travel documents"
    )
    azure_search_semantic_config: str = Field(
        default="travel-semantic-config",
        description="Semantic ranking configuration name in Azure Search"
    )

    # Azure OpenAI
    azure_openai_endpoint: str = Field(
        default="https://localhost.openai.azure.com/",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_key: str = Field(
        default="",
        description="Azure OpenAI access key"
    )
    azure_openai_deployment: str = Field(
        default="gpt-4o",
        description="Azure OpenAI deployment name for generation (e.g. gpt-4o)"
    )
    azure_openai_api_version: str = Field(
        default="2024-05-01-preview",
        description="Azure OpenAI API version"
    )
    azure_openai_embedding_deployment: str = Field(
        default="text-embedding-3-small",
        description="Azure OpenAI embedding model deployment for vector search"
    )

    # Application Settings
    app_port: int = Field(default=5000)
    app_debug: bool = Field(default=False)
    max_context_chunks: int = Field(default=5)
    min_relevance_score: float = Field(default=0.70)


settings = Settings()
