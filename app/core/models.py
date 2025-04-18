"""
Core data models for music player application
"""
from dataclasses import dataclass, field
import json
from typing import Dict, List, Optional, Any

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


@dataclass
class Album:
    """Album data model"""
    name: str
    artist: str
    cover: Optional[str] = None
    year: Optional[int] = None
    tracks: List[Music] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "name": self.name,
            "artist": self.artist,
            "cover": self.cover,
            "year": self.year,
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
            tracks=tracks
        )


@dataclass
class PlayerState:
    """Player state data model"""
    is_paused: bool = True
    is_muted: bool = False
    is_playing: bool = False
    is_shuffle: bool = False
    is_repeat: Optional[str] = None  # None, "one", or "all"
    volume: float = 0.5
    audio_duration: Optional[int] = None
    audio_position: Optional[int] = None
    current_music: Optional[Dict[str, Any]] = None
    current_album: Optional[str] = None
    prev_music: Optional[Dict[str, Any]] = None
    next_music: Optional[Dict[str, Any]] = None
    playlist: List[Dict[str, Any]] = field(default_factory=list)
    played_music: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for database storage"""
        return {
            "is_pause": str(self.is_paused),
            "is_muted": str(self.is_muted),
            "is_playing": str(self.is_playing),
            "is_shuffle": str(self.is_shuffle),
            "is_repeat": str(self.is_repeat) if self.is_repeat else "False",
            "volume": self.volume,
            "audio_duration": self.audio_duration,
            "audio_current_position": self.audio_position,
            "current_music": self._safe_json_dumps(self.current_music),
            "current_album": self.current_album,
            "prev_music": self._safe_json_dumps(self.prev_music),
            "next_music": self._safe_json_dumps(self.next_music),
            "playlist": self._safe_json_dumps(self.playlist),
            "played_music": self._safe_json_dumps(self.played_music),
        }

    def _safe_json_dumps(self, obj: Any) -> Optional[str]:
        """Safely convert an object to a JSON string"""
        if obj is None:
            return None
        try:
            return json.dumps(obj)
        except (TypeError, ValueError):
            print(f"Warning: Failed to serialize object: {type(obj)}")
            return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create a PlayerState instance from a dictionary"""
        if not data:
            return cls()

        # Convert string representations to actual booleans
        is_paused = cls._parse_bool(data.get("is_pause", "True"))
        is_muted = cls._parse_bool(data.get("is_muted", "False"))
        is_playing = cls._parse_bool(data.get("is_playing", "False"))
        is_shuffle = cls._parse_bool(data.get("is_shuffle", "False"))

        # Handle repeat state
        repeat_value = data.get("is_repeat")
        is_repeat = None
        if repeat_value and repeat_value.lower() not in ["false", "none"]:
            is_repeat = repeat_value.lower()

        # Handle complex JSON fields
        current_music = cls._safe_json_loads(data.get("current_music"))
        prev_music = cls._safe_json_loads(data.get("prev_music"))
        next_music = cls._safe_json_loads(data.get("next_music"))
        playlist = cls._safe_json_loads(data.get("playlist")) or []
        played_music = cls._safe_json_loads(data.get("played_music")) or []

        # Handle numeric fields
        volume = cls._parse_float(data.get("volume", "0.5"))
        audio_duration = cls._parse_int(data.get("audio_duration"))
        audio_position = cls._parse_int(data.get("audio_current_position"))

        return cls(
            is_paused=is_paused,
            is_muted=is_muted,
            is_playing=is_playing,
            is_shuffle=is_shuffle,
            is_repeat=is_repeat,
            volume=volume,
            audio_duration=audio_duration,
            audio_position=audio_position,
            current_music=current_music,
            current_album=data.get("current_album"),
            prev_music=prev_music,
            next_music=next_music,
            playlist=playlist,
            played_music=played_music
        )

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        """Safely parse a boolean value from various input types"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.lower()
            return value == "true" or value == "1" or value == "yes"
        return bool(value)

    @staticmethod
    def _parse_float(value: Any) -> float:
        """Safely parse a float value"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.5

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        """Safely parse an integer value"""
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_json_loads(value: Any) -> Any:
        """Safely parse a JSON string"""
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            print(f"Warning: Failed to deserialize value: {value[:20]}...")
            return None


@dataclass
class MusicFolder:
    """Music folder data model"""
    path: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "path": self.path,
            "name": self.name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicFolder':
        """Create a MusicFolder instance from a dictionary"""
        return cls(
            path=data.get("path", ""),
            name=data.get("name", "Unknown Folder")
        )
