"""
Repository for player state data
"""
from app.core.models import PlayerState
from app.data.datastore import Datastore
from app.data.cache_manager import CacheManager


class PlayerRepository:
    """Repository for player state data"""

    def __init__(self):
        """Initialize the player repository"""
        self.datastore = Datastore('player')
        self._initialize_table()
        # Use thread-safe cache manager for player state
        self._cache_manager = CacheManager[PlayerState](timeout_seconds=5)

    def _initialize_table(self):
        """Create the player table if it doesn't exist"""
        self.datastore.create_table(columns={
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'is_pause': 'TEXT DEFAULT "True"',
            'is_muted': 'TEXT DEFAULT "False"',
            'is_playing': 'TEXT DEFAULT "False"',
            'is_shuffle': 'TEXT DEFAULT "False"',
            'is_repeat': 'TEXT DEFAULT "False"',
            'volume': 'REAL DEFAULT 0.5',
            'audio_duration': 'INTEGER',
            'audio_current_position': 'INTEGER',
            'current_music': 'TEXT',
            'current_album': 'TEXT',
            'playlist': 'TEXT',
            'playlist_source': 'TEXT',
            'played_music': 'TEXT',
        })

    def _load_player_state(self) -> PlayerState:
        """
        Load player state from database

        Returns:
            PlayerState: The player state from database or default one
        """
        try:
            record = self.datastore.get_single(condition="id = ?", params=[1])
            return PlayerState.from_dict(record) if record else PlayerState()
        except Exception as err:
            print(f"Error loading player state: {err}")
            return PlayerState()

    def invalidate_cache(self):
        """Invalidate the player state cache"""
        self._cache_manager.invalidate()

    def get_player_state(self) -> PlayerState:
        """
        Get the current player state, using cache when available

        Returns:
            PlayerState: The current player state
        """
        return self._cache_manager.get(self._load_player_state)

    def update_player_state(self, state: PlayerState, persist: bool = True) -> None:
        """
        Update the player state

        Args:
            state (PlayerState): The player state to save
            persist (bool): Whether to persist to database immediately
                           (set to False for frequent updates like position changes)
        """
        # Always update the cache
        self._cache_manager.set(state)

        if not persist:
            return

        try:
            data = state.to_dict()
            record = self.datastore.get_single(condition="id = ?", params=[1])

            if not record:
                # No data exists, so insert new record
                self.datastore.save(data)
            else:
                # Update existing record
                self.datastore.update(data, condition='id = ?', condition_params=[1])
        except Exception as err:
            print(f"Error updating player state: {err}")

    def persist_cached_state(self) -> bool:
        """
        Force persistence of the cached state to the database
        Use for periodic updates or when application is closing

        Returns:
            bool: True if state was persisted successfully, False otherwise
        """
        if not self._cache_manager.is_valid():
            return False

        try:
            state = self._cache_manager.get(lambda: None)
            if state:
                self.update_player_state(state, persist=True)
                return True
            return False
        except Exception as err:
            print(f"Error persisting cached state: {err}")
            return False

    def update_position(self, position: int) -> None:
        """
        Update only the current position without persisting other state

        Args:
            position (int): Current position in milliseconds
        """
        try:
            # Update cache if valid
            if self._cache_manager.is_valid():
                def update_position_in_state(state: PlayerState) -> PlayerState:
                    state.audio_position = position
                    return state
                self._cache_manager.update(update_position_in_state)

            # Only update position in database directly
            self.datastore.update(
                {'audio_current_position': position},
                condition='id = ?',
                condition_params=[1]
            )
        except Exception as err:
            print(f"Error updating position: {err}")
