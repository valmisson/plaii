"""
Image handling utilities
"""
import base64
from typing import Dict, Optional, Any


def get_album_cover(music_metadata: Dict[str, Any]) -> Optional[str]:
    """
    Get album cover from music metadata as base64 encoded string

    Args:
        music_metadata (Dict[str, Any]): Music metadata containing an 'image' key

    Returns:
        Optional[str]: Base64 encoded image or None if no cover found
    """
    if not music_metadata or 'image' not in music_metadata or not music_metadata['image']:
        return None

    try:
        # The image is already in binary format from tinytag
        image_data = music_metadata['image']
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        return base64_image
    except Exception as err:
        print(f"Error processing album cover: {err}")
        return None


def image_to_base64(image_path: str) -> Optional[str]:
    """
    Convert an image file to base64 encoding

    Args:
        image_path (str): Path to the image file

    Returns:
        Optional[str]: Base64 encoded image or None if conversion fails
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as err:
        print(f"Error converting image to base64: {err}")
        return None
