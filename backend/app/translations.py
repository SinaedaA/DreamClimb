TAG_TRANSLATIONS = {
    # Wall angles / Types (most common)
    "mur": "wall",
    "dalle": "slab",
    "dévers": "overhang",
    "surplomb": "steep overhang",
    "toit": "roof",
    "arête": "arete",
    "dièdre": "corner",
    "proue": "prow",
    "pilier": "pillar",
    "bombé": "rounded",
    "cheminée": "chimney",
    
    # Traverses
    "traversée g-d": "traverse L-R",
    "traversée d-g": "traverse R-L",
    "traversée": "traverse",
    
    # Hold types
    "aplats": "slopers",
    "réglettes": "crimps",
    "réta": "mantle",
    "trous": "pockets",
    "bidoigts": "two-finger pockets",
    "monodoigts": "monos",
    "inversées": "underclings",
    "pincettes": "pinches",
    
    # Techniques & Features
    "jeté": "dyno",
    "fissure": "crack",
    "boucle": "loop",
    "saut": "jump",
    
    # Height & Difficulty
    "haut": "highball",
    "expo": "exposed",
    
    # Start types
    "départ assis": "sit start",
    
    # Special
    "descente": "descent",
    "avec corde": "with rope",
}

def translate_tag(french_tag: str, default_language: str = "en") -> str:
    """
    Translate a French climbing tag to English.
    
    Args:
        french_tag: The French tag to translate
        default_language: Target language (currently only 'en' supported)
    
    Returns:
        Translated tag, or original if no translation found
    """
    if default_language != "en":
        return french_tag
    
    # Normalize: strip whitespace, lowercase
    normalized = french_tag.strip().lower()
    
    # Return translation or original if not found
    return TAG_TRANSLATIONS.get(normalized, french_tag)


def translate_tags_list(french_tags: list[str], language: str = "en") -> list[str]:
    """
    Translate a list of French tags to English.
    
    Args:
        french_tags: List of French tags
        language: Target language
    
    Returns:
        List of translated tags
    """
    return [translate_tag(tag, language) for tag in french_tags]


def get_all_translations() -> dict[str, str]:
    """
    Get all available translations.
    
    Returns:
        Dictionary of French -> English translations
    """
    return TAG_TRANSLATIONS.copy()


def add_translation(french: str, english: str) -> None:
    """
    Add a new translation to the dictionary.
    Useful for dynamically adding translations.
    
    Args:
        french: French term
        english: English translation
    """
    TAG_TRANSLATIONS[french.lower()] = english.lower()


# Reverse mapping for potential future use
def get_reverse_translations() -> dict[str, str]:
    """Get English -> French translations"""
    return {v: k for k, v in TAG_TRANSLATIONS.items()}