from flet import (
    Colors,
    Container,
    margin,
    padding,
    Row,
    Tab,
    Tabs,
    Text,
    TextStyle
)

def navbar(on_change):
    return Container(
        padding=padding.symmetric(horizontal=15),
        content=Row(
            spacing=10,
            controls=[
                Text(
                    'Browser',
                    color=Colors.WHITE,
                    size=20,
                ),
                Container(
                    width=1.5,
                    height=15,
                    bgcolor=Colors.GREY_800,
                    margin=margin.only(left=15, top=2)
                ),
                Tabs(
                    selected_index=0,
                    divider_color=Colors.TRANSPARENT,
                    indicator_color=Colors.RED_ACCENT_200,
                    indicator_tab_size=False,
                    indicator_padding=padding.only(bottom=3, left=5, right=5),
                    overlay_color=Colors.TRANSPARENT,
                    unselected_label_color=Colors.WHITE,
                    label_color=Colors.WHITE,
                    label_text_style=TextStyle(
                        size=16
                    ),
                    tabs=[
                        Tab(
                            text='Musicas'
                        ),
                        Tab(
                            text='Albuns'
                        )
                    ],
                    on_change=on_change
                )
            ]
        )
    )
