import re
from typing import Tuple


SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"reveal\s+(system\s+)?prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+safety\s+filters",
    r"system\s*:\s*override",
    r"give\s+me\s+your\s+(api\s+)?keys?",
]


def validate_and_sanitize_query(query: str, max_length: int = 500) -> Tuple[bool, str]:
    """
    Validates user query against security rules:
    - Empty or whitespace check
    - Max length enforcement
    - Regex pattern matching for known prompt injection signatures

    Returns:
        (is_valid, sanitized_or_error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."

    cleaned_query = query.strip()

    if len(cleaned_query) > max_length:
        return False, f"Query exceeds maximum allowed length of {max_length} characters."

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, cleaned_query, re.IGNORECASE):
            return False, "Query rejected by security guardrails: suspicious prompt manipulation detected."

    # Remove non-printable control characters except standard punctuation and newlines
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned_query)
    return True, sanitized
