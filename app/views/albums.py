from flet import (
    Container,
    Colors,
    Column,
    ControlEvent,
    CrossAxisAlignment,
    FontWeight,
    Icons,
    IconButton,
    Image,
    OnScrollEvent,
    Page,
    Row,
    Text,
    TextOverflow,
    Stack,
    ScrollMode,
    WindowResizeEvent
)
from flet_audio import AudioState

from models import AlbumsModel, MusicsModel, PlayerModel

def albums_view(page: Page):
    albums_model = AlbumsModel()
    musics_model = MusicsModel()
    player_model = PlayerModel()

    albums_per_page = 20
    is_loaded = False

    album_play_cache = None

    def load_albums(start=0, limit=None):
        return albums_model.all_albums[start:limit]

    def load_album_playing():
        current_album = player_model.get_info('current_album')
        is_playing = player_model.get_info('is_playing') == 'True'

        if current_album:
            nonlocal album_play_cache
            album_play_cache = current_album if is_playing else None
            update_play_button(current_album, is_playing)

    def on_scroll_change(event: OnScrollEvent):
        nonlocal is_loaded

        try:
            if event.pixels < 2 and not is_loaded:
                is_loaded = True

                list_view.controls.extend(
                    [album_item(album) for album in load_albums(start=albums_per_page)]
                )
                list_view.update()
        except Exception as err:
            print(f'Error ao processar o evento de rolagem: {err}')

    def on_resized_page(event: WindowResizeEvent):
        list_view.height = event.height - 120
        page.update()

    def on_settings_subscribe(_, status):
        if (status == 'new_folder' or status == 'remove_folder'):
            if page.get_control(list_view.uid):
                albums = load_albums(limit=albums_per_page)

                list_view.controls = [album_item(album) for album in albums] if albums else [list_empty]
                list_view.update()

    def on_play_music_state_subscribe(_, data: dict):
        nonlocal album_play_cache

        audio_state = data.get('state')
        album_key = data.get('album_key')

        if audio_state == AudioState.PLAYING:
            album_play_cache = album_key
            update_play_button(album_key, is_playing=True)
        elif audio_state == AudioState.PAUSED and album_key:
            album_play_cache = album_key
            update_play_button(album_key, is_playing=False)
        else:
            album_play_cache = None
            update_play_button(None, is_playing=False)

    def on_album_play(album: str):
        current_album = player_model.get_info('current_album')
        is_paused = player_model.get_info('is_pause') == 'True'

        if current_album == album and is_paused:
            page.pubsub.send_all_on_topic('resume_music', {})
            return

        musics = musics_model.get_album_musics(album)
        music = musics[0] if musics else None

        page.pubsub.send_all_on_topic('play_music', {
            'music_to_play': music,
            'musics_list': musics
        })

    def on_pause_album(_):
        page.pubsub.send_all_on_topic('pause_music', {})

    def update_play_button(album_key=None, is_playing=False):
        for item in list_view.controls:
            if hasattr(item, 'content') and item.content.controls:
                stack = item.content.controls[0]
                play_btn = stack.controls[1]
                pause_btn = stack.controls[2]

                is_current_album = stack.data == album_key
                play_btn.visible = is_current_album and not is_playing
                pause_btn.visible = is_current_album and is_playing

                page.update()

    def album_item(album: dict):
        def on_hover(event: ControlEvent):
            is_visible = event.data == 'true'
            is_playing = album.get('name') == album_play_cache

            if not is_playing:
                play_button.visible = is_visible

            container.bgcolor = (
                Colors.with_opacity(0.4, Colors.GREY_800)
                if is_visible
                else Colors.GREY_900
            )
            container.update()

        play_button = IconButton(
            right=10,
            bottom=10,
            visible=False,
            icon=Icons.PLAY_ARROW,
            icon_color=Colors.GREY_900,
            bgcolor=Colors.WHITE,
            on_click=lambda _: on_album_play(album.get('name'))
        )

        pause_button = IconButton(
            right=10,
            bottom=10,
            visible=False,
            icon=Icons.PAUSE,
            icon_color=Colors.GREY_900,
            bgcolor=Colors.WHITE,
            on_click=on_pause_album
        )

        container = Container(
            padding=7,
            width=150,
            border_radius=6,
            on_hover=on_hover,
            content=Column(
                spacing=5,
                controls=[
                    Stack(
                        data=album.get('name'),
                        controls=[
                            Image(
                                border_radius=6,
                                cache_width=150,
                                cache_height=150,
                                src_base64=album.get('cover')
                            ),
                            play_button,
                            pause_button
                        ]
                    ),
                    Text(
                        album.get('name'),
                        size=14,
                        color=Colors.WHITE,
                        weight=FontWeight.W_600,
                        max_lines=2,
                        overflow=TextOverflow.ELLIPSIS,
                        tooltip=album.get('name') if len(album.get('name')) > 32 else '',
                    ),
                    Text(
                        album.get('artist'),
                        color=Colors.WHITE,
                        size=12
                    )
                ]
            ),
        )

        return container

    albums = load_albums(limit=albums_per_page)

    list_empty = Text(
        'Lista de albuns está vazia.',
        color=Colors.WHITE,
        size=16
    )

    list_view = Row(
        wrap=True,
        spacing=4,
        run_spacing=10,
        height=350,
        scroll=ScrollMode.AUTO,
        vertical_alignment=CrossAxisAlignment.START,
        controls=[album_item(album) for album in albums] if albums else [list_empty],
        on_scroll=on_scroll_change
    )

    load_album_playing()

    page.on_resized = on_resized_page

    page.pubsub.subscribe_topic('settings', on_settings_subscribe)
    page.pubsub.subscribe_topic('play_music_state', on_play_music_state_subscribe)

    return list_view
