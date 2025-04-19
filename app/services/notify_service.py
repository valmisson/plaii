"""
Notification service for handling notifications in the application.
"""
from flet import (
    Container,
    MainAxisAlignment,
    padding,
    Page,
    Row,
    Text,
)
from threading import Timer
from typing import Optional

from app.config.colors import AppColors
from app.config.settings import DEFAULT_WINDOW_WIDTH


class NotifyService:
    def __init__(self, page: Page):
        self.page = page

        # Create the view
        self._container = Container(
            bgcolor=AppColors.BLACK_LIGHT_100,
            width=DEFAULT_WINDOW_WIDTH,
            visible=False,
            padding=padding.symmetric(vertical=5),
            content=Row(
                alignment=MainAxisAlignment.CENTER,
                controls=[
                    Text(
                        "Indexando bibliotecas...",
                        color=AppColors.WHITE,
                        max_lines=1,
                        size=14,
                    ),
                ]
            ),
        )

    def init(self):
        """Initialize the notification service"""
        return self._container

    def hide(self):
        """Hide the notification"""
        self._container.visible = False
        self.page.bottom_appbar.height = 120
        self.page.update()

    def show(self, time: Optional[int]=None):
        """Show the notification"""
        self._container.visible = True
        self.page.bottom_appbar.height = 150

        self.page.update()

        # Hide the notification after a certain time
        if time:
            timer = Timer(time/1000, self.hide)  # Convert milliseconds to seconds
            timer.start()
