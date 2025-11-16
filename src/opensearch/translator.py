"""
Library description translator.

Translates foreign language library descriptions to English using LLM.
"""

import re
from typing import Any
from src.llm.client import llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


def detect_non_english(text: str) -> bool:
    """
    Detect if text contains non-English characters.

    Args:
        text: Text to check

    Returns:
        True if text contains non-ASCII characters (likely foreign language)
    """
    if not text:
        return False

    # Check for common non-English character ranges
    # Chinese, Japanese, Korean, Arabic, Cyrillic, etc.
    non_english_pattern = re.compile(r'[^\x00-\x7F]+')
    return bool(non_english_pattern.search(text))


async def translate_description(description: str, source_language: str = "auto") -> str:
    """
    Translate library description to English using LLM.

    Args:
        description: Description text to translate
        source_language: Source language (default: "auto" for auto-detect)

    Returns:
        Translated description in English
    """
    if not description or not detect_non_english(description):
        # Already in English or empty
        return description

    try:
        logger.info(f"Translating description", length=len(description), has_non_english=True)

        system_prompt = """You are a technical translator specializing in software library descriptions.
Translate the given text to English while preserving technical terms and package names.
Keep the translation concise and accurate. Only output the translation, no explanations."""

        user_prompt = f"""Translate this library description to English:

{description}

Translation:"""

        translated = await llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,  # Low temperature for consistent translations
        )

        # Clean up translation
        translated = translated.strip()

        logger.info(f"Translation complete", original_length=len(description), translated_length=len(translated))

        return translated

    except Exception as e:
        logger.error(f"Translation failed", error=str(e), description_length=len(description))
        # Return original description if translation fails
        return description


async def translate_library_descriptions(libraries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Translate descriptions for a list of libraries.

    Args:
        libraries: List of library dictionaries with 'description' field

    Returns:
        Updated list with translated descriptions
    """
    for library in libraries:
        description = library.get("description", "")
        if description and detect_non_english(description):
            # Translate description
            translated = await translate_description(description)
            library["description"] = translated
            library["original_description"] = description  # Keep original for reference
            logger.debug(
                f"Translated library description",
                library=library.get("library_name", "Unknown"),
                original=description[:50],
                translated=translated[:50],
            )

    return libraries


__all__ = [
    "detect_non_english",
    "translate_description",
    "translate_library_descriptions",
]
