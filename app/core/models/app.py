from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class App:
    """Application data model"""
    current_view: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "current_view": self.current_view
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'App':
        """Create an App instance from a dictionary"""
        return cls(
            current_view=int(data.get("current_view", 0))
        )
