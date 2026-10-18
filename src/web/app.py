import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import settings
from src.core.security import validate_and_sanitize_query
from src.core.search_client import AzureSearchService
from src.core.rag_engine import RAGEngine

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)

search_service = AzureSearchService()
rag_engine = RAGEngine()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST", "GET"])
def handle_rag_query():
    """
    Primary endpoint: Validates user input, retrieves relevant travel context
    via Hybrid Search, and generates grounded synthesis using GPT-4o.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        raw_query = data.get("query", "")
    else:
        raw_query = request.args.get("query", "")

    # Security Guardrail Check
    is_valid, validation_msg = validate_and_sanitize_query(raw_query)
    if not is_valid:
        return jsonify({
            "status": "error",
            "message": validation_msg
        }), 400

    sanitized_query = validation_msg

    # Step 1: Hybrid Retrieval
    retrieved_chunks = search_service.search(
        query=sanitized_query,
        top_k=settings.max_context_chunks
    )

    # Step 2: Grounded Synthesis
    generation_result = rag_engine.generate(
        query=sanitized_query,
        retrieved_chunks=retrieved_chunks
    )

    return jsonify({
        "status": "success",
        "query": sanitized_query,
        "answer": generation_result["answer"],
        "citations": generation_result["citations"],
        "latency_seconds": generation_result["latency_seconds"],
        "model": generation_result["model"],
        "notice": generation_result.get("notice")
    })


@app.route("/api/search", methods=["GET"])
def handle_search_only():
    """Returns raw hybrid search results without LLM synthesis."""
    query = request.args.get("q", "")
    is_valid, sanitized = validate_and_sanitize_query(query)
    if not is_valid:
        return jsonify({"status": "error", "message": sanitized}), 400

    results = search_service.search(sanitized, top_k=settings.max_context_chunks)
    return jsonify({
        "status": "success",
        "query": sanitized,
        "count": len(results),
        "results": results
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "Enterprise Travel RAG Assistant",
        "version": "1.0.0",
        "azure_search_configured": bool(settings.azure_search_key),
        "azure_openai_configured": bool(settings.azure_openai_key),
        "model_deployment": settings.azure_openai_deployment
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=settings.app_port,
        debug=settings.app_debug
    )
