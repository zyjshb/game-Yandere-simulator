# -*- coding: utf-8 -*-
"""
Synthesizes a high-quality eerie low-frequency heartbeat WAV file using only
the standard library (wave, struct, math).
"""

import math
import struct
import wave


def generate_heartbeat_wav(filepath):
    """
    Use pure Python math and the wave library to generate a 12-second,
    high-quality, eerie low-frequency double-thump heartbeat (Lub-Dub) loop.
    """
    sample_rate = 22050
    duration = 12.0
    num_samples = int(sample_rate * duration)

    with wave.open(filepath, "wb") as wav_file:
        wav_file.setnchannels(1)       # mono
        wav_file.setsampwidth(2)      # 16-bit PCM
        wav_file.setframerate(sample_rate)

        frames = []
        for i in range(num_samples):
            t = i / sample_rate
            value = 0.0

            def get_thump(t, t_start, t_end, freq, amp):
                if t_start <= t <= t_end:
                    d = t_end - t_start
                    u = (t - t_start) / d
                    envelope = math.sin(math.pi * u) ** 2
                    return amp * envelope * math.sin(2 * math.pi * freq * (t - t_start))
                return 0.0

            bpm_period = 1.333
            num_beats = int(duration / bpm_period)
            for b in range(num_beats):
                beat_start = b * bpm_period
                value += get_thump(t, beat_start + 0.1, beat_start + 0.28, 55.0, 0.75)
                value += get_thump(t, beat_start + 0.35, beat_start + 0.53, 42.0, 0.55)

            int_val = int(value * 32767)
            int_val = max(-32768, min(32767, int_val))
            frames.append(struct.pack("<h", int_val))

        wav_file.writeframes(b"".join(frames))
