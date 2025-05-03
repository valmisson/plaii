"""
Metadata service for handling music file metadata
"""
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tinytag import TinyTag
from typing import Dict, List, Any, Callable, Optional

from app.config.settings import (
    DEFAULT_DURATION_TEXT,
    DEFAULT_PLACEHOLDER_IMAGE,
    DEFAULT_BATCH_SIZE
)
from app.core.models import Music, Album
from app.utils.time_format import format_time
from app.utils.image_utils import image_to_base64


class MetadataService:
    """Service for handling music file metadata extraction and processing"""

    @staticmethod
    def load_music_metadata(file: str, with_image: bool = False) -> Dict[str, Any]:
        """
        Load metadata from a music file

        Args:
            file (str): Path to the music file
            with_image (bool): Whether to include album art image data

        Returns:
            Dict[str, Any]: Dictionary with metadata
        """
        try:
            tag = TinyTag.get(file, image=with_image)

            title = (f'{tag.track}. {tag.title}' if tag.track else tag.title) \
                if tag.title else os.path.basename(file).split('.')[0]

            # Extract year from tag if available
            tag_year = None
            if tag.year:
                match = re.search(r'\b\d{4}\b', str(tag.year))
                tag_year = match.group(0) if match else tag.year

            metadata = {
                'title': title,
                'artist': tag.artist or 'Artista desconhecido',
                'album': tag.album or 'Álbum desconhecido',
                'album_artist': tag.albumartist or 'Artista desconhecido',
                'year': tag_year,
                'track': tag.track,
                'genre': tag.genre,
                'duration': format_time(tag.duration, is_in_seconds=True),
                'filename': file,
            }

            if with_image:
                metadata['image'] = tag.images.front_cover.data \
                    if tag.images.front_cover else open(DEFAULT_PLACEHOLDER_IMAGE, 'rb').read()

            return metadata
        except Exception as err:
            print(f"Error loading metadata for {file}: {err}")
            filename = os.path.basename(file)
            return {
                'title': filename.split('.')[0],
                'artist': 'Artista desconhecido',
                'album': 'Álbum desconhecido',
                'duration': DEFAULT_DURATION_TEXT,
                'filename': file,
            }

    @staticmethod
    def load_music_cover(file: str) -> bytes:
        """
        Load album cover image from a music file

        Args:
            file (str): Path to the music file

        Returns:
            bytes: Album cover image data
        """
        try:
            # Reuse existing load_music_metadata method with image loading enabled
            metadata = MetadataService.load_music_metadata(file, with_image=True)
            if 'image' in metadata:
                return image_to_base64(metadata['image'])
            else:
                # Fallback to default image
                image = open(DEFAULT_PLACEHOLDER_IMAGE, 'rb').read()
                return image_to_base64(image)
        except Exception as err:
            print(f"Error loading cover for {file}: {err}")
            image = open(DEFAULT_PLACEHOLDER_IMAGE, 'rb').read()
            return image_to_base64(image)

    @staticmethod
    async def scan_folder_async(
        folder_path: str,
        batch_size = DEFAULT_BATCH_SIZE,
        process_callback: Optional[Callable[[List[Music], List[Album]], None]] = None
    ) -> tuple[List[Music], List[Album]]:
        """
        Scan a folder for music files asynchronously and extract metadata

        Args:
            folder_path (str): Path to the folder to scan
            batch_size (int): Number of files to process in each batch
            process_callback (Optional[Callable]): Optional callback for incremental processing

        Returns:
            tuple[List[Music], List[Album]]: Tuple containing list of Music objects and list of Album objects
        """
        supported_extensions = ['.mp3', '.ogg', '.flac', '.wav', '.m4a']
        music_files = []
        file_paths = []
        # Dictionary to store albums by album:artist key
        albums_dict = {}

        try:
            # Get all files in the folder and its subfolders in parallel
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in supported_extensions:
                        file_paths.append(file_path)

            total_files = len(file_paths)

            # Process files in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                for i in range(0, total_files, batch_size):
                    batch_files = file_paths[i:i+batch_size]
                    batch_tasks = []

                    for file_path in batch_files:
                        batch_tasks.append(
                            asyncio.get_event_loop().run_in_executor(
                                executor,
                                MetadataService.load_music_metadata,
                                file_path
                            )
                        )

                    results = await asyncio.gather(*batch_tasks)

                    batch_musics = []
                    # Track albums updated in this batch
                    albums_updated_in_batch = set()

                    for metadata in results:
                        music = Music(
                            title=metadata['title'],
                            artist=metadata['artist'],
                            album=metadata['album'],
                            album_artist=metadata['album_artist'],
                            filename=metadata['filename'],
                            folder=folder_path,
                            duration=metadata['duration'],
                            track_number=metadata.get('track'),
                            year=metadata.get('year'),
                            genre=metadata.get('genre')
                        )
                        music_files.append(music)
                        batch_musics.append(music)

                        # Skip tracks without album info
                        if not music.album:
                            continue

                        # Group by album
                        album_key = f"{music.album}:{music.album_artist}"
                        if album_key not in albums_dict:
                            album_cover = MetadataService.load_music_cover(music.filename)
                            albums_dict[album_key] = Album(
                                name=music.album,
                                artist=music.album_artist,
                                year=music.year,
                                genre=music.genre,
                                cover=album_cover,
                            )

                        # Add the music to the album's tracks
                        albums_dict[album_key].tracks.append(music)
                        # Mark this album as updated in this batch
                        albums_updated_in_batch.add(album_key)

                    # Include all albums updated in this batch in the callback
                    batch_albums = [albums_dict[key] for key in albums_updated_in_batch]

                    if process_callback and batch_musics:
                        process_callback(batch_musics, batch_albums)

        except Exception as err:
            print(f"Error scanning folder {folder_path}: {err}")

        return music_files, list(albums_dict.values())

    @staticmethod
    def scan_folder(
        folder_path: str,
        batch_size = DEFAULT_BATCH_SIZE,
        process_callback: Optional[Callable[[List[Music], List[Album]], None]] = None
    ) -> tuple[List[Music], List[Album]]:
        """
        Scan a folder for music files and extract metadata

        Args:
            folder_path (str): Path to the folder to scan
            batch_size (int): Number of files to process in each batch
            process_callback (Optional[Callable]): Optional callback for incremental processing

        Returns:
            tuple[List[Music], List[Album]]: Tuple containing list of Music objects and list of Album objects
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                MetadataService.scan_folder_async(folder_path, batch_size, process_callback)
            )
        finally:
            loop.close()

    @staticmethod
    def extract_folder_name(folder_path: str) -> str:
        """
        Extract a folder name from a path

        Args:
            folder_path (str): Path to the folder

        Returns:
            str: The folder name
        """
        try:
            return os.path.basename(os.path.normpath(folder_path))
        except Exception:
            return "Unknown Folder"
