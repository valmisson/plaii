from app.core.models import App
from app.data.datastore import Datastore
from app.data.cache_manager import CacheManager

class AppRepository:
    """Repository for app state data"""

    def __init__(self):
        """Initialize the app repository"""
        self.datastore = Datastore('app')
        self._initialize_table()

    def _initialize_table(self):
        """Create the app table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'current_view': 'INTEGER DEFAULT 0',
        })

    def get_app_state(self) -> App:
        """
        Load app data from database

        Returns:
            App: The app data from database or default one
        """
        try:
            record = self.datastore.get_single(condition="id = ?", params=[1])
            return App.from_dict(record) if record else App()
        except Exception as err:
            print(f"Error loading app state: {err}")
            return App()

    def update_app_state(self, state: App) -> None:
        """
        Update the app state in the database

        Args:
            state (App): The app state to update
        """
        try:
            data = state.to_dict()
            record = self.datastore.get_single(condition="id = ?", params=[1])

            if not record:
                # not found, insert new record
                self.datastore.save(data)
            else:
                # found, update existing record
                self.datastore.update(data, condition='id = ?', condition_params=[1])
        except Exception as err:
            print(f"Error updating app state: {err}")
