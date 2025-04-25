"""
Thread-safe cache manager for repository data
"""
import time
import threading
from typing import Optional, TypeVar, Generic, Callable

T = TypeVar('T')


class CacheManager(Generic[T]):
    """
    A thread-safe caching manager for repositories.

    Provides synchronized access to cached data with timeout-based invalidation.
    """

    def __init__(self, timeout_seconds: int = 10):
        """
        Initialize the cache manager.

        Args:
            timeout_seconds (int): Cache timeout in seconds
        """
        self._data: Optional[T] = None
        self._timestamp: float = 0
        self._timeout: int = timeout_seconds
        self._lock = threading.RLock()

    def get(self, loader: Callable[[], T]) -> T:
        """
        Get data from cache or load it if cache is invalid.

        Args:
            loader (Callable[[], T]): Function to load data when cache is invalid

        Returns:
            T: Cached or freshly loaded data
        """
        with self._lock:
            if self.is_valid():
                return self._data

            # Cache invalid, reload data
            self._data = loader()
            self._timestamp = time.time()
            return self._data

    def is_valid(self) -> bool:
        """
        Check if the cache is still valid based on timeout.

        Returns:
            bool: True if cache is valid, False otherwise
        """
        return (self._data is not None and
                (time.time() - self._timestamp) < self._timeout)

    def invalidate(self) -> None:
        """Invalidate the cache."""
        with self._lock:
            self._data = None
            self._timestamp = 0

    def set(self, data: T) -> None:
        """
        Directly set the cache data.

        Args:
            data (T): Data to cache
        """
        with self._lock:
            self._data = data
            self._timestamp = time.time()

    def update(self, update_func: Callable[[T], T]) -> Optional[T]:
        """
        Update the cached data using a function.

        Args:
            update_func (Callable[[T], T]): Function to update the cached data

        Returns:
            Optional[T]: Updated data or None if cache was invalid
        """
        with self._lock:
            if not self.is_valid():
                return None

            self._data = update_func(self._data)
            self._timestamp = time.time()
            return self._data
