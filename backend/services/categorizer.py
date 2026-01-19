"""
Document Categorization Service

Hybrid categorization approach:
1. Filename pattern matching (high confidence)
2. Content keyword analysis (fallback for uncategorized)
"""

from typing import List, Dict, Optional
import re

# Category patterns with filename keywords, content keywords, and weights
CATEGORY_PATTERNS = {
    "NDAs": {
        "filename_keywords": ["NDA", "NON-DISCLOSURE", "CONFIDENTIALITY"],
        "content_keywords": ["confidential information", "non-disclosure", "proprietary", "confidentiality agreement"],
        "weight": {"filename": 10, "content": 5}
    },
    "Employment Agreements": {
        "filename_keywords": ["EMPLOYMENT", "OFFER LETTER", "EMPLOYEE", "OFFER_LETTER"],
        "content_keywords": ["employment", "salary", "benefits", "terminate employment", "job title", "compensation"],
        "weight": {"filename": 10, "content": 5}
    },
    "Vendor Contracts": {
        "filename_keywords": ["VENDOR", "SUPPLIER", "PURCHASE", "VENDOR_"],
        "content_keywords": ["vendor", "supplier", "goods and services", "purchase order", "vendor agreement"],
        "weight": {"filename": 10, "content": 5}
    },
    "Master Service Agreements": {
        "filename_keywords": ["MSA", "MASTER SERVICE", "MASTER_SERVICE"],
        "content_keywords": ["master service agreement", "statement of work", "scope of work", "service level"],
        "weight": {"filename": 10, "content": 5}
    },
    "Statements of Work": {
        "filename_keywords": ["SOW", "STATEMENT OF WORK", "STATEMENT_OF_WORK"],
        "content_keywords": ["deliverables", "milestones", "project scope", "statement of work", "work product"],
        "weight": {"filename": 10, "content": 5}
    },
    "Lease Agreements": {
        "filename_keywords": ["LEASE", "RENTAL", "TENANCY"],
        "content_keywords": ["lease", "tenant", "landlord", "premises", "rental", "lessor", "lessee"],
        "weight": {"filename": 10, "content": 5}
    },
    "Amendments": {
        "filename_keywords": ["AMENDMENT", "ADDENDUM", "MODIFICATION"],
        "content_keywords": ["hereby amended", "effective date of amendment", "addendum", "modification to"],
        "weight": {"filename": 10, "content": 5}
    },
    "Service Agreements": {
        "filename_keywords": ["SERVICE AGREEMENT", "SERVICE_AGREEMENT", "SERVICES"],
        "content_keywords": ["service agreement", "services to be provided", "service provider", "scope of services"],
        "weight": {"filename": 10, "content": 5}
    }
}

def categorize_document(filename: str, text_chunks: Optional[List[str]] = None) -> str:
    """
    Categorize document using hybrid approach.

    Phase 1: Filename pattern matching - fast and accurate for well-named files
    Phase 2: Content keyword analysis - for ambiguous filenames

    Args:
        filename: Document filename (e.g., "NDA_2023.pdf")
        text_chunks: Optional list of text chunks for content analysis

    Returns:
        Category name or "Uncategorized" if no confident match
    """
    filename_upper = filename.upper()

    # Phase 1: Filename matching - check for exact keyword matches
    for category, patterns in CATEGORY_PATTERNS.items():
        for keyword in patterns["filename_keywords"]:
            if keyword in filename_upper:
                return category

    # Phase 2: Content analysis (if chunks provided)
    if text_chunks and len(text_chunks) > 0:
        scores = {category: 0 for category in CATEGORY_PATTERNS.keys()}

        # Use first 3 chunks for efficiency (enough for classification)
        sample_text = " ".join(text_chunks[:3]).lower()

        # Score each category based on keyword frequency
        for category, patterns in CATEGORY_PATTERNS.items():
            for keyword in patterns["content_keywords"]:
                count = sample_text.count(keyword.lower())
                scores[category] += count * patterns["weight"]["content"]

        # Return highest scoring category if above threshold
        max_category = max(scores, key=scores.get)
        if scores[max_category] >= 10:  # Threshold for confident content-based match
            return max_category

    return "Uncategorized"


def extract_entities_from_chunks(chunks: List[str]) -> List[Dict]:
    """
    Extract entities (companies, persons, dates) from text chunks.

    Uses regex patterns - no NLP library required for basic extraction.

    Args:
        chunks: List of text chunks to analyze

    Returns:
        List of {"type": str, "value": str, "frequency": int}
    """
    entities = {}  # {(type, value): frequency}

    # Combine first 5 chunks for entity extraction
    text = " ".join(chunks[:5])

    # Pattern 1: Company names (Corp, Inc, LLC, Ltd, etc.)
    company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Corp(?:oration)?|Inc(?:orporated)?|LLC|Ltd|Limited|LP|LLP|Company|Co\.))\b'
    companies = re.findall(company_pattern, text)
    for company in companies:
        key = ("company", company)
        entities[key] = entities.get(key, 0) + 1

    # Pattern 2: Person names in signature contexts
    # "Signed by [Name]", "Executed by [Name]", "By: [Name]"
    person_patterns = [
        r'(?:Signed by|Executed by|By:)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'(?:Name|Signature):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
    ]
    for pattern in person_patterns:
        persons = re.findall(pattern, text)
        for person in persons:
            key = ("person", person)
            entities[key] = entities.get(key, 0) + 1

    # Pattern 3: Dates (MM/DD/YYYY, Month DD, YYYY)
    date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
        r'\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b'
    ]
    for pattern in date_patterns:
        dates = re.findall(pattern, text, re.IGNORECASE)
        for date in dates:
            key = ("date", date)
            entities[key] = entities.get(key, 0) + 1

    # Convert to list format
    result = [
        {"type": entity_type, "value": value, "frequency": freq}
        for (entity_type, value), freq in entities.items()
    ]

    # Sort by frequency (most common first)
    result.sort(key=lambda x: x["frequency"], reverse=True)

    return result


def get_category_statistics(documents: List[Dict]) -> Dict[str, int]:
    """
    Calculate category distribution from document list.

    Args:
        documents: List of documents with "category" field

    Returns:
        Dictionary mapping category name to count
    """
    stats = {}
    for doc in documents:
        category = doc.get("category", "Uncategorized")
        stats[category] = stats.get(category, 0) + 1

    # Sort by count (descending)
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
