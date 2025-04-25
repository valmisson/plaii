"""
Application top bar component
"""
from flet import (
    Container,
    ButtonStyle,
    Icon,
    Icons,
    IconButton,
    MainAxisAlignment,
    MouseCursor,
    padding,
    Page,
    Row,
    RoundedRectangleBorder,
    Text,
    WindowDragArea,
)
from typing import Callable

from app.config.settings import APP_NAME
from app.config.colors import AppColors
from app.services.audio_service import AudioService


class AppBar(Container):
    """Application top bar class"""

    def __init__(self, page: Page, audio_service: AudioService, on_settings: Callable):
        """
        initialize the application top bar

        Args:
            page (Page): The Flet page object
            audio_service (AudioService): The audio service for playback
            on_settings (Callable): Callback function for settings button
        """
        super().__init__()

        self.page = page
        self.audio_service = audio_service
        self.on_settings = on_settings

        # Create the view
        self.padding=padding.only(left=5)
        self.content = self._build()

    def _build(self):
        """Build the view"""
        return WindowDragArea(
            maximizable=False,
            content=self._create_app_bar()
        )

    def _create_app_bar(self):
        """Build the application top bar"""
        return Row(
            alignment=MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                IconButton(
                    icon=Icons.MORE_HORIZ,
                    icon_size=24,
                    icon_color=AppColors.WHITE,
                    highlight_color=AppColors.TRANSPARENT,
                    hover_color=AppColors.TRANSPARENT,
                    width=35,
                    tooltip="Configurações",
                    on_click=self.on_settings
                ),
                Row(
                    spacing=5,
                    alignment=MainAxisAlignment.START,
                    controls=[
                        Icon(
                            Icons.MUSIC_NOTE_OUTLINED,
                            color=AppColors.PRIMARY,
                            size=22,
                        ),
                        Text(
                            value=APP_NAME,
                            color=AppColors.WHITE,
                            size=16,
                        )
                    ]
                ),
                Row(
                    spacing=0,
                    controls=[
                        IconButton(
                            icon=Icons.REMOVE,
                            icon_color=AppColors.WHITE,
                            bgcolor=AppColors.BLACK,
                            icon_size=20,
                            height=35,
                            width=45,
                            tooltip='Minimizar',
                            style=ButtonStyle(
                                shape=RoundedRectangleBorder(radius=0),
                                overlay_color=AppColors.GREY,
                                mouse_cursor=MouseCursor.BASIC,
                            ),
                            on_click=self.on_minimize,
                        ),
                        IconButton(
                            icon=Icons.CLOSE,
                            icon_color=AppColors.WHITE,
                            bgcolor=AppColors.BLACK,
                            icon_size=20,
                            height=35,
                            width=45,
                            tooltip='Fechar',
                            style=ButtonStyle(
                                shape=RoundedRectangleBorder(radius=0),
                                overlay_color=AppColors.RED,
                                mouse_cursor=MouseCursor.BASIC,
                            ),
                            on_click=self.on_close,
                        )
                    ]
                )
            ]
        )

    def on_minimize(self, _):
        """
        Minimize the application window

        Args:
            _: Event object
        """

        # Minimize the window
        self.page.window.minimized = True
        self.page.update()

    def on_close(self, _):
        """
        Close the application window
        Args:
            _: Event object
        """

        # Pause the audio if it's playing
        repository = self.audio_service.player_repository
        state = repository.get_player_state()

        if state.is_playing:
            state.is_playing = False
            state.is_pause = True
            repository.update_player_state(state)

        # Close the application
        self.page.window.close()
