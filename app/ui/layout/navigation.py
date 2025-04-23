"""
Navigation bar component
"""
from flet import (
    Container,
    margin,
    padding,
    Row,
    Tab,
    Tabs,
    Text,
    TextStyle,
)
from typing import Callable

from app.config.colors import AppColors
from app.data.repositories import AppRepository


class NavigationBar(Container):
    """Class for the navigation rail component"""

    def __init__(self, on_change: Callable):
        """
        Initialize the navigation bar

        Args:
            on_change (Callable): Callback function when navigation changes
        """
        super().__init__()

        self.app_repository = AppRepository()
        self.app_state = self.app_repository.get_app_state()

        self.on_tab_change = on_change

        # Configure container properties
        self.padding = padding.symmetric(horizontal=15)
        self.content = self._build()

    def _build(self):
        """Build the navigation bar UI"""
        return Row(
            spacing=10,
            controls=[
                Text(
                    'Browser',
                    color=AppColors.WHITE,
                    size=20,
                ),
                Container(
                    width=1.5,
                    height=15,
                    bgcolor=AppColors.GREY,
                    margin=margin.only(left=15, top=2)
                ),
                self._create_tabs()
            ]
        )

    def _create_tabs(self):
        """Create the navigation tabs"""
        return Tabs(
            selected_index=self.app_state.current_view,
            divider_color=AppColors.TRANSPARENT,
            indicator_color=AppColors.PRIMARY,
            indicator_tab_size=False,
            indicator_padding=padding.only(bottom=3, left=5, right=5),
            overlay_color=AppColors.TRANSPARENT,
            unselected_label_color=AppColors.WHITE,
            label_color=AppColors.WHITE,
            label_text_style=TextStyle(
                size=16
            ),
            tabs=[
                Tab(
                    text='Músicas'
                ),
                Tab(
                    text='Álbuns'
                )
            ],
            on_change=self.on_tab_change
        )
