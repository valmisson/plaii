"""
Metadata service for handling music file metadata
"""
import os
from tinytag import TinyTag
from typing import Dict, List, Any

from app.config.settings import DEFAULT_DURATION_TEXT, DEFAULT_PLACEHOLDER_IMAGE
from app.core.models import Music
from app.utils.time_format import format_time


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

            metadata = {
                'title': title,
                'artist': tag.artist or 'Artista desconhecido',
                'album': tag.album or 'Álbum desconhecido',
                'album_artist': tag.albumartist or 'Artista desconhecido',
                'year': tag.year,
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
    def scan_folder(folder_path: str) -> List[Music]:
        """
        Scan a folder for music files and extract metadata

        Args:
            folder_path (str): Path to the folder to scan

        Returns:
            List[Music]: List of Music objects found in the folder
        """
        music_files = []
        supported_extensions = ['.mp3', '.ogg', '.flac', '.wav', '.m4a']

        try:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()

                    if file_ext in supported_extensions:
                        metadata = MetadataService.load_music_metadata(file_path)
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
        except Exception as err:
            print(f"Error scanning folder {folder_path}: {err}")

        return music_files

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
