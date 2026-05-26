# -*- coding: utf-8 -*-
"""
Thin wrapper around core.game_state.build_role_simulation_prompt.

Provides a single entry-point that extracts the relevant fields from a
GameState instance and delegates to the core prompt builder.
"""

from resources.game_constants import normalize_language, detect_language
from core.game_state import build_role_simulation_prompt


def get_system_prompt(game_state):
    """Build the full localized role-simulation system prompt.

    Parameters
    ----------
    game_state : core.game_state.GameState
        The current game state holding language, stats, and day.

    Returns
    -------
    str
        The complete system prompt ready to be placed at
        ``chat_history[0]["content"]``.
    """
    selected_lang = normalize_language(game_state.cached_lang)
    user_lang = detect_language(game_state.last_user_input, selected_lang)
    return build_role_simulation_prompt(
        selected_lang=selected_lang,
        user_lang=user_lang,
        current_day=game_state.current_day,
        favorability=game_state.favorability,
        suspicion=game_state.suspicion,
        escape_rate=game_state.escape_rate,
    )
