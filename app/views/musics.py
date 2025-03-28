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
    padding,
    OnScrollEvent,
    Row,
    RoundedRectangleBorder,
    Text,
    TextButton,
    WindowResizeEvent
)
from flet_audio import AudioState

from models import MusicsModel

def musics_view(page: Page):
    musics_model = MusicsModel()
    musics_per_page = 15
    current_page = 0

    list_item_playing = None

    def load_musics():
        start = current_page * musics_per_page
        limit = start + musics_per_page

        return musics_model.all_musics[start:limit]

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
        if (status == 'new_folder' or status == 'remove_folder'):
            nonlocal current_page, musics

            current_page = 0
            musics = load_musics()

            if page.get_control(list_view.uid):
                list_view.controls = [music_item(music) for music in musics] if musics else [list_empty]
                list_view.update()

    def on_play_music_state_subscribe(_, audio_state: AudioState):
        if list_item_playing and audio_state == AudioState.PLAYING:
            update_list_item_selected(list_item_playing, is_playing=True)
        elif audio_state == AudioState.COMPLETED:
            update_list_item_selected(list_item_playing, is_playing=False)

    def on_play_music(music: dict, list_item: ListTile):
        update_list_item_selected(list_item)

        page.pubsub.send_all_on_topic('play_music', {'music_to_play': music, 'musics_list': musics})

    def update_list_item_selected(list_item: ListTile, is_playing=True):
        nonlocal list_item_playing

        if list_item and is_playing:
            if list_item_playing:
                list_item_playing.selected = False
                list_item_playing.leading.icon_color = Colors.GREY_900

            list_item_playing = list_item

            list_item_playing.selected = True
            list_item_playing.leading.icon = Icons.INSERT_CHART_OUTLINED
            list_item_playing.leading.icon_color = Colors.RED_ACCENT_200
        else:
            list_item_playing.selected = False
            list_item_playing.leading.icon = Icons.PLAY_ARROW
            list_item_playing.leading.icon_color = Colors.GREY_900

        list_item_playing.update()

    def music_item(music: dict):
        if music is not None:
            def on_hover(event: ControlEvent):
                is_visible = event.data == 'true'

                if list_item.selected:
                    icon_play.icon = Icons.PLAY_ARROW if is_visible else Icons.INSERT_CHART_OUTLINED
                    icon_play.update()
                    return

                icon_play.icon = Icons.PLAY_ARROW
                icon_play.icon_color = Colors.WHITE if is_visible else Colors.GREY_900
                icon_play.update()

            icon_play = IconButton(
                icon=Icons.PLAY_ARROW,
                highlight_color=Colors.with_opacity(
                    0.1,
                    Colors.GREY_600
                ),
                on_click=lambda _: on_play_music(music, list_item)
            )

            list_item = ListTile(
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
                content_padding=padding.only(left=5, right=25),
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
                        list_item
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
        height=355,
        controls=[
            Text(
                'Todas as Músicas',
                color=Colors.WHITE,
                size=14
            ),
            list_view
        ]
    )

    page.on_resized = on_resized_page

    page.pubsub.subscribe_topic('settings', on_subscribe_settings)
    page.pubsub.subscribe_topic('play_music_state', on_play_music_state_subscribe)

    return column
