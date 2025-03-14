from flet import (
    app,
    Colors,
    ControlEvent,
    Container,
    Page,
    padding
)

from layout.app_head import appbar
from layout.app_menu import navbar

from views.settings import settings_view
from views.musics import musics_view

class AppWindow():
    def __init__(self, page: Page):
        self.page = page

        page.appbar = appbar(page, self.on_settings_view)
        page.bgcolor = Colors.GREY_900
        page.padding = 0
        page.window.frameless = True
        page.window.width = 800
        page.window.height = 600
        page.window.focused = True
        page.window.center()

        self.views = Container(
            padding=padding.symmetric(
                horizontal=15
            )
        )

        # start with music view
        self.add_view(0)

        page.add(
            navbar(on_change=self.on_navbar_change),
            self.views
        )

        page.update()

    def add_view(self, index_view):
        self.views.content = None

        if index_view == 0:
            self.views.content = musics_view(self.page)

        self.page.update()

    def on_navbar_change(self, event: ControlEvent):
        index_view = int(event.data)
        self.add_view(index_view)

    def on_settings_view(self, _):
        self.page.open(settings_view(self.page))

if __name__ == '__main__':
    app(target=AppWindow)
