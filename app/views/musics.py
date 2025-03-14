from flet import (
    Column,
    Colors,
    ButtonStyle,
    Divider,
    Icons,
    IconButton,
    ListTile,
    ListView,
    MouseCursor,
    Page,
    OnScrollEvent,
    Row,
    RoundedRectangleBorder,
    Text,
    TextButton,
    WindowResizeEvent
)
from shared.utils import (
    format_time,
    get_music_title,
    get_music_artist,
    load_music_files,
    load_music_metadata
)

def musics_view(page: Page):
    musics_per_page = 15
    current_page = 0

    def load_musics():
        start = current_page * musics_per_page
        limit = start + musics_per_page

        musics = load_music_files(start, limit)

        return musics

    async def on_scroll_change(event: OnScrollEvent):
        nonlocal current_page

        is_final = int(len(list_view.controls) / musics_per_page) >= current_page

        try:
            if event.pixels == event.max_scroll_extent and is_final:
                current_page += 1
                list_view.controls.extend([
                    music_item(music) for music in load_musics()
                ])
                list_view.update()
        except Exception as err:
            print(f'Error ao processar o evento de rolagem: {err}')

    def on_resized_page(event: WindowResizeEvent):
        column.height = event.height - 120
        page.update()

    def music_item(file: str):
        music = load_music_metadata(file)

        if music is not None:
            return Column(
                spacing=0,
                controls=[
                    Divider(
                        height=1,
                        thickness=1,
                        leading_indent=4,
                        trailing_indent=4,
                        color=Colors.GREY_800,
                    ),
                    ListTile(
                        dense=True,
                        selected=False, # Select music playing
                        toggle_inputs=True,
                        text_color=Colors.WHITE,
                        icon_color=Colors.GREY_900,
                        hover_color=Colors.GREY_800,
                        selected_color=Colors.RED_ACCENT_200,
                        shape=RoundedRectangleBorder(4),
                        mouse_cursor=MouseCursor.BASIC,
                        leading=IconButton(
                            icon=Icons.PLAY_ARROW
                        ),
                        title=Text(
                            get_music_title(music),
                            size=16,
                        ),
                        subtitle=Row(
                            spacing=15,
                            controls=[
                                Text(
                                    get_music_artist(music),
                                    color=Colors.WHITE,
                                    size=14
                                ),
                                Row(
                                    controls=[
                                        Text(
                                            '-',
                                            size=14,
                                            color=Colors.WHITE,
                                        ),
                                        TextButton(
                                            content=Text(
                                                music.album,
                                                color=Colors.WHITE,
                                                size=14
                                            ),
                                            style=ButtonStyle(
                                                overlay_color=Colors.TRANSPARENT,
                                                padding=0
                                            )
                                        )
                                    ]
                                ) if music.album else Row(),
                            ]
                        ),
                        trailing=Text(
                            format_time(music.duration),
                            size=14,
                            color=Colors.WHITE
                        ),
                    )
                ]
        )

    musics = load_musics()

    list_view = ListView(
        expand=True,
        controls=[
            music_item(music) for music in musics
        ],
        on_scroll=on_scroll_change
    )

    column = Column(
        controls=[
            Text(
                'Todas as Música',
                color=Colors.WHITE,
                size=14
            ),
            Text(
                'Lista de musicas está vazia.',
                color=Colors.WHITE,
                size=16
            ) if not musics else list_view
        ]
    )

    page.on_resized = on_resized_page

    return column
