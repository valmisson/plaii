"""
Music tracks view component
"""
from flet import (
    Colors,
    Column,
    Container,
    CrossAxisAlignment,
    Divider,
    Icon,
    Icons,
    IconButton,
    ListView,
    ListTile,
    MouseCursor,
    OnScrollEvent,
    padding,
    Page,
    RoundedRectangleBorder,
    Text,
)
from flet_audio import AudioState
from typing import List
from time import time

from app.config.colors import AppColors
from app.core.models import Music
from app.data.repositories import MusicRepository, PlayerRepository
from app.services.audio_service import AudioService


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
        self.player_repository = PlayerRepository()

        # State
        self.musics: List[Music] = []
        self._player_state = self.player_repository.get_player_state()
        self._loading = True
        self._current_music_playing = None
        self._is_playing = False
        self._musics_per_page = 50
        self._current_page = 0
        self._last_scroll_time = 0
        self._is_loading_more = False
        self._scroll_debounce_ms = 200

        # Create the view
        self.padding = padding.only(top=20)
        self.expand = True
        self.content = self._build()

        # Subscribe to events
        self.page.pubsub.subscribe_topic('play:music', self.on_play_music_subscribe)
        self.page.pubsub.subscribe_topic('settings:folder:musics', self.on_settings_folder_subscribe)

    def _build(self):
        """Build the view"""
        self.musics = self.music_repository.get_all_music()
        self._loading = False

        self._current_music_playing = self._player_state.current_music.get('filename') if self._player_state.current_music else None

        return self._build_music_list() if self.musics else self._build_empty_state()

    def _load_musics(self, start=0, limit=None) -> List[Music]:
        """
        Load music tracks from the repository
        Args:
            start (int): The starting index for pagination
            limit (int): The maximum number of music tracks to load
        Returns:
            List[Music]: A list of music tracks
        """
        return self.musics[start:limit] if self.musics else []

    def _build_music_list(self):
        """Build the music tracks table"""
        return Column(
            height=340,
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
                ListView(
                    expand=True,
                    padding=padding.symmetric(horizontal=15),
                    controls=[
                        self._create_music_row(music) for music in self._load_musics(limit=self._musics_per_page)
                    ]
                )
            ],
            on_scroll=self.on_scroll_change,
        )

    def _build_empty_state(self):
        """Build the empty state message when no music is available"""
        return Container(
            padding=padding.symmetric(vertical=60),
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

    def _create_music_row(self, music: Music):
        """
        Create a data row for a music track

        Args:
            music (Music): The music track

        Returns:
            ListTile: The data tile component
        """
        is_current = self._current_music_playing == music.filename

        # Define action based on play state
        play_or_pause_icon = Icons.INSERT_CHART_OUTLINED if is_current else Icons.PLAY_ARROW

        play_button = IconButton(
            icon=play_or_pause_icon,
            on_click=lambda _: self.on_music_play(music)
        )

        music_row_tile = ListTile(
            selected=is_current,
            toggle_inputs=True,
            text_color=AppColors.WHITE,
            icon_color=AppColors.BLACK,
            selected_color=AppColors.PRIMARY,
            shape=RoundedRectangleBorder(4),
            mouse_cursor=MouseCursor.BASIC,
            content_padding=padding.only(left=5, right=25),
            hover_color=Colors.with_opacity(
                0.4,
                AppColors.GREY
            ),
            leading=play_button,
            title=Text(
                music.title,
                size=16,
            ),
            subtitle=Text(
                f"{music.artist} - {music.album}",
                size=14,
                color=AppColors.WHITE_ACCENT
            ),
            trailing=Text(
                music.duration,
                size=14,
                color=AppColors.WHITE
            ),
        )

        return Container(
            key=music.filename,
            content=Column(
                spacing=0,
                controls=[
                    Divider(
                        height=1,
                        thickness=1,
                        leading_indent=4,
                        trailing_indent=4,
                        color=Colors.with_opacity(
                            0.4,
                            AppColors.GREY
                        ),
                    ),
                    music_row_tile
                ]
            ),
            on_hover=lambda _: self.on_hover_music_row(
                is_visible=_.data == 'true',
                play_button=play_button,
                music_row_tile=music_row_tile
            ),
        )

    def _update_music_selected(self, current_music: str, is_playing=True):
        """
        Update the selected music row

        Args:
            current_music (str): The key of the selected music
            is_playing (bool, optional): Whether the music is playing. Defaults to True.
        """
        # Check if content is a Column (which has 'controls')
        if hasattr(self.content, 'controls'):
            # Get the list view that contains the music rows
            list_view = self.content.controls[1] if len(self.content.controls) > 1 else None
        else:
            list_view = None

        if not self.musics or not list_view:
            return

        # Find previously selected item and target item in one pass
        currently_selected = None
        target_item = None

        for item in list_view.controls:
            if item.key == current_music:
                target_item = item

            list_tile = item.content.controls[1]
            if list_tile.selected:
                currently_selected = item

            # If we found both items, we can stop searching
            if currently_selected and target_item:
                break

        # If currently selected is different from target, unselect it
        if currently_selected and currently_selected.key != current_music:
            list_tile = currently_selected.content.controls[1]
            list_tile.selected = False
            list_tile.leading.icon = Icons.PLAY_ARROW
            list_tile.leading.icon_color = AppColors.BLACK

        # Select the target item if found
        if target_item:
            list_tile = target_item.content.controls[1]
            list_tile.selected = True

            if is_playing:
                list_tile.leading.icon = Icons.INSERT_CHART_OUTLINED
                list_tile.leading.icon_color = AppColors.PRIMARY

        self.update()

    def _handle_folder_addition(self, folder_path: str):
        """
        Handle addition of a folder by incrementally updating the UI

        Args:
            folder_path (str): Path of the added folder
        """
        # Refresh our internal music list with fresh data from repository
        self.musics = self.music_repository.get_all_music(use_cache=False)

        # Reset pagination state
        self._current_page = 0
        self._is_loading_more = False

        # If we were showing empty state, rebuild the whole view
        if not hasattr(self.content, 'controls') or len(self.content.controls) < 2:
            self.content = self._build()
            return

        # Get the list view that contains the music rows
        list_view = self.content.controls[1]

        # Find the new music files from this folder
        new_music = [music for music in self.musics if music.filename.startswith(folder_path)]

        if new_music:
            # Clear the current controls and repopulate
            list_view.controls = [
                self._create_music_row(music)
                for music in self._load_musics(limit=self._musics_per_page)
            ]

    def _handle_folder_removal(self, folder_path: str):
        """
        Handle removal of a folder by incrementally updating the UI

        Args:
            folder_path (str): Path of the removed folder
        """
        # First update our internal music list
        self.musics = self.music_repository.get_all_music(use_cache=False)

        # Reset pagination state
        self._current_page = 0
        self._is_loading_more = False

        # Get the list view that contains the music rows
        if not hasattr(self.content, 'controls') or len(self.content.controls) < 2:
            # If view structure isn't as expected, just rebuild
            self.content = self._build()
            return

        list_view = self.content.controls[1]

        # Remove items from the list view that belong to this folder
        list_view.controls = [
            item for item in list_view.controls
            if not (hasattr(item, 'key') and item.key.startswith(folder_path))
        ]

        # If no items left, show empty state
        if not self.musics:
            self.content = self._build_empty_state()
        elif not list_view.controls:
            # If visible list is empty, reload the first page
            list_view.controls = [
                self._create_music_row(music)
                for music in self._load_musics(limit=self._musics_per_page)
            ]

    def on_hover_music_row(self, is_visible: bool, play_button: IconButton, music_row_tile: ListTile):
        if music_row_tile.selected:
            play_button.icon = Icons.PLAY_ARROW if is_visible else Icons.INSERT_CHART_OUTLINED
            play_button.update()
            return

        play_button.icon = Icons.PLAY_ARROW
        play_button.icon_color = AppColors.WHITE if is_visible else AppColors.BLACK
        play_button.update()

    def on_scroll_change(self, event: OnScrollEvent):
        """
        Handle scroll events to load more music tracks with improved performance

        This implementation uses:
        1. Time-based debouncing to limit processing frequency
        2. Loading lock to prevent concurrent operations
        3. Batch processing of items for better performance
        4. Pre-calculation of visible content needs
        """
        # Debounce scroll events - only process every N milliseconds
        current_time = time() * 1000  # Convert to milliseconds
        if current_time - self._last_scroll_time < self._scroll_debounce_ms:
            return

        self._last_scroll_time = current_time

        # Prevent concurrent loading operations
        if self._is_loading_more:
            return

        # Check if we need to load more content
        # Load when user is within 20% of the bottom
        scroll_threshold = event.max_scroll_extent * 0.8
        if event.pixels < scroll_threshold:
            return

        # Calculate if there's more content to load
        total_items = len(self.musics)
        loaded_items = (self._current_page + 1) * self._musics_per_page
        if loaded_items >= total_items:
            return  # No more items to load

        try:
            self._is_loading_more = True

            # Calculate the next batch of items to load
            start = loaded_items  # Start from where we left off
            end = min(loaded_items + self._musics_per_page, total_items)
            self._current_page += 1

            # Create all the music rows at once
            new_items = [
                self._create_music_row(music)
                for music in self.musics[start:end]
            ]

            # Get the ListView that contains the music rows
            list_view = self.content.controls[1]

            # Batch update the ListView with all new items at once
            list_view.controls.extend(new_items)
            list_view.update()
        except Exception as err:
            print(f'Error loading more music: {err}')
        finally:
            self._is_loading_more = False

    def on_music_play(self, music: Music):
        """
        Handle click on a music track

        Args:
            music (Music): The music track that was clicked
        """
        all_musics = [m.to_dict() for m in self._load_musics()]
        player_state = self.audio_service.player_repository.get_player_state()
        player_state.playlist = all_musics
        player_state.playlist_source = "all"  # Mark that we're playing from all songs
        self.audio_service.player_repository.update_player_state(player_state)
        self.audio_service.load_music(music)
        self.audio_service.play()

    def on_play_music_subscribe(self, _, data: dict):
        """
        Handle music playback state changes

        Args:
            _ (str): The subscription topic name
            data: Event data with state information
        """
        state = data.get('state')
        current_music = data.get('current_music')

        if current_music:
            self._current_music_playing = current_music
            self._is_playing = state == AudioState.PLAYING

            # Update the view to reflect state changes
            self._update_music_selected(current_music)

    def on_settings_folder_subscribe(self, _, data: dict):
        """
        Handle changes in the settings folder state

        Args:
            _ (str): The subscription topic name
            data: Event data with folder path
        """
        state = data.get('state')
        folder_path = data.get('folder_path')

        if state == 'remove':
            # Incrementally remove music files from the specified folder
            self._handle_folder_removal(folder_path)
        elif state == 'new':
            # Incrementally add music files from the specified folder
            self._handle_folder_addition(folder_path)

        if self.page:
            self.update()
