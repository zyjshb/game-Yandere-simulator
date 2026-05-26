# -*- coding: utf-8 -*-
"""
===============================================================================
  Overlay manager -- places / removes procedural overlay labels on a tkinter
  container without leaking memory.
===============================================================================
"""

import tkinter as tk


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
        # force upper limit 5 seconds to prevent permanent black screen
        if duration_ms is None or duration_ms > 5000:
            duration_ms = 5000
        try:
            self._photo_ref = photo_image
            self._label = tk.Label(self.parent, image=photo_image, bg="#000000", bd=0,
                                   highlightthickness=0)
            self._label.place(x=0, y=0, relwidth=1, relheight=1)
            self._after_id = self.parent.after(duration_ms, self.hide)
            # double insurance: hard timeout fallback
            self._safety_id = self.parent.after(duration_ms + 2000, self._force_hide)
        except Exception:
            self._force_hide()

    def _force_hide(self):
        """Hard timeout fallback: force clear regardless of state."""
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
        """Emergency clear: ignore all state, force destroy the overlay."""
        self.hide()

    @property
    def visible(self):
        return self._label is not None


# ---------------------------------------------------------------------------
#  Helper: create a procedural overlay sized to the current widget dimensions
# ---------------------------------------------------------------------------

def get_widget_size(widget, fallback_w=1100, fallback_h=800):
    w = widget.winfo_width()
    h = widget.winfo_height()
    if w <= 100:
        w = fallback_w
    if h <= 100:
        h = fallback_h
    return w, h
