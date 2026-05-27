# -*- coding: utf-8 -*-
"""
Story mode chapter scripts aggregator.
Imports CHAPTER_SCRIPTS from all chapter modules and merges into one dict.
"""

CHAPTER_SCRIPTS = {}

# ---- Chapters 1-10 ----
try:
    from story_mode.chapters.ch01_10 import CHAPTER_SCRIPTS as _cs_01_10
    CHAPTER_SCRIPTS.update(_cs_01_10)
except ImportError:
    pass

# ---- Chapters 11-20 ----
try:
    from story_mode.chapters.ch11_20 import CHAPTER_SCRIPTS as _cs_11_20
    CHAPTER_SCRIPTS.update(_cs_11_20)
except ImportError:
    pass

# ---- Chapters 21-30 ----
try:
    from story_mode.chapters.ch21_30 import CHAPTER_SCRIPTS as _cs_21_30
    CHAPTER_SCRIPTS.update(_cs_21_30)
except ImportError:
    pass
