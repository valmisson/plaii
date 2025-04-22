"""
Repository for album data
"""
from typing import List, Optional

from app.core.models import Album
from app.data.datastore import Datastore
from app.data.cache_manager import CacheManager
from app.utils.helpers import sort_list_by
from app.data.repositories.music_repository import MusicRepository


class AlbumRepository:
    """Repository for album data"""

    def __init__(self):
        """Initialize the album repository"""
        self.datastore = Datastore('albums')
        self._initialize_table()
        # Use thread-safe cache manager
        self._cache_manager = CacheManager[List[Album]](timeout_seconds=10)
        self.music_repository = MusicRepository()

    def _initialize_table(self):
        """Create the album table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'name': 'TEXT',
            'artist': 'TEXT',
            'cover': 'TEXT',
            'year': 'INTEGER',
        })

    def _load_all_albums(self, use_cache=True) -> List[Album]:
        """
        Load all albums from the database through music data

        Args:
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Album]: List of all albums
        """
        try:
            # Propagar a configuração use_cache para o MusicRepository
            all_music = self.music_repository.get_all_music(use_cache=use_cache)

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
            return list(albums_dict.values())
        except Exception as err:
            print(f"Error loading all albums: {err}")
            return []

    def get_all_albums(self, sort_by='name', use_cache=True) -> List[Album]:
        """
        Get all albums sorted by name or other specified key

        Args:
            sort_by (str): The key to sort by (default is 'name')
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Album]: List of all albums sorted alphabetically by name
        """
        if not use_cache:
            self._cache_manager.invalidate()

        albums = self._cache_manager.get(lambda: self._load_all_albums(use_cache=use_cache))
        return sort_list_by(key=sort_by, list=albums.copy() if albums else [])

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
            if self._cache_manager.is_valid():
                albums = self._cache_manager.get(lambda: [])
                for album in albums:
                    if album.name == name and album.artist == artist:
                        return album

            # Not found in cache or cache invalid, query from database
            all_music = self.music_repository.get_all_music(sort_by='track_number')  # Sort by track number for proper ordering

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

            # Update the cache if we have it
            if self._cache_manager.is_valid():
                def updater(albums: List[Album]) -> List[Album]:
                    for album in albums:
                        if album.name == album_name and album.artist == artist:
                            album.cover = cover_path
                    return albums
                self._cache_manager.update(updater)
            else:
                self._cache_manager.invalidate()

            return True
        except Exception as err:
            print(f"Error saving album cover: {err}")
            return False
