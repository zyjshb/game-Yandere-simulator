# -*- coding: utf-8 -*-
from tkinter import ttk


def configure_styles(style):
    """Set up all ttk widget styles for the game (Favor, Sus, Esc progress bars, scrollbar, etc.).

    Parameters
    ----------
    style : ttk.Style
        The ttk.Style instance to configure (typically created on the root Tk window).
    """
    style.theme_use("clam")
    style.configure(".", background="#000000", foreground="#CC0000")
    style.configure("TFrame", background="#000000")

    style.configure(
        "Favor.Horizontal.TProgressbar",
        thickness=10,
        troughcolor="#111111",
        background="#CC0000",
        bordercolor="#000000",
        lightcolor="#FF0000",
        darkcolor="#8A0303",
    )
    style.configure(
        "Sus.Horizontal.TProgressbar",
        thickness=10,
        troughcolor="#111111",
        background="#8A0303",
        bordercolor="#000000",
        lightcolor="#CC0055",
        darkcolor="#3A001F",
    )
    style.configure(
        "Esc.Horizontal.TProgressbar",
        thickness=10,
        troughcolor="#111111",
        background="#00AA00",
        bordercolor="#000000",
        lightcolor="#2ECC71",
        darkcolor="#0E6251",
    )

    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background="#151515",
        troughcolor="#000000",
        bordercolor="#000000",
        lightcolor="#000000",
        darkcolor="#000000",
        arrowcolor="#8A0303",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", "#252525"), ("pressed", "#353535")],
    )
