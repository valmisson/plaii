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

from models import AlbumsModel

def albums_view(page: Page):
    albums_model = AlbumsModel()
    albums_per_page = 20
    is_loaded = False

    def load_albums(start=0, limit=None):
        return albums_model.all_albums[start:limit]

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

    def on_subscribe_settings(_, status):
        if (status == 'new_folder' or status == 'remove_folder'):
            if page.get_control(list_view.uid):
                albums = load_albums(limit=albums_per_page)

                list_view.controls = [album_item(album) for album in albums] if albums else [list_empty]
                list_view.update()

    def album_item (album: dict):
        def on_hover(event: ControlEvent):
            is_visible = event.data == 'true'

            play_button.visible = is_visible
            container.bgcolor = Colors.with_opacity(
                0.4,
                Colors.GREY_800
            ) if is_visible else Colors.GREY_900
            container.update()

        play_button = IconButton(
            right=10,
            bottom=10,
            visible=False,
            icon=Icons.PLAY_ARROW,
            icon_color=Colors.GREY_900,
            bgcolor=Colors.RED_ACCENT_200
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
                        controls=[
                            Image(
                                border_radius=6,
                                cache_width=150,
                                cache_height=150,
                                src_base64=album.get('cover')
                            ),
                            play_button
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
            )
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
        height=470,
        scroll=ScrollMode.AUTO,
        vertical_alignment=CrossAxisAlignment.START,
        controls=[album_item(album) for album in albums] if albums else [list_empty],
        on_scroll=on_scroll_change
    )

    page.on_resized = on_resized_page

    page.pubsub.subscribe_topic('settings', on_subscribe_settings)

    return list_view
