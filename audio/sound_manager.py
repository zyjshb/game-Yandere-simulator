# -*- coding: utf-8 -*-
"""
SoundManager encapsulates pygame audio: heartbeat background loop and one-shot
voice playback.  All pygame mixer interaction is confined to this module.
"""

import os

from audio.heartbeat_gen import generate_heartbeat_wav

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class SoundManager:
    def __init__(self):
        self.heartbeat_sound = None
        self.heartbeat_channel = None
        self.voice_channel = None

    # ------------------------------------------------------------------
    # Heartbeat background loop
    # ------------------------------------------------------------------

    def init_heartbeat(self, audio_file="heartbeat.wav"):
        if not HAS_PYGAME:
            print("[warning] pygame not detected; background audio will be silent.")
            return

        if not os.path.exists("heartbeat.mp3") and not os.path.exists("heartbeat.wav"):
            try:
                generate_heartbeat_wav("heartbeat.wav")
            except Exception as ex:
                print(f"[system] heartbeat synthesis failed: {ex}")
                return

        if os.path.exists("heartbeat.mp3"):
            audio_file = "heartbeat.mp3"

        try:
            pygame.mixer.init()
            self.heartbeat_sound = pygame.mixer.Sound(audio_file)
            self.heartbeat_channel = self.heartbeat_sound.play(-1)
            self.heartbeat_channel.set_volume(0.8)
        except Exception as ex:
            print(f"[system] heartbeat playback error: {ex}")

    def set_heartbeat_volume(self, vol):
        """Set heartbeat volume, 0.0 to 1.0."""
        if self.heartbeat_channel:
            self.heartbeat_channel.set_volume(vol)

    # ------------------------------------------------------------------
    # Voice playback
    # ------------------------------------------------------------------

    def play_voice_from_file(self, filepath):
        """
        Play a WAV file immediately through pygame.mixer.Sound.
        Returns the Channel object (or None on failure).
        The caller is responsible for waiting on channel.get_busy().
        """
        if not HAS_PYGAME:
            return None

        try:
            voice_sound = pygame.mixer.Sound(filepath)
            channel = voice_sound.play()
            self.voice_channel = channel
            return channel
        except Exception as ex:
            print(f"[system] voice playback failed: {ex}")
            return None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def stop_all(self):
        """Stop all currently playing sounds."""
        if HAS_PYGAME and pygame.mixer.get_init():
            pygame.mixer.stop()

    def cleanup(self):
        """Release resources held by the mixer."""
        self.stop_all()
        if HAS_PYGAME and pygame.mixer.get_init():
            pygame.mixer.quit()
