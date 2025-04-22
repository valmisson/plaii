"""
Repository for music folders data
"""
from typing import List, Optional

from app.core.models import Folder
from app.data.datastore import Datastore
from app.data.cache_manager import CacheManager


class FolderRepository:
    """Repository for music folders data"""

    def __init__(self):
        """Initialize the folder repository"""
        self.datastore = Datastore('folders')
        self._initialize_table()
        # Use thread-safe cache manager with longer timeout as folders change less frequently
        self._cache_manager = CacheManager[List[Folder]](timeout_seconds=60)

    def _initialize_table(self):
        """Create the folder table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'path': 'TEXT UNIQUE',
            'name': 'TEXT',
            'added_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        })

    def _load_all_folders(self) -> List[Folder]:
        """
        Load all folders from database

        Returns:
            List[Folder]: List of all music folders
        """
        try:
            items = self.datastore.list()
            return [Folder.from_dict(item) for item in items]
        except Exception as err:
            print(f"Error loading all folders: {err}")
            return []

    def get_all_folders(self, use_cache=True) -> List[Folder]:
        """
        Get all music folders

        Args:
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Folder]: List of all music folders
        """
        if not use_cache:
            self._cache_manager.invalidate()

        folders = self._cache_manager.get(self._load_all_folders)
        return folders.copy() if folders else []

    def save_folder(self, folder: Folder) -> bool:
        """
        Save a music folder

        Args:
            folder (Folder): The music folder to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.datastore.save(folder.to_dict())

            # Update cache if we have it
            if self._cache_manager.is_valid():
                def updater(folders: List[Folder]) -> List[Folder]:
                    # Make sure we don't add duplicates
                    for existing in folders:
                        if existing.path == folder.path:
                            return folders
                    return folders + [folder]
                self._cache_manager.update(updater)
            else:
                self._cache_manager.invalidate()

            return True
        except Exception as err:
            print(f"Error saving folder: {err}")
            return False

    def delete_folder(self, path: str) -> bool:
        """
        Delete a music folder

        Args:
            path (str): The path of the folder to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rows_affected = self.datastore.delete(condition="path = ?", params=[path])

            # Update cache if we have it
            if self._cache_manager.is_valid():
                def updater(folders: List[Folder]) -> List[Folder]:
                    return [f for f in folders if f.path != path]
                self._cache_manager.update(updater)
            else:
                self._cache_manager.invalidate()

            return rows_affected > 0
        except Exception as err:
            print(f"Error deleting folder: {err}")
            return False

    def folder_exists(self, path: str) -> bool:
        """
        Check if a music folder exists

        Args:
            path (str): The path to check

        Returns:
            bool: True if the folder exists, False otherwise
        """
        try:
            # Try cache first if valid
            if self._cache_manager.is_valid():
                folders = self._cache_manager.get(lambda: [])
                return any(folder.path == path for folder in folders)

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="path = ?", params=[path])
            return record is not None
        except Exception as err:
            print(f"Error checking if folder exists: {err}")
            return False

    def get_folder_by_path(self, path: str) -> Optional[Folder]:
        """
        Get a folder by path

        Args:
            path (str): The folder path

        Returns:
            Optional[Folder]: The folder if found, None otherwise
        """
        try:
            # Try cache first if valid
            if self._cache_manager.is_valid():
                folders = self._cache_manager.get(lambda: [])
                for folder in folders:
                    if folder.path == path:
                        return folder

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="path = ?", params=[path])
            return Folder.from_dict(record) if record else None
        except Exception as err:
            print(f"Error getting folder by path: {err}")
            return None
