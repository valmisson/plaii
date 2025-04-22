"""
Music folder data model
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Folder:
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Folder':
        """Create a Folder instance from a dictionary"""
        return cls(
            path=data.get("path", ""),
            name=data.get("name", "Unknown Folder")
        )
