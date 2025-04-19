"""
Settings view component
"""
from flet import (
    AlertDialog,
    Button,
    ButtonStyle,
    Colors,
    Column,
    Container,
    FilePicker,
    FilePickerResultEvent,
    Icons,
    IconButton,
    ListTile,
    ListView,
    MainAxisAlignment,
    padding,
    Page,
    Row,
    RoundedRectangleBorder,
    Text,
    TextOverflow,
)

from app.config.colors import AppColors
from app.core.models import MusicFolder
from app.data.repositories import FolderRepository, MusicRepository
from app.services.metadata_service import MetadataService
from app.services.notify_service import NotifyService


class SettingsView(AlertDialog):
    def __init__(self, page: Page, notify_service: NotifyService):
        """
        Initialize the settings view

        Args:
            page (Page): The Flet page object
        """
        super().__init__()

        self.page = page
        self.notify_service = notify_service
        self.folder_repository = FolderRepository()
        self.music_repository = MusicRepository()

        # Create the view
        self.bgcolor=AppColors.BLACK
        self.shape=RoundedRectangleBorder(radius=8.0)
        self.title=self._create_dialog_title()
        self.actions=self._create_dialog_actions()
        self.content=self._build()

        # File picker for selecting folders - avoid adding duplicates
        self.file_picker = self._get_or_create_file_picker()

    def _build(self):
        """Build the view"""
        folders = self.folder_repository.get_all_folders()

        return Container(
            width=600,
            height=400,
            content=Column(
                spacing=25,
                controls=[
                    self._create_folders_section(folders),
                    self._create_about_section(),
                ]
            ),
        )

    def _create_dialog_title(self):
        """Create dialog title"""
        return Text(
            "Configurações",
            color=AppColors.WHITE,
        )

    def _create_dialog_actions(self):
        """Create dialog actions"""
        return [
            Button(
                "Fechar",
                color=AppColors.WHITE,
                bgcolor=AppColors.GREEN,
                style=ButtonStyle(
                    padding=padding.symmetric(horizontal=15),
                ),
                on_click=lambda _: self.on_dialog_close()
            ),
        ]

    def _get_or_create_file_picker(self):
        """
        Get an existing file picker from the page or create a new one if none exists

        Returns:
            FilePicker: A file picker instance
        """
        # Check if there's already a FilePicker in the page
        for control in self.page.controls:
            if isinstance(control, FilePicker):
                return control

        # Create and add a new FilePicker if none exists
        file_picker = FilePicker(on_result=self.on_folder_picked)
        self.page.add(file_picker)
        return file_picker

    def _create_folders_section(self, folders):
        """Create folders section"""
        return Column(
            spacing=10,
            controls=[
                Row(
                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        Text(
                            "Pastas de Música",
                            size=20,
                            weight="bold",
                            color=AppColors.WHITE
                        ),
                        IconButton(
                            icon=Icons.ADD,
                            icon_color=AppColors.WHITE,
                            tooltip="Adicionar Pasta",
                            hover_color=AppColors.TRANSPARENT,
                            highlight_color=Colors.with_opacity(0.1, AppColors.GREY),
                            on_click=lambda _: self.file_picker.get_directory_path()
                        )
                    ]
                ),
                Text(
                    "Gerencie as pastas de música que o Plaii utiliza para buscar suas músicas.",
                    color=AppColors.GREY_LIGHT_200,
                    size=14
                ),
                Container(
                    width=600,
                    padding=padding.only(left=15, right=10, top=5, bottom=10),
                    border_radius=8,
                    height=140 if len(folders) > 3 else None,
                    bgcolor=Colors.with_opacity(
                        0.4,
                        AppColors.GREY
                    ),
                    content=ListView(
                        controls=[
                            self._create_folder_list(folder) for folder in folders
                        ]
                    ) if folders else Text(
                        "Nenhuma pasta adicionada. Adicione pastas clicando no botão + acima.",
                        color=AppColors.GREY_LIGHT_200
                    ),
                )
            ]
        )

    def _create_folder_list(self, folder):
        """Create folder list"""
        return ListTile(
            data=folder.path,
            content_padding=0,
            height=40,
            title=Text(
                folder.path,
                size=14,
                color=Colors.WHITE,
                max_lines=1,
                no_wrap=True,
                overflow=TextOverflow.ELLIPSIS,
            ),
            trailing=IconButton(
                icon=Icons.DELETE,
                icon_color=AppColors.RED,
                icon_size=20,
                highlight_color=Colors.with_opacity(
                    0.2,
                    AppColors.PRIMARY
                ),
                hover_color=Colors.TRANSPARENT,
                padding=padding.all(0),
                tooltip="Remover",
                on_click=lambda _, f=folder: self.on_remove_folder(f)
            )
        )

    def _create_about_section(self):
        """Create about section"""
        return Column(
            spacing=10,
            controls=[
                Text(
                    "Sobre", size=20,
                    weight="bold",
                    color=AppColors.WHITE
                ),
                Container(height=5),
                Text(
                    "Plaii - Reprodutor de música",
                    color=AppColors.WHITE
                ),
                Text(
                    "Versão 0.1.0",
                    color=AppColors.GREY_LIGHT_200
                ),
                Text(
                    "Desenvolvido com Flet e Python",
                    color=AppColors.GREY_LIGHT_200,
                    size=12
                ),
            ]
        )

    def _get_folder_list_container_safely(self):
        """
        Safely get the folder list container with proper null checks

        Returns:
            tuple: (folder_container, current_content) or (None, None) if not found
        """
        try:
            # Navigate through UI hierarchy to find the folder container
            column = self.content.content
            folder_section = column.controls[0]
            folder_container = folder_section.controls[2]
            current_content = folder_container.content

            return folder_container, current_content
        except (AttributeError, IndexError):
            # Return None values if any part of the navigation fails
            return None, None

    def _update_folder_list_after_add(self, folder: MusicFolder):
        """Update the folder list after adding a new folder"""
        folder_container, folder_list = self._get_folder_list_container_safely()
        if not folder_container:
            return

        # Create the folder list item for the new folder
        new_folder_item = self._create_folder_list(folder)

        if isinstance(folder_list, ListView):
            # If we already have a ListView, append the new folder to existing controls
            folder_list.controls.append(new_folder_item)

            # Adjust container height if needed based on number of folders
            if len(folder_list.controls) > 3:
                folder_container.height = 140
                folder_list.auto_scroll = True
            else:
                folder_container.height = None
                folder_list.auto_scroll = False
        else:
            # If we previously had the empty state message, replace it with a new ListView
            folder_container.content = ListView(
                controls=[new_folder_item],
            )

        # Update the UI
        self.update()
        folder_list.auto_scroll = False

    def _update_folder_list_after_removal(self, folder_path: str):
        """
        Update the folder list UI after a folder has been removed

        Args:
            folder_path (str): Path of the removed folder
        """
        folder_container, folder_list = self._get_folder_list_container_safely()
        if not folder_container:
            return

        if isinstance(folder_list, ListView):
            # Remove the folder item from the list
            new_folder_list = [
                ctrl for ctrl in folder_list.controls if ctrl.data != folder_path
            ]

            # Update UI based on whether there are any folders left
            if new_folder_list:
                folder_list.controls = new_folder_list
                # If we now have 3 or fewer items, adjust the height
                if len(new_folder_list) <= 3:
                    folder_container.height = None
            else:
                # Switch to empty state message when no folders left
                folder_container.content = Text(
                    "Nenhuma pasta adicionada. Adicione pastas clicando no botão + acima.",
                    color=AppColors.GREY_LIGHT_200
                )

            self.update()

    def _send_settings_topic(self, state: str, folder_path: str):
        """
        Notify all view about settings:folder update

        Args:
            state (str): State of the folder (new, remove)
            folder_path (str): Path of the folder
        """
        status = {'state': state, 'folder_path': folder_path}

        self.page.pubsub.send_all_on_topic('settings:folder:player', status)
        self.page.pubsub.send_all_on_topic('settings:folder:musics', status)
        self.page.pubsub.send_all_on_topic('settings:folder:albums', status)

    def on_remove_folder(self, folder: MusicFolder):
        """Handle removal of a music folder"""
        try:
            # Get all music tracks to check which ones belong to the folder
            all_music = self.music_repository.get_all_music()

            # Filter music tracks that belong to the folder being removed
            folder_music = [music for music in all_music if music.filename.startswith(folder.path)]

            # Update the folder list in the UI
            self._update_folder_list_after_removal(folder.path)

            # Show notification while processing
            self.notify_service.show()

            # Remove music tracks from repository
            for music in folder_music:
                self.music_repository.delete_music(music.filename)

            # Remove folder from repository
            self.folder_repository.delete_folder(folder.path)
        except Exception as e:
            print(f"Error removing folder: {e}")
        finally:
            # Hide the notification
            self.notify_service.hide()

            # Notify all views about the folder removal
            self._send_settings_topic('remove', folder.path)

    def on_folder_picked(self, e: FilePickerResultEvent):
        """
        Handle folder selection for adding music

        Args:
            e (FilePickerResultEvent): The folder picker event
        """
        if not e.path:
            return

        folder_path = e.path

        try:
            # Add folder to repositories
            folder_name = MetadataService.extract_folder_name(folder_path)
            folder_exists = self.folder_repository.folder_exists(folder_path)

            if not folder_exists:
                # Add new folder and scan for music
                new_folder = MusicFolder(path=folder_path, name=folder_name)
                self.folder_repository.save_folder(new_folder)

                # Update folder list in the UI
                self._update_folder_list_after_add(new_folder)

                # Show notification while processing
                self.notify_service.show()

                # Scan the folder for music tracks
                music_files = MetadataService.scan_folder(folder_path)

                if not music_files:
                    return

                # Get all existing filenames in a single database query for efficiency
                existing_filenames = set()
                if self.music_repository._is_cache_valid():
                    # Use cache if available for better performance
                    existing_filenames = {music.filename for music in self.music_repository._cache}
                else:
                    # Otherwise query the database once to get all filenames
                    all_files = self.music_repository.datastore.list(column='filename')
                    existing_filenames = {record['filename'] for record in all_files if record}

                # Filter new files using the set for O(1) lookups
                new_music_files = [music for music in music_files
                                  if music.filename not in existing_filenames]

                # Use batch save instead of individual saves
                if new_music_files:
                    self.music_repository.batch_save_music(new_music_files)
        except Exception as e:
            print(f"Error scanning folder: {e}")
        finally:
            # Hide the notification
            self.notify_service.hide()

            # Notify music view about new folder addition
            self._send_settings_topic('new', folder_path)

    def on_dialog_close(self):
        """Handle dialog close event"""
        self.page.close(self)
        self.update()
