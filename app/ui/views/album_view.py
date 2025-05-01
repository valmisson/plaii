"""
Album view Component
"""
from flet import (
    ButtonStyle,
    BorderSide,
    Container,
    Column,
    CrossAxisAlignment,
    FilledButton,
    Icons,
    Image,
    MainAxisAlignment,
    OutlinedButton,
    Page,
    padding,
    Row,
    RoundedRectangleBorder,
    Text,
    TextOverflow,
)
from random import choice

from app.config.colors import AppColors
from app.config.settings import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT
)
from app.core.models import Album
from app.services.audio_service import AudioService
from app.ui.components.music_list import MusicListComponent


class AlbumView(Container):
    """View for displaying album details"""

    def __init__(self, page: Page, audio_service: AudioService, album: Album):
        """
        Initialize the AlbumView

        Args:
            page (Page): The Flet page object
            audio_service (AudioService): The audio service instance
            album (Album): The album object
        """
        super().__init__()

        self.page = page
        self.audio_service = audio_service
        self.album = album

        # Create the view
        self.expand = True
        self.padding = padding.only(top=20)
        self.content = self._build()

        self.page.pubsub.subscribe_topic('settings:folder:album', self.on_settings_folder_subscribe)

    def _build(self):
        """Build the album view"""
        return Column(
            spacing=25,
            controls=[
                self._build_album_details(),
                MusicListComponent(
                    page=self.page,
                    audio_service=self.audio_service,
                    musics=self.album.tracks,
                    height=DEFAULT_WINDOW_HEIGHT - 340,
                    is_album_view=True
                )
            ]
        )

    def _build_album_details(self):
        """Build the album details"""
        track_count = len(self.album.tracks)
        album_detail_artist = self.album.artist
        album_detail_year = f" • {self.album.year}" if self.album.year else ""
        album_detail_genre = f" • {self.album.genre}" if self.album.genre else ""
        album_detail_tracks = f" • {track_count} {'música' if track_count == 1 else 'músicas'}"

        return Container(
            height=110,
            padding=padding.symmetric(horizontal=20),
            content=Row(
                spacing=25,
                vertical_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Image(
                        src_base64=self.album.cover,
                        fit='cover',
                        border_radius=6,
                        width=110,
                    ),
                    Column(
                        controls=[
                            Text(
                                self.album.name,
                                size=18,
                                color=AppColors.WHITE,
                                max_lines=1,
                                overflow=TextOverflow.ELLIPSIS,
                            ),
                            Text(
                                f"{album_detail_artist}{album_detail_year}{album_detail_genre}{album_detail_tracks}",
                                size=16,
                                color=AppColors.WHITE_ACCENT,
                            ),
                            Container(
                                width=DEFAULT_WINDOW_WIDTH - 185,
                                content=Row(
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        Row(
                                            spacing=20,
                                            controls=[
                                                FilledButton(
                                                    icon=Icons.PLAY_ARROW,
                                                    text="Reproduzir tudo",
                                                    bgcolor=AppColors.PRIMARY,
                                                    color=AppColors.WHITE,
                                                    style=ButtonStyle(
                                                        shape=RoundedRectangleBorder(radius=4),
                                                    ),
                                                    on_click=self._on_play_album,
                                                ),
                                                OutlinedButton(
                                                    icon=Icons.QUEUE_MUSIC,
                                                    text="Adicionar à fila",
                                                    icon_color=AppColors.WHITE_ACCENT,
                                                    style=ButtonStyle(
                                                        color=AppColors.WHITE_ACCENT,
                                                        shape=RoundedRectangleBorder(radius=4),
                                                        side=BorderSide(
                                                            color=AppColors.WHITE_ACCENT,
                                                            width=1,
                                                        )
                                                    ),
                                                    on_click=self._on_add_to_queue,
                                                ),
                                            ]
                                        ),
                                        OutlinedButton(
                                            icon=Icons.KEYBOARD_RETURN,
                                            text="Voltar",
                                            icon_color=AppColors.WHITE_ACCENT,
                                            style=ButtonStyle(
                                                color=AppColors.WHITE_ACCENT,
                                                shape=RoundedRectangleBorder(radius=4),
                                                side=BorderSide(
                                                    color=AppColors.WHITE_ACCENT,
                                                    width=1,
                                                )
                                            ),
                                            on_click=self._on_goto_albums_view,
                                        ),
                                    ]
                                )
                            )
                        ]
                    )
                ]
            )
        )

    def _on_play_album(self, _):
        """Handle play album button click"""
        player_state = self.audio_service.player_repository.get_player_state()

        music_to_play = self.album.tracks[0]

        if player_state.is_shuffle:
            music_to_play = choice(self.album.tracks)

        # Set up playlist from album tracks and play first track
        all_tracks = [t.to_dict() for t in self.album.tracks]
        player_state.playlist = all_tracks
        player_state.playlist_source = "album"  # Mark that we're playing a specific album
        self.audio_service.player_repository.update_player_state(player_state)
        self.audio_service.load_music(music_to_play)
        self.audio_service.play()

    def _on_add_to_queue(self, _):
        """Handle add to queue button click"""
        # Get player state and convert album tracks to dict format
        tracks_to_add = [t.to_dict() for t in self.album.tracks]
        player_state = self.audio_service.player_repository.get_player_state()

        # If player is inactive, play immediately
        if not player_state.is_playing and not player_state.playlist:
            # Start playing this album
            player_state.playlist = tracks_to_add
            player_state.playlist_source = "album"
            self.audio_service.player_repository.update_player_state(player_state)
            self.audio_service.load_music(self.album.tracks[0])
            self.audio_service.play()
            return

        # Otherwise, just append to the existing queue
        player_state.playlist.extend(tracks_to_add)
        self.audio_service.player_repository.update_player_state(player_state)
        self.page.update()

    def _on_goto_albums_view(self, _):
        """Handle go to albums view button click"""
        if self.page:
            self.page.pubsub.send_all_on_topic(
                'navigation:album',
                {'index_view': 1, 'album': None}
            )

    def on_settings_folder_subscribe(self, _, data: dict):
        """
        Handle settings folder subscription

        Args:
            _: Unused parameter
            data (dict): Data received from the subscription
        """
        self._on_goto_albums_view(_)
