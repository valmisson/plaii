"""
Image handling utilities
"""
import base64
from typing import Optional


def image_to_base64(image_data: str) -> Optional[str]:
    """
    Convert an image to base64 encoding

    Args:
        image_data (str): Base64 encoded image data

    Returns:
        Optional[str]: Base64 encoded image or None if no cover found
    """
    if not image_data:
        return None

    try:
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        return base64_image
    except Exception as err:
        print(f"Error processing album cover: {err}")
        return None
