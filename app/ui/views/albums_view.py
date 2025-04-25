"""
Albums view component
"""
from flet import (
    ButtonStyle,
    Colors,
    Column,
    Container,
    CrossAxisAlignment,
    GridView,
    Icon,
    Icons,
    IconButton,
    Image,
    padding,
    Page,
    PopupMenuButton,
    PopupMenuItem,
    Row,
    Stack,
    Text,
    TextOverflow,
    OnScrollEvent,
)
from flet_audio import AudioState
from random import choice
from typing import List
from time import time

from app.config.settings import (
    DEFAULT_VIEW_HEIGHT,
    DEFAULT_PLACEHOLDER_IMAGE
)
from app.core.models import Album
from app.config.colors import AppColors
from app.data.repositories import AlbumRepository, PlayerRepository
from app.services.audio_service import AudioService
from app.services.metadata_service import MetadataService
from app.utils.image_utils import get_album_cover


class AlbumsView(Container):
    """View for displaying albums"""

    def __init__(self, page: Page, audio_service: AudioService):
        """
        Initialize the albums view

        Args:
            page (Page): The Flet page object
            audio_service (AudioService): The audio service for playback
        """
        super().__init__()

        self.page = page
        self.audio_service = audio_service
        self.album_repository = AlbumRepository()
        self.player_repository = PlayerRepository()

        # State
        self.albums: List[Album] = []
        self._player_state = self.player_repository.get_player_state()
        self._albums_per_page = 24
        self._current_page = 0
        self._last_scroll_time = 0
        self._is_loading_more = False
        self._scroll_debounce_ms = 200
        self._is_hovered = False

        # Track only the current playing album
        self._current_album_playing = None

        # Create the view
        self.padding = padding.only(top=20)
        self.expand = True
        self.content = self._build()

        # Subscribe to events
        self.page.pubsub.subscribe_topic('play:music', self.on_play_music_subscribe)
        self.page.pubsub.subscribe_topic('settings:folder:albums', self.on_settings_folder_subscribe)

    def _build(self):
        """Build the view"""
        self.albums = self.album_repository.get_all_albums()

        self._current_album_playing = self._player_state.current_album if self._player_state else None

        return self._create_albums_grid() if self.albums else self._create_empty_state()

    def _load_albums(self):
        """Load albums from the repository"""
        start = self._current_page * self._albums_per_page
        limit = start + self._albums_per_page

        return self.albums[start:limit] if self.albums else []

    def _create_albums_grid(self):
        """Build the albums grid view"""
        return GridView(
            height=DEFAULT_VIEW_HEIGHT,
            runs_count=6,
            spacing=10,
            run_spacing=2,
            child_aspect_ratio=0.698,
            padding=padding.symmetric(horizontal=10),
            controls=[self._create_album_card(album) for album in self._load_albums()],
            on_scroll=self.on_album_grid_scroll
        )

    def _create_album_card(self, album: Album):
        """
        Create a card for an album

        Args:
            album (Album): The album

        Returns:
            Card: The album card component
        """
        # Try to get album cover from first track
        album_cover = DEFAULT_PLACEHOLDER_IMAGE
        is_playing = self.audio_service.is_playing()
        is_current_album = self._player_state.current_album == album.name

        if album.tracks:
            try:
                metadata = MetadataService.load_music_metadata(
                    file=album.tracks[0].filename,
                    with_image=True
                )
                cover_data = get_album_cover(metadata)
                if cover_data:
                    album_cover = cover_data
            except Exception as err:
                print(f"Error loading album cover: {err}")

        # Create play button
        play_button = IconButton(
            icon=Icons.PAUSE if is_playing and is_current_album else Icons.PLAY_ARROW,
            icon_color=AppColors.BLACK,
            bgcolor=AppColors.WHITE,
            right=10,
            bottom=10,
            tooltip="Pausar" if is_playing else "Reproduzir",
            visible=is_playing and is_current_album,
            on_click=lambda _: self.on_play_album(album)
        )

        # Create context menu button
        context_menu = PopupMenuButton(
            left=0,
            bottom=5,
            visible=False,
            icon=Icons.MORE_VERT,
            bgcolor=AppColors.GREY,
            icon_color=AppColors.WHITE,
            shadow_color=AppColors.GREY_LIGHT_200,
            icon_size=20,
            tooltip="Mais opções",
            style=ButtonStyle(
                overlay_color=AppColors.TRANSPARENT,
            ),
            items=[
                PopupMenuItem(
                    content=Row(
                        controls=[
                            Icon(
                                Icons.PLAY_ARROW,
                                color=AppColors.WHITE
                            ),
                            Text(
                                "Reproduzir",
                                color=AppColors.WHITE
                            )
                        ]
                    ),
                    on_click=lambda _: self.on_play_album(album, resume=False)
                ),
                PopupMenuItem(
                    content=Row(
                        controls=[
                            Icon(
                                Icons.QUEUE_MUSIC,
                                color=AppColors.WHITE
                            ),
                            Text(
                                "Adicionar à fila",
                                color=AppColors.WHITE
                            )
                        ]
                    ),
                    on_click=lambda _: self.on_add_to_queue(album)
                ),
                PopupMenuItem(
                    content=Row(
                        controls=[
                            Icon(
                                Icons.ALBUM,
                                color=AppColors.WHITE
                            ),
                            Text(
                                "Mostrar o álbum",
                                color=AppColors.WHITE
                            )
                        ]
                    ),
                )
            ],
        )

        card = Container(
            data=album.name,
            border_radius=6,
            padding=6,
            content=Column(
                spacing=5,
                controls=[
                    Stack(
                        controls=[
                            Image(
                                src=DEFAULT_PLACEHOLDER_IMAGE,
                                src_base64=album_cover if album_cover != DEFAULT_PLACEHOLDER_IMAGE else None,
                                fit="cover",
                                border_radius=6,
                            ),
                            play_button,
                            context_menu
                        ]
                    ),
                    Column(
                        spacing=3,
                        controls=[
                            Text(
                                album.name,
                                size=15,
                                color=AppColors.WHITE,
                                tooltip=album.name if len(album.name) > 36 else None,
                                overflow=TextOverflow.ELLIPSIS,
                                max_lines=2
                            ),
                            Text(
                                album.artist,
                                size=13,
                                color=AppColors.GREY_LIGHT_300,
                                overflow=TextOverflow.ELLIPSIS,
                                max_lines=1
                            )
                        ]
                    )
                ]
            ),
            on_hover=lambda event: self.on_album_card_hover(event, album.name, play_button, context_menu, card),
        )

        return card

    def _create_empty_state(self):
        """Build the empty state message when no albums are available"""
        return Container(
            padding=padding.symmetric(vertical=60),
            content=Column(
                horizontal_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Icon(
                        Icons.MOTION_PHOTOS_OFF,
                        size=64,
                        color=AppColors.GREY
                    ),
                    Text(
                        "Nenhum álbum encontrado",
                        size=16,
                        color=AppColors.GREY_LIGHT_100
                    ),
                    Container(height=20)
                ]
            )
        )

    def _update_album_play_button(self, current_album: str, is_playing=False):
        """
        Update the play button state for the album
        Args:
            current_album (str): The name of the current album
            is_playing (bool): Whether the album is currently playing
        """
        # Skip processing if we don't have any content
        if not self.content or not hasattr(self.content, "controls") or not self.content.controls:
            return

        # Only hide previous album's play button if it's different from current
        if self._current_album_playing and self._current_album_playing != current_album:
            # Find previous album's card and hide its play button
            prev_album_card = next((card for card in self.content.controls
                                   if hasattr(card, "data") and card.data == self._current_album_playing), None)
            if prev_album_card:
                try:
                    play_button = prev_album_card.content.controls[0].controls[1]
                    play_button.visible = False
                    play_button.icon = Icons.PLAY_ARROW
                    play_button.tooltip = "Reproduzir"
                    play_button.update()
                except (IndexError, AttributeError):
                    pass

        # Only update current album if it exists
        if current_album:
            # Find current album's card and update its play button
            curr_album_card = next((card for card in self.content.controls
                                   if hasattr(card, "data") and card.data == current_album), None)
            if curr_album_card:
                try:
                    play_button = curr_album_card.content.controls[0].controls[1]
                    play_button.icon = Icons.PAUSE if is_playing else Icons.PLAY_ARROW
                    play_button.tooltip = "Pausar" if is_playing else "Reproduzir"
                    play_button.visible = True if self._is_hovered else is_playing
                    play_button.update()
                except (IndexError, AttributeError):
                    pass

        # Update current playing album reference
        self._current_album_playing = current_album if is_playing else None

    def _handle_folder_addition(self):
        """
        Handle addition of a folder by updating the album grid

        Args:
            folder_path (str): Path of the added folder
        """
        # Get updated albums including the new folder
        updated_albums = self.album_repository.get_all_albums(use_cache=False)

        # If no new albums were added, nothing to do
        if len(updated_albums) == len(self.albums):
            return

        # Update our internal albums list
        self.albums = updated_albums

        # Reset pagination state
        self._current_page = 0
        self._is_loading_more = False

        # If we were showing empty state before, rebuild completely
        if not hasattr(self.content, 'controls') or not isinstance(self.content, GridView):
            self.content = self._create_albums_grid()
            return

        # Update the grid with the first page of albums
        grid_view = self.content
        grid_view.controls = [self._create_album_card(album) for album in self._load_albums()]

        # Make sure we're not showing hover state on any album
        self._is_hovered = False

    def _handle_folder_removal(self):
        """
        Handle removal of a folder by updating the album grid
        """
        # Get updated albums without the removed folder
        updated_albums = self.album_repository.get_all_albums(use_cache=False)

        # If no change in albums, nothing to do
        if len(updated_albums) == len(self.albums):
            return

        # Update our internal albums list
        self.albums = updated_albums

        # Reset pagination state
        self._current_page = 0
        self._is_loading_more = False

        # If no content, just rebuild
        if not hasattr(self.content, 'controls'):
            self.content = self._build()
            return

        # If we have no albums left, show empty state
        if not self.albums:
            self.content = self._create_empty_state()
            return

        # Update the grid with the first page of albums
        grid_view = self.content
        grid_view.controls = [self._create_album_card(album) for album in self._load_albums()]

    def on_play_album(self, album: Album, resume=True):
        if not album or not album.tracks:
            return

        player_state = self.audio_service.player_repository.get_player_state()
        is_current_album = player_state.current_album == album.name

        # Pause if already playing
        if is_current_album and player_state.is_playing and resume:
            self.audio_service.pause()
        # Resume if paused
        elif is_current_album and player_state.is_paused and resume:
            self.audio_service.resume()
        # Play if not already playing
        else:
            track_to_play = album.tracks[0]

            if player_state.is_shuffle:
                # Shuffle the tracks if shuffle is enabled
                track_to_play = choice(album.tracks)

            # Set up playlist from album tracks and play first track
            all_tracks = [t.to_dict() for t in album.tracks]
            player_state.playlist = all_tracks
            player_state.playlist_source = "album"  # Mark that we're playing a specific album
            self.audio_service.player_repository.update_player_state(player_state)
            self.audio_service.load_music(track_to_play)
            self.audio_service.play()

    def on_add_to_queue(self, album: Album):
        """
        Add all album tracks to the playback queue

        Args:
            album (Album): Album to be added to the queue
        """
        # Ignore empty albums
        if not album or not album.tracks:
            return

        # Get player state and convert album tracks to dict format
        tracks_to_add = [t.to_dict() for t in album.tracks]
        player_state = self.audio_service.player_repository.get_player_state()

        # If player is inactive, play immediately
        if not player_state.is_playing and not player_state.playlist:
            # Start playing this album
            player_state.playlist = tracks_to_add
            player_state.playlist_source = "album"
            self.audio_service.player_repository.update_player_state(player_state)
            self.audio_service.load_music(album.tracks[0])
            self.audio_service.play()
            return

        # Otherwise, just append to the existing queue
        player_state.playlist.extend(tracks_to_add)
        self.audio_service.player_repository.update_player_state(player_state)
        self.page.update()

    def on_album_card_hover(self, event, album_name: str, play_button: IconButton, context_menu: PopupMenuButton, card: Container):
        """
        Handle hover event on album card

        Args:
            event: The hover event
            album_name (str): The name of the album
            play_button (IconButton): The play button
            context_menu (PopupMenuButton): The context menu button
            card (Container): The album card container
        """
        # Update the play button visibility
        is_visible = event.data == "true"
        is_current_album = self._current_album_playing == album_name

        play_button.visible = is_visible

        if is_current_album and self.audio_service.is_playing():
            play_button.visible = True

        # Update the context menu visibility
        context_menu.visible = is_visible

        # Update the card background color
        card.bgcolor = (
            Colors.with_opacity(0.4, AppColors.GREY)
            if is_visible
            else AppColors.BLACK
        )

        self.update()
        self._is_hovered = is_visible

    def on_album_grid_scroll(self, event: OnScrollEvent):
        """
        Handle scroll events to load more albums with improved performance

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
        scroll_threshold = event.max_scroll_extent * 0.5
        if event.pixels < scroll_threshold:
            return

        # Calculate if there's more content to load
        total_items = len(self.albums)
        loaded_items = (self._current_page + 1) * self._albums_per_page
        if loaded_items >= total_items:
            return  # No more items to load

        try:
            self._is_loading_more = True

            # Calculate the next batch of items to load
            self._current_page += 1
            start = self._current_page * self._albums_per_page
            end = min(start + self._albums_per_page, total_items)

            # Create all the album cards at once
            new_items = [
                self._create_album_card(album)
                for album in self.albums[start:end]
            ]

            # Get the Row that contains the album cards
            albums_grid = self.content

            # Batch update the Row with all new items at once
            albums_grid.controls.extend(new_items)
            albums_grid.update()
        except Exception as err:
            print(f'Error loading more albums: {err}')
        finally:
            self._is_loading_more = False

    def on_play_music_subscribe(self, _, data: dict):
        """
        Handle play music state updates

        Args:
            _: The subscription topic
            data: The event data
        """
        state = data.get('state')
        current_album = data.get('current_album')

        self._update_album_play_button(current_album, is_playing=state == AudioState.PLAYING)

    def on_settings_folder_subscribe(self, _, data: dict):
        """
        Handle folder change event from settings

        Args:
            _ (str): The subscription topic name
            data (dict): Event data with folder information
        """
        state = data.get('state')

        if state == 'remove':
            # Incrementally handle folder removal
            self._handle_folder_removal()
        elif state == 'new':
            # Incrementally handle folder addition
            self._handle_folder_addition()

        if self.page:
            self.update()
