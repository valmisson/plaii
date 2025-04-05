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
from json import loads

from models import MusicsModel, PlayerModel

def musics_view(page: Page):
    musics_model = MusicsModel()
    player_model = PlayerModel()

    musics_per_page = 50
    current_page = 0

    list_item_cache = None
    music_key_cache = None

    def load_musics():
        start = current_page * musics_per_page
        limit = start + musics_per_page

        return musics_model.all_musics[start:limit]

    def load_music_playing():
        current_music = player_model.get_info('current_music')

        if current_music:
            current_music = loads(current_music)
            update_list_item_selected(current_music.get('filename'), is_playing=True)

    async def on_scroll_change(event: OnScrollEvent):
        nonlocal current_page

        total_pages = len(musics_model.all_musics) // musics_per_page
        is_final = current_page < total_pages

        try:
            if event.pixels >= (event.max_scroll_extent - 100) and is_final:
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
        if status == 'new_folder':
            update_list_item_selected(music_key_cache, is_playing=True)

    def on_play_music_state_subscribe(_, data: dict):
        audio_state = data.get('state')
        music_key = data.get('music_key')

        if list_item_cache and audio_state == AudioState.PLAYING:
            update_list_item_selected(music_key, is_playing=True)
        elif audio_state == AudioState.COMPLETED:
            update_list_item_selected(music_key, is_playing=False)

    def on_play_music(music: dict):
        music_key = music.get('filename')
        update_list_item_selected(music_key)

        page.pubsub.send_all_on_topic('play_music', {'music_to_play': music, 'musics_list': musics})

    def update_list_item_selected(music_key, is_playing=True):
        nonlocal list_item_cache
        nonlocal music_key_cache

        music_key_cache = music_key

        container = next((item for item in list_view.controls if item.key == music_key), None)

        if container and hasattr(container, 'content') and hasattr(container.content, 'controls'):
            list_item = container.content.controls[1]

            if list_item:
                if is_playing:
                    if list_item_cache:
                        list_item_cache.selected = False
                        list_item_cache.leading.icon_color = Colors.GREY_900

                    list_item_cache = list_item

                    list_item.selected = True
                    list_item.leading.icon = Icons.INSERT_CHART_OUTLINED
                    list_item.leading.icon_color = Colors.RED_ACCENT_200
                else:
                    list_item.selected = False
                    list_item.leading.icon = Icons.PLAY_ARROW
                    list_item.leading.icon_color = Colors.GREY_900

        page.update()

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
                on_click=lambda _: on_play_music(music)
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
                key=music.get('filename'),
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
        padding=padding.only(bottom=130),
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

    load_music_playing()

    page.on_resized = on_resized_page

    page.pubsub.subscribe_topic('settings', on_subscribe_settings)
    page.pubsub.subscribe_topic('play_music_state', on_play_music_state_subscribe)

    return column
