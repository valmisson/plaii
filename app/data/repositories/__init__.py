"""
Repository module for data access
"""
from app.data.repositories.app_repository import AppRepository
from app.data.repositories.player_repository import PlayerRepository
from app.data.repositories.music_repository import MusicRepository
from app.data.repositories.album_repository import AlbumRepository
from app.data.repositories.folder_repository import FolderRepository


__all__ = [
    'AppRepository',
    'PlayerRepository',
    'MusicRepository',
    'AlbumRepository',
    'FolderRepository'
]
