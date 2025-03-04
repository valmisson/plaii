from flet import app, Colors, Column, ControlEvent, Page
from layout.app_head import appbar
from layout.app_menu import navbar

class AppWindow():
    def __init__(self, page: Page):
        page.appbar = appbar(page)
        page.bgcolor = Colors.GREY_900
        page.padding = 0
        page.window.frameless = True
        page.window.width = 800
        page.window.height = 600
        page.window.focused = True
        page.window.center()

        page.add(
            Column([
                navbar(on_change=self.on_navbar_change)
            ])
        )

        page.update()

    def on_navbar_change(self, event: ControlEvent):
        view_index = event.data

if __name__ == '__main__':
    app(target=AppWindow)
