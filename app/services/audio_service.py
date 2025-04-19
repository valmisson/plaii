"""
Audio service for handling audio playback and control
"""
from random import choice
from typing import Dict, Optional, Any, Callable

from flet import Page
from flet_audio import Audio, AudioState, AudioStateChangeEvent

from app.config.settings import DEFAULT_VOLUME
from app.core.models import PlayerState, Music
from app.data.repositories import PlayerRepository, MusicRepository


class AudioService:
    """Service for audio playback and control"""

    def __init__(self, page: Page):
        """
        Initialize the audio service

        Args:
            page (Page): The Flet page object
        """
        self.page = page
        self.player_repository = PlayerRepository()
        self.music_repository = MusicRepository()

        # Initialize audio player
        self.audio = Audio(
            src='none',
            volume=DEFAULT_VOLUME,
            balance=0,
            on_loaded=self._on_audio_loaded,
            on_state_changed=self._on_audio_state_changed,
            on_position_changed=self._on_audio_position_changed,
        )
        self.audio._initial_load = False  # Custom attribute to track initial loading
        self._position_update_counter = 0

        # Add audio player to page overlay
        self.page.overlay.append(self.audio)

        # Load initial player state
        self._load_player_state()

        # Event callbacks
        self._on_position_changed_callbacks = []
        self._on_state_changed_callbacks = []
        self._on_music_changed_callbacks = []

    def _load_player_state(self) -> None:
        """Load the player state from the repository"""
        state = self.player_repository.get_player_state()

        # Set volume
        self.audio.volume = state.volume if not state.is_muted else 0

        # Set current music if available
        if state.current_music:
            self.audio._initial_load = True
            self.audio.src = state.current_music.get('filename')
            self.audio._current_position = state.audio_position or 0

    def load_music(self, music: Music) -> None:
        """
        Load a music track into the audio player

        Args:
            music (Music): The music track to load
        """
        # Update current music in state
        state = self.player_repository.get_player_state()

        state.current_music = music.to_dict()
        state.current_album = music.album

        # Add to played music list if not already there
        if music.to_dict() not in state.played_music:
            state.played_music.append(music.to_dict())

        # Update music queue (prev/next)
        self._update_music_queue(music, state)

        # Set audio source and play
        self.audio.src = music.filename

        # Notify subscribers
        for callback in self._on_music_changed_callbacks:
            callback(music)

    def play(self) -> None:
        """
        Play a music track

        Args:
            music (Music): The music track to play
        """
        self.audio.play()

        # Update state in repository
        state = self.player_repository.get_player_state()
        state.is_paused = False
        state.is_playing = True
        self.player_repository.update_player_state(state)

    def pause(self) -> None:
        """Pause audio playback"""
        self.audio.pause()

        # Update state in repository
        state = self.player_repository.get_player_state()
        state.is_paused = True
        state.is_playing = False
        self.player_repository.update_player_state(state)

    def resume(self) -> None:
        """Resume audio playback"""
        # No music loaded, do nothing
        if self.audio.src == 'none':
            return

        self.audio.resume()

        # Update state in repository
        state = self.player_repository.get_player_state()
        state.is_paused = False
        state.is_playing = True
        self.player_repository.update_player_state(state)

    def stop(self) -> None:
        """Stop audio playback"""
        self.audio.pause()
        self.audio.seek(0)

        # Update state in repository
        state = self.player_repository.get_player_state()
        state.is_paused = True
        state.is_playing = False
        state.audio_position = 0
        self.player_repository.update_player_state(state)

    def reset(self) -> None:
        """
        Reset the audio player to its initial state"""
        self.audio.release()
        self.audio.src = 'none'

    def seek(self, position: int) -> None:
        """
        Seek to a position in the audio

        Args:
            position (int): The position in milliseconds
        """
        self.audio.seek(position)

        # Update state in repository without writing to database immediately
        state = self.player_repository.get_player_state()
        state.audio_position = position
        self.player_repository.update_player_state(state, persist=False)

    def set_volume(self, volume: float) -> None:
        """
        Set the audio volume

        Args:
            volume (float): The volume level (0.0 to 1.0)
        """
        self.audio.volume = volume

        # Update state in repository
        state = self.player_repository.get_player_state()
        state.volume = volume
        state.is_muted = volume == 0
        self.player_repository.update_player_state(state)

    def toggle_mute(self) -> bool:
        """
        Toggle mute state

        Returns:
            bool: The new mute state
        """
        state = self.player_repository.get_player_state()
        state.is_muted = not state.is_muted

        if state.is_muted:
            self.audio.volume = 0
        else:
            self.audio.volume = state.volume

        self.audio.update()

        self.player_repository.update_player_state(state)
        return state.is_muted

    def toggle_shuffle(self) -> bool:
        """
        Toggle shuffle state

        Returns:
            bool: The new shuffle state
        """
        state = self.player_repository.get_player_state()
        state.is_shuffle = not state.is_shuffle

        if state.is_shuffle:
            state.played_music = []
            if state.current_music:
                state.played_music.append(state.current_music)

        self.player_repository.update_player_state(state)
        return state.is_shuffle

    def toggle_repeat(self) -> Optional[str]:
        """
        Toggle repeat state

        Returns:
            Optional[str]: The new repeat state ("one", "all", or None)
        """
        state = self.player_repository.get_player_state()

        if not state.is_repeat:
            state.is_repeat = "all"
        elif state.is_repeat == "all":
            state.is_repeat = "one"
        else:
            state.is_repeat = None

        self.player_repository.update_player_state(state)
        return state.is_repeat

    def play_next(self) -> None:
        """Play the next track based on current state"""
        state = self.player_repository.get_player_state()

        next_music = None
        if state.is_shuffle:
            # Handle shuffle mode
            current_music = state.current_music
            if current_music and current_music in state.played_music:
                current_index = state.played_music.index(current_music)

                # Check if there's a next track in played list
                if current_index < len(state.played_music) - 1:
                    next_music = state.played_music[current_index + 1]
                else:
                    # Get music not in played list
                    available_music = [
                        music for music in state.playlist
                        if music not in state.played_music
                    ]
                    if available_music:
                        next_music = choice(available_music)
                    elif state.is_repeat == "all":
                        # Reset played list and pick a random track
                        state.played_music.clear()
                        next_music = choice(state.playlist) if state.playlist else None
        else:
            next_music = state.next_music

            # If repeat all and no next track, loop to first track
            if not next_music and state.is_repeat == "all" and state.playlist:
                next_music = state.playlist[0]

        if next_music:
            music = Music.from_dict(next_music)
            self.load_music(music)

            if not state.is_paused:
                self.play()

    def play_previous(self) -> None:
        """Play the previous track based on current state"""
        state = self.player_repository.get_player_state()

        # If we're more than 3 seconds into the song, go to the start
        if self.audio.get_current_position() and self.audio.get_current_position() > 3000:
            self.audio.seek(0)
            self.audio.resume()
            return

        prev_music = None
        if state.is_shuffle:
            # Handle shuffle mode
            current_music = state.current_music
            if current_music and current_music in state.played_music:
                current_index = state.played_music.index(current_music)

                # Check if there's a previous track in played list
                if current_index > 0:
                    prev_music = state.played_music[current_index - 1]
        else:
            prev_music = state.prev_music

        if prev_music:
            music = Music.from_dict(prev_music)
            self.load_music(music)

            if not state.is_paused:
                self.play()

    def get_current_position(self) -> int:
        """
        Get the current position in milliseconds

        Returns:
            int: The current position
        """
        try:
            return self.audio.get_current_position() or 0
        except Exception as err:
            print(f"Error getting current position: {err}")
            return 0

    def get_duration(self) -> int:
        """
        Get the audio duration in milliseconds

        Returns:
            int: The audio duration
        """
        try:
            return self.audio.get_duration() or 0
        except Exception as err:
            print(f"Error getting audio duration: {err}")
            return 0

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing

        Returns:
            bool: True if playing, False otherwise
        """
        state = self.player_repository.get_player_state()
        return state.is_playing

    def on_position_changed(self, callback: Callable[[int, int], None]) -> None:
        """
        Register a callback for position changes

        Args:
            callback: Function with signature (position, duration)
        """
        self._on_position_changed_callbacks.append(callback)

    def on_state_changed(self, callback: Callable[[AudioState, Dict[str, Any]], None]) -> None:
        """
        Register a callback for state changes

        Args:
            callback: Function with signature (state, music_data)
        """
        self._on_state_changed_callbacks.append(callback)

    def on_music_changed(self, callback: Callable[[Music], None]) -> None:
        """
        Register a callback for when music changes

        Args:
            callback: Function with signature (music)
        """
        self._on_music_changed_callbacks.append(callback)

    def _update_music_queue(self, music: Music, state: PlayerState) -> None:
        """
        Update the music queue (previous/next tracks)

        Args:
            music (Music): The current music track
            state (PlayerState): The player state
        """
        music_dict = music.to_dict()
        if music_dict not in state.playlist:
            return

        index = state.playlist.index(music_dict)

        prev_music = None
        next_music = None

        if index > 0:
            prev_music = state.playlist[index - 1]

        if index < len(state.playlist) - 1:
            next_music = state.playlist[index + 1]

        state.prev_music = prev_music
        state.next_music = next_music

    def _on_audio_loaded(self, _) -> None:
        """Handle audio loaded event"""
        state = self.player_repository.get_player_state()

        if state.is_playing:
            self.audio.play()

        if getattr(self.audio, '_initial_load', False):
            # For initial load, just update the duration info without playing
            self.audio.seek(self.audio._current_position)
            self.audio._initial_load = False

        try:
            duration = self.audio.get_duration()
            if duration is not None:
                state.audio_duration = duration
                self.player_repository.update_player_state(state)
        except Exception as err:
            print(f"Error getting audio duration: {err}")
            # Set a default duration or leave it as is in the state

    def _on_audio_state_changed(self, event: AudioStateChangeEvent) -> None:
        """Handle audio state changed event"""
        state = self.player_repository.get_player_state()

        if event.state == AudioState.COMPLETED:
            if state.is_repeat == "one" and state.current_music:
                # Repeat current track
                music = Music.from_dict(state.current_music)
                self.load_music(music)
                self.play()
            else:
                self.play_next()
        elif event.state == AudioState.PAUSED:
            state.is_paused = True
            state.is_playing = False
            self.player_repository.update_player_state(state)
        elif event.state == AudioState.PLAYING:
            state.is_paused = False
            state.is_playing = True
            self.player_repository.update_player_state(state)

        # Notify subscribers
        for callback in self._on_state_changed_callbacks:
            callback(event.state, state.current_music or {})

        # Publish event to page
        self.page.pubsub.send_all_on_topic(
            'play:music',
            {
                'state': event.state,
                'current_music': state.current_music.get('filename') if state.current_music else None,
                'current_album': state.current_music.get('album') if state.current_music else None,
            }
        )

    def _on_audio_position_changed(self, _) -> None:
        """Handle audio position changed event"""
        position = self.get_current_position()
        duration = self.get_duration()

        # Notify subscribers
        for callback in self._on_position_changed_callbacks:
            callback(position, duration)

        # Update position in database periodically to avoid excessive writes
        self._position_update_counter += 1
        if self._position_update_counter >= 10:  # Reduced frequency (was 5)
            self.player_repository.update_position(position)
            self._position_update_counter = 0

    def cleanup(self) -> None:
        """
        Perform cleanup operations before application exit
        """
        # Make sure to persist any cached state
        self.player_repository.persist_cached_state()
