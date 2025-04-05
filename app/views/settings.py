from flet import (
    AlertDialog,
    Button,
    ButtonStyle,
    Colors,
    Container,
    ExpansionTile,
    FilePicker,
    FilePickerResultEvent,
    Icon,
    Icons,
    IconButton,
    ListTile,
    ListView,
    margin,
    MainAxisAlignment,
    OutlinedButton,
    Page,
    padding,
    ProgressRing,
    Row,
    RoundedRectangleBorder,
    Stack,
    Text,
)

from shared import load_music_files
from models import FoldersModel, MusicsModel, AlbumsModel

def settings_view(page: Page):
    folders_model = FoldersModel()
    musics_model = MusicsModel()
    albums_model = AlbumsModel()
    folder_paths_status = []
    folder_paths_to_add = []
    folder_paths_to_remove = []

    def save_musics():
        add_loading_message()

        if len(folder_paths_to_add):
            musics = load_music_files(folder_paths_to_add)
            musics_model.save_musics(musics)
            albums_model.save_albums(musics)

        remove_loading_message()
        folder_paths_to_add.clear()

    def remove_musics():
        add_loading_message()

        for folder_path in folder_paths_to_remove:
            musics_model.remove_musics(folder_path)
            albums_model.remove_albums(folder_path)

        remove_loading_message()
        folder_paths_to_remove.clear()

    def on_finish(_):
        page.close(dialog)

        for status in folder_paths_status:
            if status == 'new_folder':
                save_musics()
                page.pubsub.send_all_on_topic('settings', 'new_folder')
            elif status == 'remove_folder':
                remove_musics()
                page.pubsub.send_all_on_topic('folder_removed', None)
                page.pubsub.send_all_on_topic('settings', 'remove_folder')

        folder_paths_status.clear()


    def on_folder_picker_result(event: FilePickerResultEvent):
        folder_path = event.path

        has_path = [
            ctrl for ctrl in folder_paths.controls if ctrl.key == folder_path
        ]

        if folder_path and not has_path:
            folders_model.save_folder_path(folder_path)

            folder_paths.controls.append(
                folder_path_item(folder_path)
            )

            if len(folder_paths.controls) >= 3:
                folder_paths.auto_scroll = True
                folder_paths.height = 180

            folder_paths_to_add.append(folder_path)
            folder_paths_status.append('new_folder')
            folder_paths.update()

    def on_remove_folder_path(folder_path):
        nonlocal folder_paths_status

        folders_model.remove_folder_path(folder_path)
        folder_paths_to_remove.append(folder_path)

        new_folder_list = [
            ctrl for ctrl in folder_paths.controls if ctrl.key != folder_path
        ]

        folder_paths.controls = new_folder_list

        if len(folder_paths.controls) == 2:
            folder_paths.auto_scroll = False
            folder_paths.height = None

        folder_paths_status.append('remove_folder')
        folder_paths.update()

    def add_loading_message():
        page.add(loading_message)
        page.update()

    def remove_loading_message():
        if loading_message in page.controls:
            page.remove(loading_message)
            page.update()

    def folder_path_item(path: str):
        return ListTile(
            key=path,
            content_padding=0,
            title=Text(
                path,
                color=Colors.WHITE,
            ),
            trailing=IconButton(
                icon=Icons.CLOSE,
                icon_color=Colors.WHITE70,
                highlight_color=Colors.with_opacity(
                    0.2,
                    Colors.RED_ACCENT_200
                ),
                hover_color=Colors.TRANSPARENT,
                padding=padding.all(0),
                on_click=lambda _: on_remove_folder_path(path)
            )
        )

    file_picker = FilePicker(
        on_result=on_folder_picker_result
    )

    folder_paths = ListView(
        controls=[
            folder_path_item(path) for path in folders_model.folder_paths
        ]
    )

    dialog = AlertDialog(
        modal=True,
        bgcolor=Colors.GREY_900,
        shape=RoundedRectangleBorder(radius=8.0),
        content_padding=padding.only(top=35, right=25, bottom=35, left=25),
        title=Text(
            'Configurações',
            color=Colors.WHITE,
            size=16
        ),
        content=ExpansionTile(
            text_color=Colors.WHITE,
            icon_color=Colors.WHITE70,
            bgcolor=Colors.GREY_800,
            collapsed_text_color=Colors.WHITE,
            collapsed_bgcolor=Colors.GREY_800,
            collapsed_icon_color=Colors.WHITE70,
            collapsed_shape=RoundedRectangleBorder(radius=4.0),
            shape=RoundedRectangleBorder(radius=4.0),
            controls_padding=padding.only(top=10, right=10, bottom=10, left=15),
            tile_padding=padding.symmetric(vertical=5, horizontal=15),
            leading=Icon(
                name=Icons.FOLDER_OUTLINED,
                color=Colors.WHITE
            ),
            title=Row(
                spacing=55,
                controls=[
                    Text('Locais'),
                    Container(
                        margin=margin.only(right=20),
                        content=OutlinedButton(
                            text='Adicionar Pasta',
                            style=ButtonStyle(
                                color=Colors.WHITE,
                                shape=RoundedRectangleBorder(radius=4.0)
                            ),
                            on_click=lambda _: file_picker.get_directory_path()
                        )
                    )
                ]
            ),
            controls=[
                folder_paths
            ]
        ),
        actions=[
            Button(
                text='Finalizar',
                color=Colors.WHITE,
                bgcolor=Colors.GREEN_500,
                style=ButtonStyle(
                    padding=padding.symmetric(horizontal=15),
                ),
                on_click=on_finish
            )
        ]
    )

    loading_message = Stack(
        controls=[
            Container(
                top=-170,
                width=page.width,
                bgcolor=Colors.GREY_900,
                padding=padding.symmetric(vertical=10),
                content=Row(
                    alignment=MainAxisAlignment.CENTER,
                    controls=[
                        ProgressRing(
                            width=15,
                            height=15,
                            stroke_width=2,
                            color=Colors.RED_ACCENT_200,
                        ),
                        Text(
                            'Indexando bibliotecas...',
                            size=14,
                            color=Colors.WHITE,
                        )
                    ]
                )
            )
        ]
    )

    if len(folder_paths.controls) >= 3:
        folder_paths.height = 180

    page.add(file_picker)

    return dialog
