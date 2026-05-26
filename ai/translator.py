# -*- coding: utf-8 -*-
"""
Parse raw API responses into structured game data.

Extracts the inner monologue (<think> block), spoken dialogue, and the
JSON delta payload that the LLM appended.
"""
import json
import re

from resources.game_constants import (
    normalize_language,
    detect_language,
    ensure_readability_translation,
)


def parse_api_response(raw_text, user_input, game_state):
    """Parse a raw LLM reply into structured components.

    Handles:
    * Splitting the ``||{...}||`` JSON suffix from the spoken text.
    * Regex fallback when the JSON block is malformed.
    * Extracting the ``<think>...</think>`` inner monologue.
    * Stripping residual ``||`` tokens from the spoken text.
    * Running ``ensure_readability_translation`` for bilingual output.

    Parameters
    ----------
    raw_text : str
        The exact text returned by the LLM.
    user_input : str
        The player's last message (used for language detection and
        translation heuristics).
    game_state : core.game_state.GameState
        Provides ``cached_lang`` for the current interface language.

    Returns
    -------
    dict
        Keys:
        - ``"think"`` : str  -- extracted inner monologue (may be empty).
        - ``"spoken"`` : str -- cleaned, translation-adjusted dialogue.
        - ``"delta"`` : dict or None -- raw JSON delta payload before
          normalization.
    """
    raw_delta = None
    spoken_text = raw_text

    # ---- 1. Split on the canonical || delimiter ----
    if "||" in raw_text:
        try:
            parts = raw_text.split("||")
            spoken_text = parts[0].strip()
            json_str = parts[1].strip()
            raw_delta = json.loads(json_str)
        except Exception:
            pass

    # ---- 2. Regex fallback: find a valid-looking delta block ----
    if raw_delta is None:
        match = re.search(r'\{[^{}]*"favorability"[^{}]*\}', raw_text)
        if match:
            try:
                raw_delta = json.loads(match.group(0))
                spoken_text = raw_text.replace(
                    match.group(0), ""
                ).replace("||", "").strip()
            except Exception:
                pass

    # ---- 3. Strip any residual || tokens from spoken text ----
    if "||" in spoken_text:
        spoken_text = spoken_text.split("||")[0].strip()

    # ---- 4. Extract <think>...</think> block ----
    think_content = ""
    lower_text = spoken_text.lower()
    start_idx = lower_text.find("<think>")
    if start_idx != -1:
        end_idx = lower_text.find("</think>", start_idx + 7)
        if end_idx != -1:
            think_content = spoken_text[start_idx + 7:end_idx].strip()
            spoken_text = (
                spoken_text[:start_idx] + " " + spoken_text[end_idx + 8:]
            )
        else:
            # Unclosed <think> -- take everything after it
            think_content = spoken_text[start_idx + 7:].strip()
            spoken_text = spoken_text[:start_idx]

    # ---- 5. Apply readability translation (bilingual output) ----
    selected_lang = normalize_language(game_state.cached_lang)
    user_lang = detect_language(user_input, selected_lang)
    spoken_text = ensure_readability_translation(
        spoken_text, selected_lang, user_lang, user_input,
    )

    return {
        "think": think_content,
        "spoken": spoken_text,
        "delta": raw_delta,
    }
