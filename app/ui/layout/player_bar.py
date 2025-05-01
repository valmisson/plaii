"""
Player control bar component
"""
from flet import (
    Colors,
    Column,
    Container,
    ControlEvent,
    FontWeight,
    IconButton,
    Icons,
    Image,
    MainAxisAlignment,
    padding,
    Page,
    ResponsiveRow,
    Row,
    Slider,
    Text,
    TextOverflow,
)
from flet_audio import AudioState

from app.config.colors import AppColors
from app.config.settings import (
    DEFAULT_PLACEHOLDER_IMAGE,
    DEFAULT_DURATION_TEXT,
    DEFAULT_PLAYER_HEIGHT
)
from app.core.models import Music
from app.data.repositories import PlayerRepository, MusicRepository
from app.services.audio_service import AudioService
from app.services.metadata_service import MetadataService
from app.utils.time_format import format_time
from app.utils.helpers import safe_update


class PlayerBar(Container):
    """Player control bar component class"""

    def __init__(self, page: Page, audio_service: AudioService):
        """
        Initialize the player control bar

        Args:
            page (Page): The Flet page object
            audio_service (AudioService): The audio service
        """
        super().__init__()

        self.page = page
        self.audio_service = audio_service
        self.player_repository = PlayerRepository()
        self.music_repository = MusicRepository()

        # Initialize player state
        self.player_state = self.player_repository.get_player_state()
        self._is_muted = self.player_state.is_muted
        self._is_shuffle = self.player_state.is_shuffle
        self._is_repeat = self.player_state.is_repeat
        self._volume = self.player_state.volume
        self._is_playing = False
        self._was_playing = False

        # Create UI components
        self._create_ui_components()

        # Register callbacks with the audio service
        self._register_callbacks()

        # Initialize music info if available
        self._initialize_music_info()

        # Setup the BottomAppBar properties and content
        self.height = DEFAULT_PLAYER_HEIGHT
        self.bgcolor = AppColors.BLACK_DARK_100
        self.padding = padding.symmetric(vertical=10, horizontal=15)
        self.content = self._build()

    def _build(self):
        """Build the player bar content"""

        return Column(
            spacing=15,
            controls=[
                Row(
                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        self.current_time,
                        Container(
                            expand=True,
                            height=10,
                            content=self.progress_time
                        ),
                        self.end_time,
                    ]
                ),
                ResponsiveRow(
                    spacing=120,
                    controls=[
                        Row(  # Left section - album cover and track info
                            col=4,
                            controls=[
                                self.music_cover,
                                Column(
                                    width=240,
                                    spacing=5,
                                    controls=[
                                        self.music_title,
                                        self.music_artist
                                    ]
                                )
                            ]
                        ),
                        Row(  # Center section - playback controls
                            col=4,
                            alignment=MainAxisAlignment.CENTER,
                            controls=[
                                self.button_shuffle,
                                self.button_previous,
                                self.button_play,
                                self.button_pause,
                                self.button_next,
                                self.button_repeat
                            ]
                        ),
                        Row(  # Right section - volume control
                            col=4,
                            alignment=MainAxisAlignment.END,
                            controls=[
                                self.button_volume,
                                self.volume_slider
                            ],
                        )
                    ]
                )
            ]
        )

    def _create_ui_components(self):
        """Create all UI components used in the player bar"""
        # Time display components
        self.current_time = Text(
            value=DEFAULT_DURATION_TEXT,
            color=AppColors.WHITE,
        )

        self.progress_time = Slider(
            min=0,
            active_color=AppColors.PRIMARY,
            inactive_color=AppColors.GREY,
            on_change_end=self.on_progress_time_seek,
            on_change_start=self.on_start_progress_time_seek,
        )

        self.end_time = Text(
            value=DEFAULT_DURATION_TEXT,
            color=AppColors.WHITE,
        )

        # Music info components
        self.music_cover = Image(
            width=62,
            height=62,
            border_radius=4,
            src=DEFAULT_PLACEHOLDER_IMAGE,
        )

        self.music_title = Text(
            value='Titulo da musica',
            color=AppColors.WHITE,
            size=16,
            weight=FontWeight.W_500,
            max_lines=1,
            overflow=TextOverflow.ELLIPSIS,
        )

        self.music_artist = Text(
            value='Nome do artista',
            color=AppColors.GREY_LIGHT_200,
            size=14,
            max_lines=1,
        )

        # Playback control buttons
        self.button_play = IconButton(
            tooltip='Executar',
            icon=Icons.PLAY_ARROW,
            icon_color=AppColors.BLACK,
            icon_size=30,
            bgcolor=AppColors.WHITE,
            hover_color=AppColors.TRANSPARENT,
            visible=not self._is_playing,
            on_click=lambda _: self.audio_service.resume()
        )

        self.button_pause = IconButton(
            tooltip='Pausar',
            icon=Icons.PAUSE,
            icon_color=AppColors.BLACK,
            icon_size=30,
            bgcolor=AppColors.WHITE,
            hover_color=AppColors.TRANSPARENT,
            visible=self._is_playing,
            on_click=lambda _: self.audio_service.pause()
        )

        self.button_previous = IconButton(
            tooltip='Voltar',
            icon=Icons.SKIP_PREVIOUS,
            icon_color=AppColors.WHITE,
            icon_size=28,
            hover_color=AppColors.TRANSPARENT,
            highlight_color=Colors.with_opacity(0.1, AppColors.GREY),
            on_click=lambda _: self.audio_service.play_previous()
        )

        self.button_next = IconButton(
            icon_size=28,
            tooltip='Avançar',
            icon=Icons.SKIP_NEXT,
            icon_color=AppColors.WHITE,
            hover_color=AppColors.TRANSPARENT,
            highlight_color=Colors.with_opacity(0.1, AppColors.GREY),
            on_click=lambda _: self.audio_service.play_next()
        )

        self.button_shuffle = IconButton(
            icon=Icons.SHUFFLE,
            icon_color=AppColors.PRIMARY if self._is_shuffle else AppColors.GREY_LIGHT_100,
            hover_color=AppColors.TRANSPARENT,
            tooltip='Embaralhar: ' + ('Ativado' if self._is_shuffle else 'Desativado'),
            highlight_color=Colors.with_opacity(0.1, AppColors.GREY),
            on_click=lambda _: self._update_shuffle_state()
        )

        self.button_repeat = IconButton(
            icon=Icons.REPEAT_ONE if self._is_repeat == 'one' else Icons.REPEAT,
            icon_color=AppColors.PRIMARY if self._is_repeat else AppColors.GREY_LIGHT_100,
            hover_color=AppColors.TRANSPARENT,
            tooltip='Repetir: ' + ('Um' if self._is_repeat == 'one' else 'Tudo' if self._is_repeat == 'all' else 'Desativado'),
            highlight_color=Colors.with_opacity(0.1, AppColors.GREY),
            on_click=lambda _: self._update_repeat_state()
        )

        # Volume control components
        self.button_volume = IconButton(
            tooltip='Volume',
            icon=self._get_volume_icon(self._volume, self._is_muted),
            icon_color=AppColors.WHITE,
            hover_color=AppColors.TRANSPARENT,
            highlight_color=Colors.with_opacity(0.1, AppColors.GREY),
            on_click=lambda _: self._toggle_mute()
        )

        self.volume_slider = Slider(
            min=0,
            max=1,
            value=0 if self._is_muted else self._volume,
            width=120,
            label='{value}',
            active_color=AppColors.PRIMARY,
            inactive_color=AppColors.GREY,
            on_change=lambda e: self._set_volume(e.control.value),
        )

    def _register_callbacks(self):
        """Register callbacks with the audio service"""
        self.audio_service.on_position_changed(self.on_position_changed)
        self.audio_service.on_state_changed(self.on_state_changed)
        self.audio_service.on_music_changed(self._update_music_info)

        self.page.pubsub.subscribe_topic('settings:folder:player', self.on_settings_folder_subscribe)

    def _initialize_music_info(self):
        """Initialize music info if available"""
        if self.player_state.current_music:
            try:
                current_music = Music.from_dict(self.player_state.current_music)
                self._update_music_info(current_music)

                if self.player_state.audio_position is not None and self.player_state.audio_duration is not None:
                    self._update_current_time(self.player_state.audio_position)
                    self._update_end_time(self.player_state.audio_position, self.player_state.audio_duration)
                    self._update_progress_time(self.player_state.audio_position, self.player_state.audio_duration)
            except Exception as err:
                print(f"Error initializing music info: {err}")

    def _update_play_button(self, is_play: bool):
        """Update the play/pause button state"""
        self._is_playing = is_play
        self.button_play.visible = not is_play
        self.button_pause.visible = is_play
        safe_update(self)

    def _update_current_time(self, position: int):
        """Update the current time display"""
        self.current_time.value = format_time(position)
        safe_update(self)

    def _update_end_time(self, position: int, duration: int):
        """Update the end time display"""
        try:
            if duration is None:
                self.end_time.value = DEFAULT_DURATION_TEXT
            else:
                new_time = duration - position
                self.end_time.value = format_time(new_time)
            safe_update(self)
        except Exception as err:
            print(f'Error updating end time: {err}')
            self.end_time.value = DEFAULT_DURATION_TEXT
            safe_update(self)

    def _update_progress_time(self, current_position: int, end_position: int):
        """Update the progress slider"""
        try:
            self.progress_time.value = current_position
            if end_position is not None and end_position > 0:
                self.progress_time.max = end_position
            safe_update(self)
        except Exception as err:
            print(f'Error updating progress time: {err}')

    def _update_music_info(self, music: Music):
        """Update the displayed music information"""
        self.music_title.value = music.title
        self.music_artist.value = music.artist
        self.end_time.value = music.duration
        self.current_time.value = DEFAULT_DURATION_TEXT
        self.progress_time.value = 0
        self._update_music_cover(music.filename)
        safe_update(self.page)

    def _update_music_cover(self, filename: str):
        """Update the music cover image"""
        try:
            cover = MetadataService.load_music_cover(filename)
            self.music_cover.src_base64 = cover
            safe_update(self)
        except Exception as err:
            print(f'Error updating music cover: {err}')
            self.music_cover.src = DEFAULT_PLACEHOLDER_IMAGE
            safe_update(self)

    def _update_shuffle_state(self):
        """Update the shuffle button state"""
        self._is_shuffle = self.audio_service.toggle_shuffle()
        self.button_shuffle.icon_color = AppColors.PRIMARY if self._is_shuffle else AppColors.GREY_LIGHT_100
        self.button_shuffle.tooltip = 'Embaralhar: ' + ('Ativado' if self._is_shuffle else 'Desativado')
        safe_update(self.button_shuffle)

    def _update_repeat_state(self):
        """Update the repeat button state"""
        self._is_repeat = self.audio_service.toggle_repeat()

        if self._is_repeat == 'one':
            self.button_repeat.icon = Icons.REPEAT_ONE
            self.button_repeat.tooltip = 'Repetir: Um'
            self.button_repeat.icon_color = AppColors.PRIMARY
        elif self._is_repeat == 'all':
            self.button_repeat.icon = Icons.REPEAT
            self.button_repeat.tooltip = 'Repetir: Tudo'
            self.button_repeat.icon_color = AppColors.PRIMARY
        else:
            self.button_repeat.icon = Icons.REPEAT
            self.button_repeat.tooltip = 'Repetir: Desativado'
            self.button_repeat.icon_color = AppColors.GREY_LIGHT_100

        safe_update(self.button_repeat)

    def _get_volume_icon(self, volume: float, is_muted: bool):
        """Get the volume icon based on volume level and mute state"""
        if is_muted or volume == 0:
            return Icons.VOLUME_OFF
        elif volume <= 0.44:
            return Icons.VOLUME_DOWN
        else:
            return Icons.VOLUME_UP

    def _toggle_mute(self):
        """Toggle the mute state"""
        self._is_muted = self.audio_service.toggle_mute()
        self.button_volume.icon = self._get_volume_icon(self._volume, self._is_muted)
        self.volume_slider.value = 0 if self._is_muted else self._volume
        safe_update(self)

    def _set_volume(self, new_volume: float):
        """Set the volume level"""
        self._volume = new_volume
        self._is_muted = new_volume == 0
        self.audio_service.set_volume(new_volume)
        self.button_volume.icon = self._get_volume_icon(new_volume, self._is_muted)
        safe_update(self.page)

    def on_position_changed(self, position, duration):
        """Handle audio position change events"""
        self._update_current_time(position)
        self._update_end_time(position, duration)
        self._update_progress_time(position, duration)

    def on_progress_time_seek(self, e: ControlEvent):
        """Handle end of progress time seek event"""
        self.audio_service.seek(int(float(e.data)))
        if self._was_playing:
            self.audio_service.resume()

    def on_start_progress_time_seek(self, _):
        """Handle start of progress time seek event"""
        self._was_playing = self._is_playing
        if self._is_playing:
            self.audio_service.pause()

    def on_state_changed(self, state, _):
        """Handle audio state change events"""
        self._update_play_button(state == AudioState.PLAYING)

    def on_settings_folder_subscribe(self, _, data: dict):
        """
        Handle settings folder subscription events

        Args:
            _ (str): The subscription topic name
            data (dict): Event data with folder path and state
        """
        state = data.get('state')
        folder_path = data.get('folder_path')

        # Handle different folder events
        if state == 'remove':
            self._handle_folder_removal(folder_path)
        elif state == 'new':
            self._handle_folder_addition(folder_path)

    def _handle_folder_removal(self, folder_path: str):
        """
        Update the playlist when a folder is removed from the system.
        Removes all references to music from the specified folder.

        Args:
            folder_path (str): The path of the folder being removed.
        """
        try:
            # Get a fresh copy of the player state
            player_state = self.player_repository.get_player_state()
            if not player_state:
                return

            # Skip if the playlist is empty
            if not player_state.playlist:
                return

            # Remove all playlist items from the removed folder
            original_len = len(player_state.playlist)
            player_state.playlist = [
                music for music in player_state.playlist
                if music.get('folder') != folder_path
            ]
            player_state.played_music = [
                music for music in player_state.played_music
                if music.get('folder') != folder_path
            ]

            # Save changes to database if the playlist was updated
            if len(player_state.playlist) != original_len:
                self.player_repository.update_player_state(player_state)
                self.player_state = player_state

        except Exception as err:
            import traceback
            print(f"Error updating playlist after folder removal: {err}")
            print(f"Error details: {traceback.format_exc()}")

    def _handle_folder_addition(self, folder_path: str):
        """
        Update the playlist and next/previous songs when a new folder is added.
        Only applies when the playlist source is "all" (not playing from a specific album).

        Args:
            folder_path (str): The path of the folder being added.
        """
        try:
            # Get a fresh copy of the player state
            player_state = self.player_repository.get_player_state()
            if not player_state:
                return

            # Skip if playing from a specific album
            if player_state.playlist_source == "album":
                return

            # Skip if the playlist is empty
            if not player_state.playlist:
                return

            # Get fresh music data directly from database
            all_musics = self.music_repository.get_all_music(use_cache=False)
            if not all_musics:
                return

            # Update playlist with all tracks
            updated_playlist = [music.to_dict() for music in all_musics]
            if not updated_playlist:
                return

            # Update playlist
            player_state.playlist = updated_playlist

            # Save changes to database
            self.player_repository.update_player_state(player_state)
            self.player_state = player_state

        except Exception as err:
            import traceback
            print(f"Error updating playlist after folder addition: {err}")
            print(f"Error details: {traceback.format_exc()}")

