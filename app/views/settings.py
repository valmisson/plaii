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
    MainAxisAlignment,
    margin,
    OutlinedButton,
    Page,
    padding,
    Row,
    RoundedRectangleBorder,
    Text,
)

def settings_view(page: Page):
    def on_folder_picker_result(event: FilePickerResultEvent):
        folder_path = event.path

        has_path = [
            ctrl for ctrl in folder_paths.controls if ctrl.key == folder_path
        ]

        if folder_path and not has_path:
            add_folder_path(folder_path)

    def on_remove_folder_path(path):
        new_list = [
            ctrl for ctrl in folder_paths.controls if ctrl.key != path
        ]

        folder_paths.controls = new_list

        if len(folder_paths.controls) == 2:
            folder_paths.height = None

        folder_paths.update()

    def on_save(_):
        page.close(dialog)

    file_picker = FilePicker(
        on_result=on_folder_picker_result
    )

    def add_folder_path(path: str):
        folder_paths.controls.append(
            ListTile(
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
        )

        if len(folder_paths.controls) == 3:
            folder_paths.height = 180

        folder_paths.update()

    folder_paths = ListView(
        auto_scroll=True
    )

    dialog = AlertDialog(
        modal=True,
        bgcolor=Colors.GREY_900,
        shape=RoundedRectangleBorder(radius=8.0),
        title_padding=padding.only(top=5, right=15, bottom=0, left=25),
        content_padding=padding.only(top=25, right=25, bottom=35, left=25),
        title=Row(
            alignment=MainAxisAlignment.SPACE_BETWEEN,
            spacing=0,
            controls=[
                Text(
                    'Configurações',
                    color=Colors.WHITE,
                    size=16
                ),
                IconButton(
                    icon=Icons.CLOSE,
                    icon_color=Colors.WHITE70,
                    highlight_color=Colors.with_opacity(
                        0.2,
                        Colors.RED_ACCENT_200
                    ),
                    hover_color=Colors.TRANSPARENT,
                    padding=padding.all(0),
                    on_click=lambda _: page.close(dialog)
                )
            ]
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
                text='Salvar',
                color=Colors.WHITE,
                bgcolor=Colors.GREEN_500,
                style=ButtonStyle(
                    padding=padding.symmetric(horizontal=15),
                ),
                on_click=on_save
            )
        ]
    )

    page.overlay.append(file_picker)

    return dialog
