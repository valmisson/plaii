"""
Repository for album data
"""
import json
from typing import List

from app.core.models import Album
from app.data.datastore import Datastore
from app.data.cache_manager import CacheManager
from app.data.repositories.music_repository import MusicRepository
from app.utils.helpers import sort_list_by


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
            'year': 'INTEGER',
            'genre': 'TEXT',
            'cover': 'TEXT',
            'tracks': 'TEXT'
        })

    def _load_all_albums(self, use_cache=True) -> List[Album]:
        """
        Load all albums from the database

        Args:
            use_cache (bool): Whether to use cached results if available

        Returns:
            List[Album]: List of all albums
        """
        try:
            # Get all albums from the database
            records = self.datastore.list()
            albums = []

            for record in records:
                try:
                    # Parse tracks JSON if it exists
                    if 'tracks' in record and record['tracks']:
                        try:
                            # Convert the stored JSON string back to a list of track dictionaries
                            record['tracks'] = json.loads(record['tracks'])
                        except json.JSONDecodeError as json_err:
                            print(f"Error decoding JSON for album {record.get('name')}: {json_err}")
                            record['tracks'] = []
                    else:
                        record['tracks'] = []

                    # Use Album.from_dict to create album object
                    album = Album.from_dict(record)
                    album.tracks = sort_list_by(key='title', list=album.tracks)
                    albums.append(album)
                except Exception as album_err:
                    print(f"Error processing album record: {album_err}")
                    continue

            return albums
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

    def batch_save_albums(self, albums_list: List[Album]) -> bool:
        """
        Save multiple albums in a single transaction, updating existing ones if needed.
        This method preserves existing tracks and only adds new ones.

        Args:
            albums_list (List[Album]): List of albums to save

        Returns:
            bool: True if successful, False otherwise
        """
        if not albums_list:
            return True

        try:
            # Group albums by key (name:artist) for easier lookup
            album_dict = {f"{album.name}:{album.artist}": album for album in albums_list}

            # Phase 1: Prepare data - separate into inserts and updates
            inserts = []  # New albums to insert
            updates = []  # Existing albums to update

            # Fetch all existing albums that match our keys in a single query
            if album_dict:
                album_keys = list(album_dict.keys())
                names_artists = [key.split(':', 1) for key in album_keys]

                # Build conditions for a single query
                conditions = []
                params = []
                for name, artist in names_artists:
                    conditions.append("(name = ? AND artist = ?)")
                    params.extend([name, artist])

                condition_str = " OR ".join(conditions) if conditions else ""
                existing_records = self.datastore.list(condition=condition_str, params=params) if condition_str else []

                # Create a lookup dictionary of existing records
                existing_dict = {f"{record['name']}:{record['artist']}": record
                                for record in existing_records if 'name' in record and 'artist' in record}

                # Process each album
                for key, album in album_dict.items():
                    name, artist = key.split(':', 1)

                    # Convert tracks to dictionaries using built-in to_dict() method
                    track_dicts = [track.to_dict() for track in album.tracks]

                    if key not in existing_dict:
                        # New album
                        inserts.append({
                            'name': name,
                            'artist': artist,
                            'year': album.year,
                            'genre': album.genre,
                            'cover': album.cover,
                            'tracks': json.dumps(track_dicts)
                        })
                    else:
                        # Existing album - merge tracks
                        record = existing_dict[key]
                        existing_tracks = []

                        try:
                            if record.get('tracks'):
                                existing_tracks = json.loads(record['tracks'])
                        except (json.JSONDecodeError, TypeError):
                            pass

                        # Fast lookup for existing filenames
                        existing_filenames = {t.get('filename') for t in existing_tracks if t.get('filename')}

                        # Add only new tracks
                        added = False
                        for track in track_dicts:
                            if track['filename'] not in existing_filenames:
                                existing_tracks.append(track)
                                added = True

                        # Only update if we added tracks or need to update other fields
                        update_data = {}
                        if added:
                            update_data['tracks'] = json.dumps(existing_tracks)

                        # Update other fields only if needed
                        if not record.get('year') and album.year:
                            update_data['year'] = album.year
                        if not record.get('genre') and album.genre:
                            update_data['genre'] = album.genre
                        if not record.get('cover') and album.cover:
                            update_data['cover'] = album.cover

                        if update_data:
                            updates.append((update_data, name, artist))

            # Phase 2: Execute database operations in batch
            with self.datastore.transaction() as conn:
                cursor = conn.cursor()

                # Insert new albums
                if inserts:
                    for data in inserts:
                        columns = ', '.join(data.keys())
                        placeholders = ', '.join(['?' for _ in data])
                        cursor.execute(
                            f'INSERT INTO {self.datastore.table} ({columns}) VALUES ({placeholders})',
                            tuple(data.values())
                        )

                # Update existing albums
                if updates:
                    for update_data, name, artist in updates:
                        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
                        cursor.execute(
                            f'UPDATE {self.datastore.table} SET {set_clause} WHERE name = ? AND artist = ?',
                            tuple(update_data.values()) + (name, artist)
                        )

            # Invalidate cache to ensure fresh data
            self._cache_manager.invalidate()
            return True
        except Exception as err:
            print(f"Error in batch save albums: {err}")
            return False

    def batch_delete_albums(self, album_names: List[int]) -> bool:
        """
        Delete multiple albums in a single transaction by their IDs

        Args:
            album_names (List[int]): List of album to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not album_names:
            return True

        try:
            # Convert album_names to a comma-separated string for SQL IN clause
            placeholders = ','.join(['?' for _ in album_names])

            # Execute the delete operation
            with self.datastore.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'DELETE FROM {self.datastore.table} WHERE name IN ({placeholders})',
                    tuple(album_names)
                )

            # Invalidate cache to ensure fresh data
            self._cache_manager.invalidate()
            return True
        except Exception as err:
            print(f"Error in batch delete albums: {err}")
            return False
