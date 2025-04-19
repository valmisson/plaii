"""
Time formatting utilities
"""
from app.config.settings import DEFAULT_DURATION_TEXT


def format_time(milliseconds: int, is_in_seconds=False) -> str:
    """
    Format milliseconds to mm:ss format

    Args:
        milliseconds (int or float): Time in milliseconds or seconds
        is_in_seconds (bool): If True, milliseconds are treated as seconds

    Returns:
        str: Formatted time string in mm:ss format
    """
    if milliseconds is None:
        return DEFAULT_DURATION_TEXT

    # Convert to float first to ensure we handle all numeric types
    milliseconds = float(milliseconds)

    # Convert milliseconds to seconds
    seconds_total = int(milliseconds // 1000) if not is_in_seconds else int(milliseconds)

    # Calculate minutes and remaining seconds
    minutes = seconds_total // 60
    seconds = seconds_total % 60

    # Format as mm:ss
    return f"{minutes:02d}:{seconds:02d}"


def parse_time(time_str: str) -> int:
    """
    Parse time string in mm:ss format to milliseconds

    Args:
        time_str (str): Time string in mm:ss format

    Returns:
        int: Time in milliseconds
    """
    if not time_str or ":" not in time_str:
        return 0

    try:
        # Split into minutes and seconds
        parts = time_str.split(":")
        if len(parts) != 2:
            return 0

        minutes = int(parts[0])
        seconds = int(parts[1])

        # Convert to milliseconds
        return (minutes * 60 + seconds) * 1000
    except ValueError:
        return 0
