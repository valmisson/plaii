"""
Repository for music tracks data
"""
from typing import List, Optional

from app.core.models import Music
from app.data.datastore import Datastore
from app.data.cache_manager import CacheManager
from app.utils.helpers import sort_list_by


class MusicRepository:
    """Repository for music tracks data"""

    def __init__(self):
        """Initialize the music repository"""
        self.datastore = Datastore('musics')
        self._initialize_table()
        # Use thread-safe cache manager
        self._cache_manager = CacheManager[List[Music]](timeout_seconds=10)

    def _initialize_table(self):
        """Create the music table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'title': 'TEXT',
            'artist': 'TEXT',
            'album': 'TEXT',
            'album_artist': 'TEXT',
            'filename': 'TEXT UNIQUE',
            'folder': 'TEXT',
            'duration': 'TEXT',
            'track_number': 'INTEGER',
            'year': 'INTEGER',
            'genre': 'TEXT',
            'added_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        })

    def _load_all_music(self) -> List[Music]:
        """
        Load all music from database

        Returns:
            List[Music]: List of all music tracks
        """
        try:
            items = self.datastore.list()
            return [Music.from_dict(item) for item in items]
        except Exception as err:
            print(f"Error loading all music: {err}")
            return []

    def get_all_music(self, sort_by='title', use_cache=True) -> List[Music]:
        """
        Get all music tracks sorted by a specific key

        Args:
            sort_by (str): The key to sort by (default is 'title')
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Music]: List of all music tracks sorted by the specified key
        """
        if not use_cache:
            self._cache_manager.invalidate()

        musics = self._cache_manager.get(self._load_all_music)
        return sort_list_by(key=sort_by, list=musics.copy() if musics else [])

    def get_music_by_filename(self, filename: str) -> Optional[Music]:
        """
        Get a music track by filename

        Args:
            filename (str): The filename to search for

        Returns:
            Optional[Music]: The music track or None if not found
        """
        try:
            # Try cache first for performance
            if self._cache_manager.is_valid():
                musics = self._cache_manager.get(lambda: [])
                for music in musics:
                    if music.filename == filename:
                        return music

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="filename = ?", params=[filename])
            return Music.from_dict(record) if record else None
        except Exception as err:
            print(f"Error getting music by filename: {err}")
            return None

    def get_music_by_folder_path(self, folder_path: str, sort_by='title') -> List[Music]:
        """
        Get all music tracks from a specific folder path

        Args:
            folder_path (str): The folder path to filter by
            sort_by (str): The key to sort by (default is 'title')

        Returns:
            List[Music]: List of music tracks in the specified folder
        """
        try:
            # Query directly rather than filtering in memory for better performance
            records = self.datastore.list(condition="folder = ?", params=[folder_path])
            musics = [Music.from_dict(record) for record in records]
            return sort_list_by(key=sort_by, list=musics.copy() if musics else [])
        except Exception as err:
            print(f"Error getting music by folder path: {err}")
            return []

    def save_music(self, music: Music) -> bool:
        """
        Save a music track

        Args:
            music (Music): The music track to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.datastore.save(music.to_dict())
            self._cache_manager.invalidate()
            return True
        except Exception as err:
            print(f"Error saving music: {err}")
            return False

    def update_music(self, music: Music) -> bool:
        """
        Update a music track

        Args:
            music (Music): The music track to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = music.to_dict()
            rows_affected = self.datastore.update(
                data,
                condition="filename = ?",
                condition_params=[music.filename]
            )

            # Update the cache if we have it
            if self._cache_manager.is_valid():
                def updater(musics: List[Music]) -> List[Music]:
                    result = []
                    for m in musics:
                        if m.filename == music.filename:
                            result.append(music)
                        else:
                            result.append(m)
                    return result
                self._cache_manager.update(updater)
            else:
                self._cache_manager.invalidate()

            return rows_affected > 0
        except Exception as err:
            print(f"Error updating music: {err}")
            return False

    def delete_music(self, filename: str) -> bool:
        """
        Delete a music track

        Args:
            filename (str): The filename of the track to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rows_affected = self.datastore.delete(condition="filename = ?", params=[filename])

            # Update cache if we have it
            if self._cache_manager.is_valid():
                def updater(musics: List[Music]) -> List[Music]:
                    return [m for m in musics if m.filename != filename]
                self._cache_manager.update(updater)
            else:
                self._cache_manager.invalidate()

            return rows_affected > 0
        except Exception as err:
            print(f"Error deleting music: {err}")
            return False

    def music_exists(self, filename: str) -> bool:
        """
        Check if a music track exists

        Args:
            filename (str): The filename to check

        Returns:
            bool: True if the track exists, False otherwise
        """
        try:
            # Try cache first
            if self._cache_manager.is_valid():
                musics = self._cache_manager.get(lambda: [])
                return any(music.filename == filename for music in musics)

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="filename = ?", params=[filename])
            return record is not None
        except Exception as err:
            print(f"Error checking if music exists: {err}")
            return False

    def batch_save_music(self, music_list: List[Music]) -> bool:
        """
        Save multiple music tracks in a single transaction

        Args:
            music_list (List[Music]): List of music tracks to save

        Returns:
            bool: True if successful, False otherwise
        """
        if not music_list:
            return True

        try:
            # Use transaction to ensure all or nothing
            with self.datastore.transaction() as conn:
                cursor = conn.cursor()
                for music in music_list:
                    data = music.to_dict()
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['?' for _ in data])

                    cursor.execute(
                        f'INSERT INTO {self.datastore.table} ({columns}) VALUES ({placeholders})',
                        tuple(data.values())
                    )

            self._cache_manager.invalidate()
            return True
        except Exception as err:
            print(f"Error in batch save: {err}")
            return False

    def batch_delete_music(self, filenames: List[str]) -> bool:
        """
        Delete multiple music tracks in a single transaction

        Args:
            filenames (List[str]): List of filenames to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not filenames:
            return True

        try:
            # Use transaction for better performance with multiple deletes
            placeholders = ', '.join(['?' for _ in filenames])
            cursor = self.datastore.execute_query(
                f'DELETE FROM {self.datastore.table} WHERE filename IN ({placeholders})',
                filenames
            )

            rows_affected = cursor.rowcount

            # Update cache if we have it
            if self._cache_manager.is_valid():
                def updater(musics: List[Music]) -> List[Music]:
                    # Create a set for O(1) lookups
                    delete_set = set(filenames)
                    return [m for m in musics if m.filename not in delete_set]
                self._cache_manager.update(updater)
            else:
                self._cache_manager.invalidate()

            return rows_affected > 0
        except Exception as err:
            print(f"Error in batch delete: {err}")
            return False
