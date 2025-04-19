"""
Application color scheme
"""
from flet import Colors
from enum import Enum


class AppColors(Enum):
    # Primary colors
    PRIMARY = Colors.RED_ACCENT_200

    # Text and backgrounds
    BLACK = Colors.GREY_900
    BLACK_DARK_100 = "#1D1D1D"
    BLACK_LIGHT_100 = "#262626"
    WHITE = Colors.WHITE
    GREY = Colors.GREY_800
    GREY_LIGHT_100 = Colors.GREY_600
    GREY_LIGHT_200 = Colors.GREY_500
    GREY_LIGHT_300 = Colors.GREY_400

    # Accent colors
    WHITE_ACCENT = Colors.WHITE70
    RED = Colors.RED_700
    GREEN = Colors.GREEN_700

    # Utility colors
    TRANSPARENT = Colors.TRANSPARENT

    def __str__(self):
        return self.value

    def __get__(self, instance, owner):
        return self.value
