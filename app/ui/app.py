"""
Main application window and UI initialization
"""
from flet import (
    Column,
    Container,
    ControlEvent,
    Page,
    ScrollbarTheme,
    Theme,
)

from app.config.settings import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT
)
from app.config.colors import AppColors
from app.data.repositories import AppRepository
from app.services.audio_service import AudioService
from app.services.notify_service import NotifyService
from app.ui.layout.app_bar import AppBar
from app.ui.layout.navigation import NavigationBar
from app.ui.layout.bottom_bar import BottomBar
from app.ui.views.musics_view import MusicsView
from app.ui.views.albums_view import AlbumsView
from app.ui.views.album_view import AlbumView
from app.ui.views.settings_view import SettingsView


class AppWindow:
    """Main application window class"""

    def __init__(self, page: Page):
        """
        Initialize the application window

        Args:
            page (Page): The Flet page object
        """
        self.page = page
        self.app_repository = AppRepository()
        self.app_state = self.app_repository.get_app_state()

        self.initialize_window()
        self.initialize_services()
        self.initialize_ui()

    def initialize_window(self):
        """Initialize window properties"""
        self.page.bgcolor = AppColors.BLACK
        self.page.padding = 0
        self.page.window.frameless = True
        self.page.window.width = DEFAULT_WINDOW_WIDTH
        self.page.window.height = DEFAULT_WINDOW_HEIGHT
        self.page.window.focused = True
        self.page.window.center()

        self.page.theme = Theme(
            scrollbar_theme=ScrollbarTheme(
                thickness=6,
                thumb_visibility=True,
                thumb_color=AppColors.GREY,
            ),
        )

    def initialize_services(self):
        """Initialize application services"""
        self.audio_service = AudioService(self.page)
        self.notify_service = NotifyService(self.page)

        self.page.pubsub.subscribe_topic(
            'navigation:album',
            self.on_navigation_album_subscribe
        )

    def initialize_ui(self):
        """Initialize the UI components"""
        # Set up app bar (top)
        self.page.appbar = AppBar(
            self.page,
            audio_service=self.audio_service,
            on_settings=self.on_settings_view
        )

        # create settings view
        self.settings_view = SettingsView(
            self.page,
            notify_service=self.notify_service,
        )

        # Create main navigation bar
        self.navigation_bar = NavigationBar(on_change=self.on_navbar_change)

        # Create main content container
        self.views_container = Container()

        # Add navigation bar and views container to page
        self.page.add(
            self.views_container
        )

        # Set up player bar (bottom)
        self.page.bottom_appbar = BottomBar(
            self.page,
            audio_service=self.audio_service,
            notify_service=self.notify_service
        )

        # Start with music view
        self.add_view(self.app_state.current_view)

        self.page.update()

    def add_view(self, index_view: int, data=None):
        """
        Switch to the specified view

        Args:
            index_view (int): Index of the view to display
        """
        self.views_container.content = None

        if index_view == 0:
            self.views_container.content = Column(
                controls=[
                    self.navigation_bar,
                    MusicsView(
                        page=self.page,
                        audio_service=self.audio_service
                    )
                ]
            )
        elif index_view == 1:
            self.views_container.content = Column(
                controls=[
                    self.navigation_bar,
                    AlbumsView(
                        page=self.page,
                        audio_service=self.audio_service
                    )
                ]
            )
        elif index_view == 2:
            self.views_container.content = AlbumView(
                page=self.page,
                audio_service=self.audio_service,
                album=data
            )

        self.views_container.update()

    def on_navbar_change(self, event: ControlEvent):
        """
        Handle navigation bar changes

        Args:
            event: Navigation change event
        """
        index_view = int(event.data)
        self.add_view(index_view)

        app_state = self.app_repository.get_app_state()
        app_state.current_view = index_view
        self.app_repository.update_app_state(app_state)

    def on_settings_view(self, _: ControlEvent):
        """
        Handle settings view action

        Args:
            _: Control event
        """
        self.page.open(self.settings_view)

    def on_navigation_album_subscribe(self, _, data):
        """
        Handle album navigation subscription

        Args:
            _: Control event
            data: Data from the event
        """
        index_view = data.get('index_view')
        self.add_view(index_view, data.get('album'))
