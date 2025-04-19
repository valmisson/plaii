from app.core.models import Album, Music
from re import match
from typing import List
from unicodedata import combining, normalize

def normalize_str(value: str) -> str:
    """
    Normalize a string by removing accents and special characters
    Args:
        value (str): The string to normalize
    Returns:
        str: The normalized string
    """
    if value is None:
        return ""

    # Convert to string if it's not already
    value_str = str(value)

    # Normalize to decompose accents
    normalized = normalize('NFD', value_str)

    # Keep only letters (no accents, no special characters)
    result = ''.join(c for c in normalized
                     if not combining(c))

    return result.lower()

def sort_list_by(key: str, list: List[Album|Music], reverse=False) -> List[Album|Music]:
    """
    Sort a list of objects by a specific key
    Args:
        list (List[Album|Music]): The list of objects to sort
        key (str): The key to sort by
        reverse (bool): Whether to reverse the order
    Returns:
        List[Album|Music]: The sorted list
    """
    # Define a custom sort key function
    def sort_key(text: str):
        regex = match(r'(\d+)', text)
        if regex:
            return (0, int(regex.group(0)), text)
        return (1, text)

    # Sort the list using the custom sort key
    return sorted(list, key=lambda x: sort_key(normalize_str(getattr(x, key, ""))), reverse=reverse)
