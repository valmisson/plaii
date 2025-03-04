from flet import (
    Button,
    ButtonStyle,
    Colors,
    Container,
    Icon,
    Icons,
    IconButton,
    MouseCursor,
    MainAxisAlignment,
    Page,
    padding,
    RoundedRectangleBorder,
    Row,
    Text,
    WindowDragArea,
)

def appbar(page: Page):
    def on_minimize(_):
        page.window.minimized = True
        page.update()

    def on_maximize(_):
        page.window.maximized = page.window.width == 800.0
        page.update()

    def on_close(_):
        page.window.close()

    return WindowDragArea(
        Container(
            padding=padding.only(left=5),
            content=Row(
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    IconButton(
                        icon=Icons.MORE_HORIZ,
                        icon_size=24,
                        icon_color=Colors.WHITE,
                        highlight_color=Colors.TRANSPARENT,
                        hover_color=Colors.TRANSPARENT,
                        width=35,
                    ),
                    Text(
                        'Plaii',
                        size=16,
                        color=Colors.WHITE,
                    ),
                    Row(
                        spacing=0,
                        controls=[
                            Button(
                                bgcolor=Colors.GREY_900,
                                height=35,
                                width=45,
                                tooltip='Minimizar',
                                content=Icon(
                                    name=Icons.REMOVE,
                                    color=Colors.WHITE,
                                    size=20,
                                ),
                                style=ButtonStyle(
                                    shape=RoundedRectangleBorder(radius=0),
                                    overlay_color=Colors.GREY_800,
                                    mouse_cursor=MouseCursor.BASIC,
                                ),
                                on_click=on_minimize,
                            ),
                            Button(
                                bgcolor=Colors.GREY_900,
                                height=35,
                                width=45,
                                tooltip='Maximizar',
                                content=Icon(
                                    name=Icons.CROP_SQUARE,
                                    color=Colors.WHITE,
                                    size=18,
                                ),
                                style=ButtonStyle(
                                    shape=RoundedRectangleBorder(radius=0),
                                    overlay_color=Colors.GREY_800,
                                    mouse_cursor=MouseCursor.BASIC,
                                ),
                                on_click=on_maximize,
                            ),
                            Button(
                                bgcolor=Colors.GREY_900,
                                height=35,
                                width=45,
                                tooltip='Fechar',
                                content=Icon(
                                    name=Icons.CLOSE,
                                    color=Colors.WHITE,
                                    size=20,
                                ),
                                style=ButtonStyle(
                                    shape=RoundedRectangleBorder(radius=0),
                                    overlay_color=Colors.RED_700,
                                    mouse_cursor=MouseCursor.BASIC,
                                ),
                                on_click=on_close,
                            )
                        ]
                    )
                ]
            )
        )
    )
