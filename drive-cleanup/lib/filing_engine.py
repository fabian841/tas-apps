"""
Filing engine — determines where a file should be filed based on
filename, content, and the FILING_RULES table.
"""
import os
import re

from config.folder_structure import FILING_RULES, MEDIA_EXTENSIONS


def classify_file(filename, content=""):
    """
    Determine the destination folder for a file.
    Returns (destination_path, confidence_pct, matched_rule_keywords).
    """
    filename_lower = filename.lower()
    content_lower = content.lower() if content else ""
    combined = f"{filename_lower} {content_lower}"

    # Check file extension for media files
    _, ext = os.path.splitext(filename_lower)
    is_media = ext in MEDIA_EXTENSIONS

    best_match = None
    best_priority = 999
    matched_keywords = []

    for rule in FILING_RULES:
        for keyword in rule["keywords"]:
            if keyword.lower() in combined:
                if rule["priority"] < best_priority or (
                    rule["priority"] == best_priority and best_match is None
                ):
                    best_match = rule["destination"]
                    best_priority = rule["priority"]
                    matched_keywords = [keyword]
                elif rule["priority"] == best_priority and rule["destination"] == best_match:
                    matched_keywords.append(keyword)

    # If it's a media file and no better match, send to MEDIA
    if is_media and (best_match is None or best_priority > 2):
        # Check if filename hints at a product
        product_keywords = ["pb4000", "portaboom", "miniboom", "tz30"]
        if any(pk in filename_lower for pk in product_keywords):
            best_match = "SALES & MARKETING/MEDIA"
            matched_keywords = ["media+product"]
        elif best_match is None:
            best_match = "SALES & MARKETING/MEDIA"
            matched_keywords = ["media_extension"]

    if best_match is None:
        return None, 0, []

    # Calculate confidence
    confidence = _calculate_confidence(best_priority, len(matched_keywords), bool(content))
    return best_match, confidence, matched_keywords


def _calculate_confidence(priority, keyword_count, has_content):
    """
    Confidence scoring:
    - Priority 1 (very specific): 90-100%
    - Priority 2 (specific): 75-90%
    - Priority 3 (general): 50-70%
    Bonus for multiple keyword matches and content availability.
    """
    base = {1: 90, 2: 75, 3: 50}.get(priority, 40)
    bonus = min(keyword_count - 1, 3) * 5  # up to +15 for multiple matches
    content_bonus = 10 if has_content else 0
    return min(base + bonus + content_bonus, 100)


def generate_filename(original_name, date_str=None):
    """
    Rename file per convention: YYYYMMDD_Topic_Source.ext
    If date unknown, use 000000.
    """
    _, ext = os.path.splitext(original_name)
    # Clean the name
    name = os.path.splitext(original_name)[0]
    # Replace spaces with underscores, remove special chars
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"\s+", "_", clean.strip())

    if date_str is None:
        date_str = "000000"

    return f"{date_str}_{clean}{ext}"


def generate_archive_name(original_name):
    """Prefix with ARCHIVED_ when moving to archive."""
    if original_name.startswith("ARCHIVED_"):
        return original_name
    return f"ARCHIVED_{original_name}"
