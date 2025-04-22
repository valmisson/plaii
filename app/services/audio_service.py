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

        # Ensure we have a playlist to work with
        if not state.playlist:
            return

        next_music = None

        if state.is_shuffle:
            next_music = self._get_track_shuffle_mode(state, is_next=True)
        else:
            next_music = self._get_track_normal_mode(state, is_next=True)

        # Play the track if we found one
        if next_music:
            music = Music.from_dict(next_music)
            self.load_music(music)

            if not state.is_paused:
                self.play()

    def play_previous(self) -> None:
        """Play the previous track based on current state"""
        state = self.player_repository.get_player_state()

        # If we're more than 3 seconds into the song, go to the start instead of previous song
        if self.audio.get_current_position() and self.audio.get_current_position() > 3000:
            self.audio.seek(0)
            self.audio.resume()
            return

        # Ensure we have a playlist to work with
        if not state.playlist:
            return

        prev_music = None

        if state.is_shuffle:
            prev_music = self._get_track_shuffle_mode(state, is_next=False)
        else:
            prev_music = self._get_track_normal_mode(state, is_next=False)

        # Play the track if we found one
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

    def _get_track_shuffle_mode(self, state: PlayerState, is_next: bool) -> Optional[Dict]:
        """
        Get next or previous track when in shuffle mode

        Args:
            state (PlayerState): Current player state
            is_next (bool): True for next track, False for previous track

        Returns:
            Optional[Dict]: Track to play or None
        """
        if not state.current_music:
            # No current track
            if is_next:
                # For next, choose a random track
                return choice(state.playlist) if state.playlist else None
            else:
                # For previous, get the last played music if available
                return state.played_music[-1] if state.played_music else None

        # Check if current music is in the played list
        if state.current_music in state.played_music:
            current_index = state.played_music.index(state.current_music)

            if is_next:
                # For next, return the next music in played list if available
                if current_index < len(state.played_music) - 1:
                    return state.played_music[current_index + 1]

                # Otherwise, get unplayed music
                available_music = [
                    music for music in state.playlist
                    if music not in state.played_music
                ]

                if available_music:
                    return choice(available_music)
                elif state.is_repeat == "all" and state.playlist:
                    # If all have been played and repeat all is enabled
                    state.played_music.clear()
                    return choice(state.playlist)
            else:
                # For previous, return the previous music in played list if available
                if current_index > 0:
                    return state.played_music[current_index - 1]
        else:
            # Current music is not in the played list (was removed or another issue)
            if is_next:
                # For next, choose an unplayed music
                available_music = [
                    music for music in state.playlist
                    if music not in state.played_music
                ]

                if available_music:
                    return choice(available_music)
                elif state.playlist and state.is_repeat == "all":
                    state.played_music.clear()
                    return choice(state.playlist)
            else:
                # For previous, get the last played music if available
                return state.played_music[-1] if state.played_music else None

        return None

    def _get_track_normal_mode(self, state: PlayerState, is_next: bool) -> Optional[Dict]:
        """
        Get next or previous track when in normal sequential mode

        Args:
            state (PlayerState): Current player state
            is_next (bool): True for next track, False for previous track

        Returns:
            Optional[Dict]: Track to play or None
        """
        if not state.current_music:
            # No current music, but playlist exists
            if is_next:
                # For next, return the first track
                return state.playlist[0] if state.playlist else None
            else:
                # For previous, return the last track
                return state.playlist[-1] if state.playlist else None

        # Check if current music is in the playlist
        if state.current_music in state.playlist:
            index = state.playlist.index(state.current_music)

            if is_next:
                # For next, return the next if possible
                if index < len(state.playlist) - 1:
                    return state.playlist[index + 1]
                elif state.is_repeat == "all":
                    # If at the end and repeat all is enabled
                    return state.playlist[0]
            else:
                # For previous, return the previous if possible
                if index > 0:
                    return state.playlist[index - 1]
                elif state.is_repeat == "all":
                    # If at the beginning and repeat all is enabled
                    return state.playlist[-1]
        else:
            # Current music was removed from the playlist
            current_filename = state.current_music.get('filename', '')

            if is_next:
                # For next, find the first music that comes after alphabetically
                for music in state.playlist:
                    if music.get('filename', '') > current_filename:
                        return music

                # If not found, use the first track
                return state.playlist[0] if state.playlist else None
            else:
                # For previous, find the music that comes before alphabetically
                best_match = None

                for music in state.playlist:
                    if music.get('filename', '') < current_filename:
                        best_match = music
                    else:
                        # Stop when we pass the point where the current music would be
                        break

                # If a match is found, use it; otherwise, use the last track
                if best_match:
                    return best_match
                elif state.playlist:
                    return state.playlist[-1]

        return None

    def cleanup(self) -> None:
        """
        Perform cleanup operations before application exit
        """
        # Make sure to persist any cached state
        self.player_repository.persist_cached_state()
