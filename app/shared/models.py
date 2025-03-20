from .utils import sort_by
from .datastore import Datastore

class MusicsModel():
    def __init__(self):
        self.datastore = Datastore('musics')

        self.datastore.create_table(columns={
            'title': 'TEXT',
            'artist': 'TEXT',
            'album': 'TEXT',
            'duration': 'TEXT',
            'filename': 'TEXT',
            'parent_folder': 'TEXT'
        })

    @property
    def all_musics(self):
        list = self.datastore.list()

        self.datastore.disconnect()

        return sort_by(list, key='title')

    def get_music(self, filename: str):
        item = self.datastore.list(
            condition=f'filename = "{filename}"'
        )

        self.datastore.disconnect()

        return item

    def save_musics(self, musics: list[dict]):
        for music in musics:
            music_filename = music.get('filename')
            has_music = self.get_music(music_filename)

            if not has_music:
                self.datastore.save(data=music)
            elif has_music:
                current_parent_folder: list[str] = has_music[0].get('parent_folder').split(',')
                music_parent_folder: str = music.get('parent_folder')

                if music_parent_folder not in current_parent_folder:
                    current_parent_folder.append(music_parent_folder)

                    new_parent_folder = ','.join(current_parent_folder)

                    self.datastore.update(
                        data={ 'parent_folder': new_parent_folder },
                        condition=f'filename = "{music_filename}"'
                    )

        self.datastore.disconnect()

    def remove_musics(self, parent_folder):
        musics_to_remove = self.datastore.list(
            condition=f'parent_folder LIKE "%{parent_folder}%"'
        )

        for music in musics_to_remove:
            filename: str = music.get('filename')
            parent_folder_str: str = music.get('parent_folder')
            parent_folder_list: list[str] = parent_folder_str.split(',')

            if len(parent_folder_list) > 1:
                new_parent_folder_list = list(
                    filter(lambda i: i != parent_folder, parent_folder_list)
                )
                new_parent_folder = ','.join(new_parent_folder_list)

                self.datastore.update(
                    data={ 'parent_folder': new_parent_folder },
                    condition=f'filename = "{filename}"'
                )
            else:
                self.datastore.delete(f'filename = "{filename}"')

        self.datastore.disconnect()

class FoldersModel():
    def __init__(self):
        self.datastore = Datastore('folders')

        self.datastore.create_table(columns={ 'path': 'TEXT' })

    @property
    def folder_paths(self):
        list_items = self.datastore.list(column='path')

        self.datastore.disconnect()

        return [item.get('path') for item in list_items]


    def save_folder_path(self, path: str):
        exist_path = self.datastore.list(
            column='path',
            condition=f'path = "{path}"'
        )

        if not exist_path:
            self.datastore.save(data={ 'path': path })

        self.datastore.disconnect()

    def remove_folder_path(self, path: str):
        exist_path = self.datastore.list(
            column='path',
            condition=f'path = "{path}"'
        )

        if exist_path:
            self.datastore.delete(condition=f'path = "{path}"')

        self.datastore.disconnect()
