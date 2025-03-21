from flet import (
    Column,
    Colors,
    Container,
    ControlEvent,
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

from models import MusicsModel

def musics_view(page: Page):
    musics_model = MusicsModel()
    musics_per_page = 15
    current_page = 0

    def load_musics():
        start = current_page * musics_per_page
        limit = start + musics_per_page

        return musics_model.all_musics[start:limit]

    def update_musics_list():
        nonlocal current_page

        current_page = 0
        musics = load_musics()

        list_view.controls = [music_item(music) for music in musics] if musics else [list_empty]
        list_view.update()

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

    def on_subscribe_settings(_, status):
        if status == 'new_folder' or status == 'remove_folder':
            update_musics_list()

    def music_item(music: dict):
        if music is not None:
            def on_hover(event: ControlEvent):
                is_visible = event.data == 'true'

                icon_play.icon_color = Colors.WHITE if is_visible else Colors.GREY_900
                icon_play.update()

            icon_play = IconButton(
                icon=Icons.PLAY_ARROW,
            )

            return Container(
                on_hover=on_hover,
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
                                Colors.GREY_800
                            ),
                        ),
                        ListTile(
                            dense=True,
                            selected=False, # Select music playing
                            toggle_inputs=True,
                            text_color=Colors.WHITE,
                            icon_color=Colors.GREY_900,
                            hover_color=Colors.with_opacity(
                                0.4,
                                Colors.GREY_800
                            ),
                            selected_color=Colors.RED_ACCENT_200,
                            shape=RoundedRectangleBorder(4),
                            mouse_cursor=MouseCursor.BASIC,
                            leading=icon_play,
                            title=Text(
                                music.get('title'),
                                size=16,
                            ),
                            subtitle=Row(
                                spacing=15,
                                controls=[
                                    Text(
                                        music.get('artist'),
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
                                                    music.get('album'),
                                                    color=Colors.WHITE,
                                                    size=14
                                                ),
                                                style=ButtonStyle(
                                                    overlay_color=Colors.TRANSPARENT,
                                                    padding=0
                                                )
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            trailing=Text(
                                music.get('duration'),
                                size=14,
                                color=Colors.WHITE
                            ),
                        )
                    ]
            )
        )

    musics = load_musics()

    list_empty = Text(
        'Lista de musicas está vazia.',
        color=Colors.WHITE,
        size=16
    )

    list_view = ListView(
        expand=True,
        controls=[music_item(music) for music in musics] if musics else [list_empty],
        on_scroll=on_scroll_change
    )

    column = Column(
        height=page.height - 250,
        controls=[
            Text(
                'Todas as Música',
                color=Colors.WHITE,
                size=14
            ),
            list_view
        ]
    )

    page.on_resized = on_resized_page

    page.pubsub.subscribe_topic('settings', on_subscribe_settings)

    return column
