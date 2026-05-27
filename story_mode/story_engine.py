# -*- coding: utf-8 -*-
"""
Story mode engine for offline play.
Provides chapter-driven narrative replies when no API key is configured.
"""

import random
from resources.game_constants import normalize_language, classify_player_intent
from story_mode.story_data import CHAPTER_META, BRANCH_THRESHOLD, ROUTE_LABELS


def determine_route(game_state):
    fav = game_state.favorability
    sus = game_state.suspicion
    esc = game_state.escape_rate
    if fav >= BRANCH_THRESHOLD["affection"]["favorability"] and sus <= BRANCH_THRESHOLD["affection"]["suspicion_max"]:
        return "affection"
    if esc >= BRANCH_THRESHOLD["escape"]["escape_rate"]:
        return "escape"
    if fav <= BRANCH_THRESHOLD["darkness"]["favorability_max"] or sus >= BRANCH_THRESHOLD["darkness"]["suspicion"]:
        return "darkness"
    return None


def get_current_chapter(game_state):
    day = game_state.current_day
    if day <= 0:
        day = 1
    if day > 30:
        day = 30
    return day


def get_story_reply(player_input, game_state):
    chapter = get_current_chapter(game_state)
    lang = normalize_language(game_state.cached_lang)

    from story_mode.chapters import CHAPTER_SCRIPTS
    scripts = CHAPTER_SCRIPTS.get(chapter, {})

    if not scripts:
        return _fallback_reply(player_input, lang)

    intent = classify_player_intent(player_input)
    intent_name = intent["name"]
    route = determine_route(game_state)

    # Chapter 17-30: route-based selection
    if chapter >= 17 and route:
        pool = scripts.get(route, [])
    else:
        pool = scripts.get(intent_name, scripts.get("default", []))

    if not pool:
        pool = scripts.get("default", [])

    if not pool:
        return _fallback_reply(player_input, lang)

    return random.choice(pool)


def _fallback_reply(user_input, lang):
    from ai.api_client import _generate_mock_reply
    return _generate_mock_reply(user_input, lang)


def get_chapter_title(chapter):
    meta = CHAPTER_META.get(chapter, {})
    return meta.get("title", f"第{chapter}章")


def get_route_label(route):
    return ROUTE_LABELS.get(route, "")
