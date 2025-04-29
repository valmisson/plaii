"""
Music tracks view component
"""
from flet import (
    Column,
    Container,
    CrossAxisAlignment,
    Icon,
    Icons,
    padding,
    Page,
    Text,
)
from typing import List

from app.config.colors import AppColors
from app.config.settings import DEFAULT_VIEW_HEIGHT
from app.core.models import Music
from app.data.repositories import MusicRepository
from app.services.audio_service import AudioService
from app.ui.components.music_list import MusicListComponent


class MusicsView(Container):
    """View for displaying music tracks"""

    def __init__(self, page: Page, audio_service: AudioService):
        """
        Initialize the music view

        Args:
            page (Page): The Flet page object
            audio_service (AudioService): The audio service for playback
        """
        super().__init__()

        self.page = page
        self.audio_service = audio_service
        self.music_repository = MusicRepository()

        # State
        self.musics: List[Music] = []

        # Create the view
        self.padding = padding.only(top=20)
        self.expand = True
        self.content = self._build()

    def _build(self):
        """Build the view"""
        self.musics = self.music_repository.get_all_music()
        self._loading = False

        return self._build_music_list() if self.musics else self._build_empty_state()

    def _build_music_list(self):
        """Build the music tracks table"""
        return Column(
            spacing=10,
            controls=[
                Container(
                    padding=padding.symmetric(horizontal=15),
                    content=Text(
                        "Todas as músicas",
                        color=AppColors.WHITE,
                        size=14,
                    ),
                ),
                MusicListComponent(
                    page=self.page,
                    audio_service=self.audio_service,
                    musics=self.musics,
                    height=DEFAULT_VIEW_HEIGHT - 30,
                ),
            ],
        )

    def _build_empty_state(self):
        """Build the empty state message when no music is available"""
        return Container(
            padding=padding.symmetric(vertical=150),
            content=Column(
                horizontal_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Icon(
                        Icons.MUSIC_OFF,
                        size=64,
                        color=AppColors.GREY
                    ),
                    Text(
                        "Nenhuma música encontrada",
                        size=16,
                        color=AppColors.GREY_LIGHT_100
                    ),
                    Container(height=20)
                ]
            )
        )


