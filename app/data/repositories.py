"""
Repository classes for data access
"""
import time
from typing import List, Optional

from app.core.models import Music, Album, PlayerState, MusicFolder
from app.data.datastore import Datastore
from app.utils.helpers import sort_list_by


class PlayerRepository:
    """Repository for player state data"""

    def __init__(self):
        """Initialize the player repository"""
        self.datastore = Datastore('player')
        self._initialize_table()
        # Use in-memory cache to reduce database reads with cache timestamp
        self._cached_state = None
        self._cache_timestamp = 0
        self._cache_timeout = 5  # Cache timeout in seconds

    def _initialize_table(self):
        """Create the player table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'is_pause': 'TEXT DEFAULT "True"',
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
            'playlist': 'TEXT',
            'played_music': 'TEXT',
        })

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid based on timeout"""
        return (self._cached_state is not None and
                (time.time() - self._cache_timestamp) < self._cache_timeout)

    def get_player_state(self) -> PlayerState:
        """
        Get the current player state, using cache when available

        Returns:
            PlayerState: The current player state
        """
        if self._is_cache_valid():
            return self._cached_state

        # Cache expired or doesn't exist, fetch from database
        try:
            record = self.datastore.get_single(condition="id = ?", params=[1])

            if not record:
                # No data exists, create default state
                self._cached_state = PlayerState()
            else:
                self._cached_state = PlayerState.from_dict(record)

            # Update cache timestamp
            self._cache_timestamp = time.time()
            return self._cached_state

        except Exception as err:
            print(f"Error getting player state: {err}")
            # Return a default state in case of errors
            return PlayerState()

    def update_player_state(self, state: PlayerState, persist: bool = True) -> None:
        """
        Update the player state

        Args:
            state (PlayerState): The player state to save
            persist (bool): Whether to persist to database immediately
                           (set to False for frequent updates like position changes)
        """
        # Update the cache
        self._cached_state = state
        self._cache_timestamp = time.time()

        if not persist:
            return

        try:
            data = state.to_dict()
            record = self.datastore.get_single(condition="id = ?", params=[1])

            if not record:
                # No data exists, so insert new record
                self.datastore.save(data)
            else:
                # Update existing record
                self.datastore.update(data, condition='id = ?', condition_params=[1])
        except Exception as err:
            print(f"Error updating player state: {err}")

    def persist_cached_state(self) -> bool:
        """
        Force persistence of the cached state to the database
        Use for periodic updates or when application is closing

        Returns:
            bool: True if state was persisted successfully, False otherwise
        """
        if self._cached_state is None:
            return False

        try:
            self.update_player_state(self._cached_state, persist=True)
            return True
        except Exception as err:
            print(f"Error persisting cached state: {err}")
            return False

    def update_position(self, position: int) -> None:
        """
        Update only the current position without persisting other state

        Args:
            position (int): Current position in milliseconds
        """
        try:
            # Update cache
            if self._cached_state is not None:
                self._cached_state.audio_position = position
                self._cache_timestamp = time.time()

            # Only update position in database directly
            self.datastore.update(
                {'audio_current_position': position},
                condition='id = ?',
                condition_params=[1]
            )
        except Exception as err:
            print(f"Error updating position: {err}")


class MusicRepository:
    """Repository for music tracks data"""

    def __init__(self):
        """Initialize the music repository"""
        self.datastore = Datastore('musics')
        self._initialize_table()
        # Add basic caching
        self._cache = None
        self._cache_timestamp = 0
        self._cache_timeout = 10  # Cache timeout in seconds

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

    def _clear_cache(self):
        """Clear the music cache"""
        self._cache = None

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        return (self._cache is not None and
                (time.time() - self._cache_timestamp) < self._cache_timeout)

    def get_all_music(self, sort_by='title', use_cache=True) -> List[Music]:
        """
        Get all music tracks sorted by a specific key

        Args:
            sort_by (str): The key to sort by (default is 'title')
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Music]: List of all music tracks sorted by the specified key
        """
        if use_cache and self._is_cache_valid():
            return sort_list_by(key=sort_by, list=self._cache.copy())

        try:
            items = self.datastore.list()
            musics = [Music.from_dict(item) for item in items]

            # Update cache
            self._cache = musics
            self._cache_timestamp = time.time()

            return sort_list_by(key=sort_by, list=musics)
        except Exception as err:
            print(f"Error getting all music: {err}")
            return []

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
            if self._is_cache_valid():
                for music in self._cache:
                    if music.filename == filename:
                        return music

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="filename = ?", params=[filename])
            return Music.from_dict(record) if record else None
        except Exception as err:
            print(f"Error getting music by filename: {err}")
            return None

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
            self._clear_cache()
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
            self._clear_cache()
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
            self._clear_cache()
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
            if self._is_cache_valid():
                return any(music.filename == filename for music in self._cache)

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

            self._clear_cache()
            return True
        except Exception as err:
            print(f"Error in batch save: {err}")
            return False


class AlbumRepository:
    """Repository for album data"""

    def __init__(self):
        """Initialize the album repository"""
        self.datastore = Datastore('albums')
        self._initialize_table()
        # Add caching for album data
        self._cache = None
        self._cache_timestamp = 0
        self._cache_timeout = 10  # Cache timeout in seconds

    def _initialize_table(self):
        """Create the album table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'name': 'TEXT',
            'artist': 'TEXT',
            'cover': 'TEXT',
            'year': 'INTEGER',
        })

    def _clear_cache(self):
        """Clear the album cache"""
        self._cache = None

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        return (self._cache is not None and
                (time.time() - self._cache_timestamp) < self._cache_timeout)

    def get_all_albums(self, sort_by='name', use_cache=True) -> List[Album]:
        """
        Get all albums sorted by name or other specified key

        Args:
            sort_by (str): The key to sort by (default is 'name')
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Album]: List of all albums sorted alphabetically by name
        """
        if use_cache and self._is_cache_valid():
            return sort_list_by(key=sort_by, list=self._cache.copy())

        try:
            music_repo = MusicRepository()
            all_music = music_repo.get_all_music()

            # Group by album
            albums_dict = {}
            for music in all_music:
                if not music.album:  # Skip tracks without album info
                    continue

                key = f"{music.album}:{music.album_artist}"
                if key not in albums_dict:
                    albums_dict[key] = Album(
                        name=music.album,
                        artist=music.album_artist,
                        year=music.year
                    )
                albums_dict[key].tracks.append(music)

            # Convert to list
            albums = list(albums_dict.values())

            # Update cache
            self._cache = albums
            self._cache_timestamp = time.time()

            return sort_list_by(key=sort_by, list=albums)
        except Exception as err:
            print(f"Error getting all albums: {err}")
            return []

    def get_album_by_name_and_artist(self, name: str, artist: str) -> Optional[Album]:
        """
        Get an album by name and artist

        Args:
            name (str): The album name
            artist (str): The artist name

        Returns:
            Optional[Album]: The album or None if not found
        """
        try:
            # First check cache if valid
            if self._is_cache_valid():
                for album in self._cache:
                    if album.name == name and album.artist == artist:
                        return album

            # Not found in cache or cache invalid, query from database
            music_repo = MusicRepository()
            all_music = music_repo.get_all_music(sort_by='track_number')  # Sort by track number for proper ordering

            tracks = [m for m in all_music if m.album == name and m.artist == artist]

            if not tracks:
                return None

            return Album(
                name=name,
                artist=artist,
                year=tracks[0].year if tracks else None,
                tracks=tracks
            )
        except Exception as err:
            print(f"Error getting album by name and artist: {err}")
            return None

    def save_album_cover(self, album_name: str, artist: str, cover_path: str) -> bool:
        """
        Save or update album cover path

        Args:
            album_name (str): The album name
            artist (str): The artist name
            cover_path (str): Path to album cover image

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if album exists in our album table
            record = self.datastore.get_single(
                condition="name = ? AND artist = ?",
                params=[album_name, artist]
            )

            data = {
                'name': album_name,
                'artist': artist,
                'cover': cover_path
            }

            if not record:
                # Insert new record
                self.datastore.save(data)
            else:
                # Update existing record
                self.datastore.update(
                    {'cover': cover_path},
                    condition="name = ? AND artist = ?",
                    condition_params=[album_name, artist]
                )

            self._clear_cache()
            return True
        except Exception as err:
            print(f"Error saving album cover: {err}")
            return False


class FolderRepository:
    """Repository for music folders data"""

    def __init__(self):
        """Initialize the folder repository"""
        self.datastore = Datastore('folders')
        self._initialize_table()
        # Add basic caching
        self._cache = None
        self._cache_timestamp = 0
        self._cache_timeout = 60  # Cache timeout in seconds - folders change less frequently

    def _initialize_table(self):
        """Create the folder table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'path': 'TEXT UNIQUE',
            'name': 'TEXT',
            'added_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        })

    def _clear_cache(self):
        """Clear the folders cache"""
        self._cache = None

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        return (self._cache is not None and
                (time.time() - self._cache_timestamp) < self._cache_timeout)

    def get_all_folders(self, use_cache=True) -> List[MusicFolder]:
        """
        Get all music folders

        Args:
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[MusicFolder]: List of all music folders
        """
        if use_cache and self._is_cache_valid():
            return self._cache.copy()

        try:
            items = self.datastore.list()
            folders = [MusicFolder.from_dict(item) for item in items]

            # Update cache
            self._cache = folders
            self._cache_timestamp = time.time()

            return folders
        except Exception as err:
            print(f"Error getting all folders: {err}")
            return []

    def save_folder(self, folder: MusicFolder) -> bool:
        """
        Save a music folder

        Args:
            folder (MusicFolder): The music folder to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.datastore.save(folder.to_dict())
            self._clear_cache()
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
            self._clear_cache()
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
            if self._is_cache_valid():
                return any(folder.path == path for folder in self._cache)

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="path = ?", params=[path])
            return record is not None
        except Exception as err:
            print(f"Error checking if folder exists: {err}")
            return False

    def get_folder_by_path(self, path: str) -> Optional[MusicFolder]:
        """
        Get a folder by path

        Args:
            path (str): The folder path

        Returns:
            Optional[MusicFolder]: The folder if found, None otherwise
        """
        try:
            # Try cache first if valid
            if self._is_cache_valid():
                for folder in self._cache:
                    if folder.path == path:
                        return folder

            # Not in cache or cache invalid, query database
            record = self.datastore.get_single(condition="path = ?", params=[path])
            return MusicFolder.from_dict(record) if record else None
        except Exception as err:
            print(f"Error getting folder by path: {err}")
            return None
