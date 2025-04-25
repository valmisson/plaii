from flet import (
    BottomAppBar,
    Column,
    Page,
)

from app.config.settings import DEFAULT_PLAYER_HEIGHT
from app.config.colors import AppColors
from app.services.audio_service import AudioService
from app.services.notify_service import NotifyService
from app.ui.layout.player_bar import PlayerBar


class BottomBar(BottomAppBar):
    """Application bottom bar class"""

    def __init__(self, page: Page, audio_service: AudioService, notify_service: NotifyService):
        """
        Initialize the application bottom bar

        Args:
            page (Page): The Flet page object
        """
        super().__init__()

        self.page = page
        self.audio_service = audio_service
        self.notify_service = notify_service

        # Create the view
        self.height = DEFAULT_PLAYER_HEIGHT
        self.padding = 0
        self.bgcolor = AppColors.TRANSPARENT
        self.content = self._build()

    def _build(self):
        """Build the view"""
        return Column(
            spacing=0,
            controls=[
                self.notify_service.init(),
                PlayerBar(page=self.page, audio_service=self.audio_service),
            ]
        )
