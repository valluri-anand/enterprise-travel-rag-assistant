"""
Azure AI Search Ingestion & Cognitive Skillset Pipeline Definition.
Configures Index Schema, Vector Profile, Semantic Configuration, and Cognitive Skillsets
(OCR, Keyphrase Extraction, Entity Recognition).
"""

from typing import Dict, Any


def get_travel_index_schema(
    index_name: str = "travel-intelligence-index",
    vector_dimensions: int = 1536
) -> Dict[str, Any]:
    """
    Returns the comprehensive Azure AI Search Index Schema supporting:
    - Hybrid Search (Text + Vectors)
    - Semantic Ranking Configuration
    - Cognitive Skillset Enrichment outputs
    """
    return {
        "name": index_name,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "title", "type": "Edm.String", "searchable": True, "filterable": True, "sortable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "location", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
            {"name": "category", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
            {
                "name": "contentVector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "dimensions": vector_dimensions,
                "vectorSearchProfileName": "travel-vector-profile"
            },
            {"name": "metadata_storage_path", "type": "Edm.String", "filterable": True},
            {"name": "extracted_entities", "type": "Collection(Edm.String)", "searchable": True, "facetable": True},
            {"name": "keyphrases", "type": "Collection(Edm.String)", "searchable": True}
        ],
        "vectorSearch": {
            "algorithms": [
                {
                    "name": "hnsw-algorithm",
                    "kind": "hnsw",
                    "parameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }
            ],
            "profiles": [
                {
                    "name": "travel-vector-profile",
                    "algorithm": "hnsw-algorithm"
                }
            ]
        },
        "semantic": {
            "configurations": [
                {
                    "name": "travel-semantic-config",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "contentFields": [{"fieldName": "content"}],
                        "keywordsFields": [{"fieldName": "category"}, {"fieldName": "location"}]
                    }
                }
            ]
        }
    }


def get_cognitive_skillset_definition(skillset_name: str = "travel-cognitive-skillset") -> Dict[str, Any]:
    """
    Defines Cognitive Skillset with OCR, Entity Recognition, and Keyphrase Extraction
    for parsing multi-format unstructured travel documentation (PDFs, Images, Word docs).
    """
    return {
        "name": skillset_name,
        "description": "Multi-modal cognitive skillset for unstructured travel document intelligence",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Vision.OcrSkill",
                "name": "TravelOcrSkill",
                "description": "Extract text and scanned itineraries from images & PDFs",
                "context": "/document/normalized_images/*",
                "defaultLanguageCode": "en",
                "detectOrientation": True,
                "inputs": [{"name": "image", "source": "/document/normalized_images/*"}],
                "outputs": [{"name": "text", "targetName": "ocr_text"}]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.V3.EntityRecognitionSkill",
                "name": "TravelEntityRecognitionSkill",
                "description": "Extract locations, dates, transit points, and organizations",
                "context": "/document",
                "categories": ["Location", "DateTime", "Organization"],
                "defaultLanguageCode": "en",
                "inputs": [{"name": "text", "source": "/document/content"}],
                "outputs": [{"name": "entities", "targetName": "extracted_entities"}]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.KeyPhraseExtractionSkill",
                "name": "TravelKeyPhraseSkill",
                "description": "Extract key highlights and travel topics",
                "context": "/document",
                "inputs": [{"name": "text", "source": "/document/content"}],
                "outputs": [{"name": "keyPhrases", "targetName": "keyphrases"}]
            }
        ]
    }
