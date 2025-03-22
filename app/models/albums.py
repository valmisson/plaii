from shared import (
    Datastore,
    get_album_artist,
    get_album_cover,
    load_music_metadata,
    sort_by
)

class AlbumsModel():
    def __init__(self):
        self.datastore = Datastore('albums')

        self.datastore.create_table(columns={
            'name': 'TEXT UNIQUE',
            'artist': 'TEXT',
            'cover': 'TEXT',
            'parent_folder': 'TEXT'
        })

    @property
    def all_albums(self):
        list = self.datastore.list()

        self.datastore.disconnect()

        return sort_by(list, key='name')

    def get_album(self, name: str):
        item = self.datastore.list(
            condition=f'name = "{name}"'
        )

        self.datastore.disconnect()

        return item

    def save_albums(self, musics: list[dict]):
        for music in musics:
            album_name = music.get('album')
            has_album = self.get_album(album_name)

            if has_album:
                current_parent_folder: list[str] = has_album[0].get('parent_folder').split(',')
                music_parent_folder: str = music.get('parent_folder')

                if music_parent_folder not in current_parent_folder:
                    current_parent_folder.append(music_parent_folder)

                    new_parent_folder = ','.join(current_parent_folder)

                    self.datastore.update(
                        data={ 'parent_folder': new_parent_folder },
                        condition=f'name = "{album_name}"'
                    )
            else:
                music_metadata = load_music_metadata(
                    file=music.get('filename'),
                    with_image=True
                )

                self.datastore.save(data={
                    'name': album_name,
                    'artist': get_album_artist(music_metadata),
                    'cover': get_album_cover(music_metadata),
                    'parent_folder': music.get('parent_folder')
                })

        self.datastore.disconnect()

    def remove_albums(self, parent_folder):
        albums_to_remove = self.datastore.list(
            condition=f'parent_folder LIKE "%{parent_folder}%"'
        )

        for album in albums_to_remove:
            album_name: str = album.get('name')
            parent_folder_str: str = album.get('parent_folder')
            parent_folder_list: list[str] = parent_folder_str.split(',')

            if len(parent_folder_list) > 1:
                new_parent_folder_list = list(
                    filter(lambda i: i != parent_folder, parent_folder_list)
                )
                new_parent_folder = ','.join(new_parent_folder_list)

                self.datastore.update(
                    data={ 'parent_folder': new_parent_folder },
                    condition=f'name = "{album_name}"'
                )
            else:
                self.datastore.delete(f'name = "{album_name}"')

        self.datastore.disconnect()
