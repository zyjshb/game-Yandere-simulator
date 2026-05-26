# -*- coding: utf-8 -*-
"""
===============================================================================
  Procedural visual effects module for Saki yandere game.
  Every texture, particle, and overlay is generated at runtime using
  Pillow + tkinter Canvas. Zero external image assets required.
===============================================================================
"""

import random
import math
import colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageTk
import tkinter as tk


# ══════════════════════════════════════════════════════════════════════════════
#  Procedural texture generators (Pillow-based)
# ══════════════════════════════════════════════════════════════════════════════

class ProceduralFX:
    """Static methods that return ImageTk.PhotoImage objects ready for tkinter."""

    @staticmethod
    def blood_splatter(width, height, drops=40, intensity=0.6):
        """Generate a semi-transparent blood splatter overlay."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        base = (180, 10, 15)  # deep arterial red

        for _ in range(drops):
            cx = random.randint(0, width)
            cy = random.randint(0, height)
            # main splatter blob
            r = random.randint(8, max(12, int(45 * intensity)))
            alpha = random.randint(40, int(200 * intensity))
            color = (
                base[0] + random.randint(-20, 30),
                base[1] + random.randint(-5, 20),
                base[2] + random.randint(-5, 15),
                alpha,
            )
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

            # trailing droplets
            for _ in range(random.randint(1, 5)):
                tx = cx + random.randint(-r * 2, r * 2)
                ty = cy + random.randint(-r * 2, r * 2)
                tr = random.randint(1, max(2, r // 3))
                draw.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill=color)

        # darken / pool in corners
        for _ in range(int(drops * 0.4)):
            cx = random.randint(0, width)
            cy = random.randint(int(height * 0.7), height)
            r = random.randint(15, 60)
            dark_pool = (50, 0, 5, random.randint(30, 100))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=dark_pool)

        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        return ImageTk.PhotoImage(img)

    @staticmethod
    def vignette(width, height, darkness=0.55):
        """Radial vignette: dark edges, clearer center."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = width // 2, height // 2
        max_dist = math.sqrt(cx * cx + cy * cy)

        # draw concentric rings of increasing opacity
        steps = 40
        for i in range(steps):
            ratio = i / steps
            # inner is clear, outer is dark
            alpha = int(255 * darkness * (ratio ** 1.8))
            r = int(max_dist * ratio)
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                outline=(0, 0, 0, alpha),
                width=random.randint(1, 3),
            )

        img = img.filter(ImageFilter.GaussianBlur(radius=8))
        return ImageTk.PhotoImage(img)

    @staticmethod
    def scanlines(width, height, spacing=4, opacity=0.18):
        """CRT scanline overlay."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        alpha = int(255 * opacity)
        for y in range(0, height, spacing):
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha), width=1)

        return ImageTk.PhotoImage(img)

    @staticmethod
    def static_noise(width, height, intensity=0.25):
        """Random static/noise texture for glitch moments."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pixels = img.load()

        alpha = int(255 * intensity)
        for y in range(height):
            for x in range(width):
                if random.random() < intensity:
                    v = random.randint(0, 80)
                    pixels[x, y] = (v, 0, 0, alpha)

        return ImageTk.PhotoImage(img)

    @staticmethod
    def chromatic_aberration(width, height, shift=4):
        """R/G/B channel-split image for screen-tear glitch aesthetic.
        Returns a PhotoImage with offset red and cyan fringes at edges."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Red fringe on the right edge
        red_alpha = 120
        for i in range(shift):
            x = width - shift + i
            draw.line([(x, 0), (x, height)], fill=(255, 0, 0, red_alpha), width=2)

        # Cyan/blue fringe on the left edge
        cyan_alpha = 100
        for i in range(shift):
            draw.line([(i, 0), (i, height)], fill=(0, 180, 255, cyan_alpha), width=2)

        return ImageTk.PhotoImage(img)

    @staticmethod
    def blood_drip_streak(width, height, count=6):
        """Vertical blood drip streaks oozing from top of screen."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        for _ in range(count):
            x = random.randint(30, width - 30)
            start_y = random.randint(0, height // 3)
            end_y = random.randint(start_y + 40, height)

            segments = random.randint(3, 8)
            px, py = x, start_y
            for _ in range(segments):
                nx = px + random.randint(-8, 8)
                ny = py + random.randint(15, 35)
                alpha = random.randint(60, 180)
                w = random.randint(2, 5)
                draw.line([(px, py), (nx, ny)], fill=(140, 5, 10, alpha), width=w)
                px, py = nx, ny

        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        return ImageTk.PhotoImage(img)

    @staticmethod
    def flesh_pulse_frame(width, height, pulse=0.5):
        """A subtle pulsing red border glow that fades inward."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        border_width = int(8 + pulse * 12)
        alpha = int(40 + pulse * 80)

        for i in range(border_width):
            a = int(alpha * (1 - i / border_width) ** 2)
            draw.rectangle(
                [i, i, width - i - 1, height - i - 1],
                outline=(200, 0, 20, a),
                width=1,
            )

        return ImageTk.PhotoImage(img)

    @staticmethod
    def scream_lines(width, height, count=30):
        """Radial lines emanating from center — psychological distress."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = width // 2, height // 2
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            length = random.randint(40, max(width, height))
            ex = cx + length * math.cos(angle)
            ey = cy + length * math.sin(angle)
            alpha = random.randint(20, 80)
            w = random.randint(1, 2)
            draw.line([(cx, cy), (ex, ey)], fill=(180, 0, 30, alpha), width=w)

        return ImageTk.PhotoImage(img)

    @staticmethod
    def cell_shade(width, height, grid=40):
        """Dark grid overlay for dungeon/cell atmosphere."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        for x in range(0, width, grid):
            draw.line([(x, 0), (x, height)], fill=(0, 0, 0, 40), width=1)
        for y in range(0, height, grid):
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, 40), width=1)

        return ImageTk.PhotoImage(img)

    @staticmethod
    def glitch_block(width, height, blocks=8):
        """Random opaque blocks that simulate data corruption slices."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        for _ in range(blocks):
            bx = random.randint(0, width - 60)
            by = random.randint(0, height - 30)
            bw = random.randint(40, 200)
            bh = random.randint(4, 20)
            color = (
                random.choice([200, 0, 50]),
                random.choice([0, 50]),
                random.choice([0, 50, 200]),
                random.randint(80, 180),
            )
            draw.rectangle([bx, by, bx + bw, by + bh], fill=color)

        return ImageTk.PhotoImage(img)

    @staticmethod
    def screen_tear(width, height, num_tears=8):
        """Generate horizontal CRT tear lines composed of digital white/red noise strips."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        for _ in range(num_tears):
            ty = random.randint(0, height - 15)
            th = random.randint(3, 12)
            # Draw horizontal static noise in this stripe
            for x in range(0, width, random.randint(1, 4)):
                if random.random() < 0.7:
                    c = random.choice([
                        (255, 255, 255, random.randint(100, 230)),
                        (200, 0, 0, random.randint(80, 200)),
                        (100, 100, 100, random.randint(50, 150))
                    ])
                    draw.rectangle([x, ty, x + random.randint(2, 10), ty + th], fill=c)
        return ImageTk.PhotoImage(img)

    @staticmethod
    def pixel_melt_layer(width, height, intensity=0.5):
        """Generate vertical melting tracks with red pixel trails and digital smear columns."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        num_drips = int(30 + intensity * 80)
        for _ in range(num_drips):
            x = random.randint(0, width - 5)
            y_start = random.randint(0, int(height * 0.8))
            length = random.randint(20, int(150 + intensity * 200))
            w = random.randint(1, 4)

            for dy in range(length):
                cy = y_start + dy
                if cy >= height:
                    break
                alpha_factor = 1.0 - (dy / length)
                alpha = int((100 + random.randint(0, 120)) * alpha_factor)
                cx = x + (random.randint(-1, 1) if random.random() < 0.1 else 0)

                color = (
                    int(180 + 75 * alpha_factor),
                    0,
                    int(10 + 20 * (1.0 - alpha_factor)),
                    alpha
                )
                draw.rectangle([cx, cy, cx + w - 1, cy + 1], fill=color)
        return ImageTk.PhotoImage(img)



# ══════════════════════════════════════════════════════════════════════════════
#  Canvas-based particle engine (ambient floating embers / dust motes)
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
#  Overlay manager — places / removes procedural overlay labels on a tkinter
#  container without leaking memory.
# ══════════════════════════════════════════════════════════════════════════════

class OverlayManager:
    """Manages a semi-transparent procedural overlay on a parent widget."""

    def __init__(self, parent):
        self.parent = parent
        self._label = None
        self._photo_ref = None
        self._after_id = None
        self._safety_id = None  # hard timeout failsafe (max 5s)

    def show(self, photo_image, duration_ms=None):
        self.hide()
        # 强制上限 5 秒，防止永久黑屏
        if duration_ms is None or duration_ms > 5000:
            duration_ms = 5000
        try:
            self._photo_ref = photo_image
            self._label = tk.Label(self.parent, image=photo_image, bg="#000000", bd=0,
                                   highlightthickness=0)
            self._label.place(x=0, y=0, relwidth=1, relheight=1)
            self._after_id = self.parent.after(duration_ms, self.hide)
            # 双重保险：硬超时兜底
            self._safety_id = self.parent.after(duration_ms + 2000, self._force_hide)
        except Exception:
            self._force_hide()

    def _force_hide(self):
        """硬超时兜底：不管什么状态，强制清除。"""
        self.hide()

    def hide(self):
        for tid in (self._after_id, self._safety_id):
            if tid is not None:
                try:
                    self.parent.after_cancel(tid)
                except Exception:
                    pass
        self._after_id = None
        self._safety_id = None

        if self._label is not None:
            try:
                self._label.destroy()
            except Exception:
                pass
            self._label = None
        self._photo_ref = None

    def force_clear(self):
        """紧急清除：忽略所有状态，强制销毁叠加层。"""
        self.hide()

    @property
    def visible(self):
        return self._label is not None


# ══════════════════════════════════════════════════════════════════════════════
#  Helper: create a procedural overlay sized to the current widget dimensions
# ══════════════════════════════════════════════════════════════════════════════

def get_widget_size(widget, fallback_w=1100, fallback_h=800):
    w = widget.winfo_width()
    h = widget.winfo_height()
    if w <= 100:
        w = fallback_w
    if h <= 100:
        h = fallback_h
    return w, h
