from flet import Colors, Page
from ui.layout.appbar import pageAppBar

class WindowMain():
    def __init__(self, page: Page):
        page.bgcolor = Colors.GREY_900
        page.appbar = pageAppBar(page)
        page.padding = 0
        page.window.frameless = True
        page.window.width = 800
        page.window.height = 600
        page.window.focused = True
        page.window.center()

        page.update()
