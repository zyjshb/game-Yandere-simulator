# -*- coding: utf-8 -*-
"""
ECGCanvas -- wraps the ECG heartbeat waveform animation and optional visual
effects (dripping blood, scanlines, snow noise, fake error overlay).

Reads visual parameters from a ``GameState`` instance (suspicion, ecg_frenzy,
think_jitter, etc.) which are set by the owning MainWindow.
"""

import math
import random
import tkinter as tk

from visual_fx import ParticleEngine


class ECGCanvas(tk.Canvas):
    """A tkinter Canvas subclass that draws a real-time animated ECG waveform.

    The waveform responds to the game suspicion level and frenzy/think-jitter
    flags stored on the GameState object.
    """

    def __init__(self, parent, game_state):
        super().__init__(parent, bg="#000000", height=45, highlightthickness=0)
        self.game_state = game_state
        self.ecg_time = 0.0
        self._particle_engine = None
        self._after_id = None
        self._active = True
        self._start_animation_loop()

    # ------------------------------------------------------------------
    # Animation loop
    # ------------------------------------------------------------------

    def _start_animation_loop(self):
        self._update_ecg()

    def _update_ecg(self):
        if not self._active:
            return

        self.ecg_time += 0.035
        self.delete("all")

        # Safely query actual canvas width
        width = self.winfo_width()
        if width <= 200:
            width = 1100

        height = 45
        points = []
        num_points = 300
        dx = width / num_points

        susp = self.game_state.suspicion
        is_frenzy = getattr(self.game_state, "shaking", False) or getattr(self.game_state, "ecg_frenzy", False)
        is_think_jitter = getattr(self.game_state, "think_jitter", False)

        # --- colour / amplitude selection ---
        if is_frenzy:
            period = 0.35
            color_main = "#FF0000"
            color_mid = "#FF3333"
            color_fade = "#7A0000"
            amplitude_scale = 1.4
            jitter_range = 8.5
        elif is_think_jitter:
            period = 0.8
            color_main = "#9E0000"
            color_mid = "#540000"
            color_fade = "#2A0000"
            amplitude_scale = 0.5
            jitter_range = 1.8
        else:
            period = 1.4 - 0.9 * (susp / 100.0)
            if susp < 30:
                color_main = "#8A0303"
                color_mid = "#500000"
                color_fade = "#200000"
                amplitude_scale = 0.75
                jitter_range = 0.0
            elif susp < 75:
                color_main = "#CC0000"
                color_mid = "#8A0303"
                color_fade = "#400000"
                amplitude_scale = 1.0
                jitter_range = 1.2
            else:
                color_main = "#FF0000"
                color_mid = "#CC0000"
                color_fade = "#600000"
                amplitude_scale = 1.25
                jitter_range = 4.2

        # --- grid ---
        grid_color = "#0B0000" if susp < 50 else "#150000"
        for grid_x in range(0, width, 40):
            self.create_line(grid_x, 0, grid_x, height, fill=grid_color, width=1)
        for grid_y in range(0, height, 15):
            self.create_line(0, grid_y, width, grid_y, fill=grid_color, width=1)

        # --- waveform ---
        points.clear()
        for idx in range(num_points):
            x = idx * dx
            t_val = (self.ecg_time + (idx * 0.015)) % period
            y_baseline = height / 2

            tp = t_val / period
            y = y_baseline

            if getattr(self.game_state, "ecg_flatline_active", False):
                # flatline -- keep y at baseline
                pass
            else:
                if 0.0 <= tp < 0.06:
                    y = y_baseline - 3.5 * math.sin(math.pi * tp / 0.06) * amplitude_scale
                elif 0.12 <= tp < 0.15:
                    y = y_baseline + 5.0 * ((tp - 0.12) / 0.03) * amplitude_scale
                elif 0.15 <= tp < 0.20:
                    y = (y_baseline + 5.0 * amplitude_scale) - 35.0 * ((tp - 0.15) / 0.05) * amplitude_scale
                elif 0.20 <= tp < 0.25:
                    y = (y_baseline - 30.0 * amplitude_scale) + 38.0 * ((tp - 0.20) / 0.05) * amplitude_scale
                elif 0.25 <= tp < 0.28:
                    y = (y_baseline + 8.0 * amplitude_scale) - 8.0 * ((tp - 0.25) / 0.03) * amplitude_scale
                elif 0.38 <= tp < 0.55:
                    y = y_baseline - 6.5 * math.sin(math.pi * (tp - 0.38) / 0.17) * amplitude_scale

            if jitter_range > 0 and not getattr(self.game_state, "ecg_flatline_active", False):
                y += random.uniform(-jitter_range, jitter_range)

            points.append((x, y))

        for p_idx in range(len(points) - 1):
            x1, y1 = points[p_idx]
            x2, y2 = points[p_idx + 1]

            alpha_ratio = p_idx / len(points)
            if alpha_ratio > 0.85:
                c = color_main
                w = 6 if is_frenzy else (2 if susp > 70 else 1)
            elif alpha_ratio > 0.6:
                c = color_mid
                w = 3 if is_frenzy else 1
            else:
                c = color_fade
                w = 2 if is_frenzy else 1

            self.create_line(x1, y1, x2, y2, fill=c, width=w)

        last_x, last_y = points[-1]
        glow_radius = 2.5 if int(self.ecg_time * 5) % 2 == 0 else 1.0
        self.create_oval(
            last_x - glow_radius, last_y - glow_radius,
            last_x + glow_radius, last_y + glow_radius,
            fill=color_main, outline="",
        )

        # --- extra visual layers (dripping blood, scanlines, snow noise, fake error) ---
        if getattr(self.game_state, "dripping_blood_active", False):
            for line in getattr(self.game_state, "dripping_blood_lines", []):
                line["y"] += line["speed"]
                self.create_line(line["x"], 0, line["x"], line["y"], fill="#FF0000", width=2)

        if getattr(self.game_state, "scanlines_active", False):
            for _ in range(12):
                scan_y = random.randint(2, height - 2)
                self.create_line(0, scan_y, width, scan_y, fill="#FF0000", width=random.randint(1, 4))

        if getattr(self.game_state, "snow_noise_active", False):
            for _ in range(60):
                rx = random.randint(0, width)
                ry = random.randint(0, height)
                self.create_oval(rx - 1, ry - 1, rx + 1, ry + 1, fill="#FF2222", outline="")

        if getattr(self.game_state, "fake_error_active", False):
            self.create_rectangle(width / 2 - 120, 5, width / 2 + 120, height - 5,
                                  fill="#1A0000", outline="#FF0000", width=2)
            self.create_text(width / 2, height / 2, text="FATAL ERROR: HEART OVERLOAD",
                             fill="#FF0000", font=("Consolas", 10, "bold"))

        self._after_id = self.after(30, self._update_ecg)

    # ------------------------------------------------------------------
    # Particle engine
    # ------------------------------------------------------------------

    def start_particle_engine(self, count=30):
        """Initialize and start a ParticleEngine on this canvas."""
        if self._particle_engine is not None:
            return
        self._particle_engine = ParticleEngine(self, count=count)
        self._particle_engine.start()

    def stop_particle_engine(self):
        """Stop and clean up the particle engine."""
        if self._particle_engine is not None:
            self._particle_engine.stop()
            self._particle_engine = None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def destroy(self):
        self._active = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.stop_particle_engine()
        super().destroy()
