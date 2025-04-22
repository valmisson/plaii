"""
Music track data model
"""
from dataclasses import dataclass
from typing import Dict, Optional, Any

from app.config.settings import DEFAULT_DURATION_TEXT


@dataclass
class Music:
    """Music track data model"""
    title: str
    artist: str
    album: str
    album_artist: str
    filename: str
    duration: str
    track_number: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    folder: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "filename": self.filename,
            "folder": self.folder,
            "duration": self.duration,
            "track_number": self.track_number,
            "year": self.year,
            "genre": self.genre
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Music':
        """Create a Music instance from a dictionary"""
        return cls(
            title=data.get("title", "Titulo desconhecido"),
            artist=data.get("artist", "Artista desconhecido"),
            album=data.get("album", "Álbum desconhecido"),
            album_artist=data.get("album_artist", "Artista desconhecido"),
            filename=data.get("filename", ""),
            folder=data.get("folder"),
            duration=data.get("duration", DEFAULT_DURATION_TEXT),
            track_number=data.get("track_number"),
            year=data.get("year"),
            genre=data.get("genre")
        )
