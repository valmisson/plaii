from shared import Datastore

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
