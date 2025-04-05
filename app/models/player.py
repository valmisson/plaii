from shared import Datastore

class PlayerModel():
    def __init__(self):
        self.datastore = Datastore('player')

        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'is_pause': 'TEXT DEFAULT "False"',
            'is_muted': 'TEXT DEFAULT "False"',
            'is_playing': 'TEXT DEFAULT "False"',
            'is_shuffle': 'TEXT DEFAULT "False"',
            'is_repeat': 'TEXT DEFAULT "False"',
            'volume': 'REAL DEFAULT 0.5',
            'audio_duration': 'INTEGER',
            'audio_current_position': 'INTEGER',
            'current_music': 'TEXT',
            'current_album': 'TEXT',
            'prev_music': 'TEXT',
            'next_music': 'TEXT',
            'musics_list': 'TEXT',
            'played_music': 'TEXT',
        })

    @property
    def all_info(self):
        list = self.datastore.list()

        return list[0] if list else None

    def get_info(self, info: str):
        item = self.datastore.list(
            column=info
        )

        if not item:
            return None

        return item[0].get(info)

    def update_info(self, data: dict):
        # Check if there's any data in the database
        existing_data = self.datastore.list()

        if not existing_data:
            # No data exists, so save instead of update
            self.datastore.save(data)
        else:
            # Data exists, proceed with update
            self.datastore.update(
                data,
                condition='id = 1'
            )
