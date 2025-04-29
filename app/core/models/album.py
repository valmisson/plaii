"""
Album data model
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from app.core.models.music import Music


@dataclass
class Album:
    """Album data model"""
    name: str
    artist: str
    cover: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    tracks: List[Music] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "name": self.name,
            "artist": self.artist,
            "cover": self.cover,
            "year": self.year,
            "genre": self.genre,
            "tracks": [track.to_dict() for track in self.tracks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Album':
        """Create an Album instance from a dictionary"""
        tracks = [Music.from_dict(track) for track in data.get("tracks", [])]
        return cls(
            name=data.get("name", "Álbum desconhecido"),
            artist=data.get("artist", "Artista desconhecido"),
            cover=data.get("cover"),
            year=data.get("year"),
            genre=data.get("genre"),
            tracks=tracks
        )
