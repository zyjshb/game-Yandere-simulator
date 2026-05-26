# -*- coding: utf-8 -*-
import tkinter as tk


class PlaceholderEntry(tk.Entry):
    """A tkinter Entry widget that shows placeholder text when empty."""

    def __init__(self, master=None, placeholder="", placeholder_color="#555555",
                 default_color="#FF0000", show_char=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_color = default_color
        self.show_char = show_char

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg=self.placeholder_color)
            if self.show_char:
                self.config(show="")

    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(fg=self.default_color)
            if self.show_char:
                self.config(show=self.show_char)

    def _on_focus_out(self, event):
        if not self.get():
            self._show_placeholder()

    def get_actual_value(self):
        val = self.get()
        if val == self.placeholder:
            return ""
        return val

    def update_placeholder(self, new_placeholder):
        curr_val = self.get()
        if curr_val == self.placeholder or not curr_val:
            self.delete(0, tk.END)
            self.placeholder = new_placeholder
            self.insert(0, new_placeholder)
            self.config(fg=self.placeholder_color)
        else:
            self.placeholder = new_placeholder
