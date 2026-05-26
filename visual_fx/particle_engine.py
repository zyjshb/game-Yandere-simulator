# -*- coding: utf-8 -*-
"""
===============================================================================
  Canvas-based particle engine (ambient floating embers / dust motes).
===============================================================================
"""

import random
import tkinter as tk


class ParticleEngine:
    """Drives a set of floating particles on a tkinter Canvas."""

    def __init__(self, canvas, count=35):
        self.canvas = canvas
        self.particles = []
        self.active = False
        self._after_id = None
        self.count = count
        self.intensity = 0  # 0.0 .. 1.0, driven by suspicion

    def start(self):
        if self.active:
            return
        self.active = True
        self._replenish()
        self._tick()

    def stop(self):
        self.active = False
        if self._after_id is not None:
            self.canvas.after_cancel(self._after_id)
            self._after_id = None
        for pid in self.particles:
            self.canvas.delete(pid)
        self.particles.clear()

    def _replenish(self):
        w = self.canvas.winfo_width() or 1100
        h = self.canvas.winfo_height() or 45
        while len(self.particles) < self.count:
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(1, 3)
            alpha = random.randint(15, 80)
            color = f"#{alpha:02x}0000"
            pid = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                          fill=color, outline="")
            self.particles.append(pid)

    def _tick(self):
        if not self.active:
            return

        w = self.canvas.winfo_width() or 1100
        h = self.canvas.winfo_height() or 45

        for pid in list(self.particles):
            try:
                coords = self.canvas.coords(pid)
                if not coords:
                    self.particles.remove(pid)
                    continue
                cx = (coords[0] + coords[2]) / 2
                cy = (coords[1] + coords[3]) / 2
                # drift upward + slight horizontal wander
                nx = cx + random.uniform(-0.4, 0.4)
                ny = cy - random.uniform(0.2, 1.0)
                if ny < -5:
                    ny = h + 5
                    nx = random.randint(0, w)
                if nx < -5:
                    nx = w + 5
                elif nx > w + 5:
                    nx = -5
                r = (coords[2] - coords[0]) / 2
                self.canvas.coords(pid, nx - r, ny - r, nx + r, ny + r)
            except Exception:
                if pid in self.particles:
                    self.particles.remove(pid)

        self._replenish()
        self._after_id = self.canvas.after(50, self._tick)
