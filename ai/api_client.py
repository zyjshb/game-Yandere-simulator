# -*- coding: utf-8 -*-
"""
Standalone API client for fetching Saki's AI responses.

Runs in a background thread created by the caller.  No tkinter dependencies.
"""
import time
import random
import json
import re
import threading
import queue

from resources.game_constants import (
    normalize_language,
    detect_language,
    classify_player_intent,
    roll_delta_for_intent,
    MOCK_REPLY_BANK,
    translation_required,
    build_offline_translation_line,
    LANGUAGE_PROFILES,
)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Mock reply generator (standalone, no tkinter)
# ---------------------------------------------------------------------------

def _generate_mock_reply(user_input, selected_lang):
    """Generate an offline mock reply when no API key is configured.

    Uses the same MOCK_REPLY_BANK and intent classification as the full
    game so the offline experience stays consistent.
    """
    lang = normalize_language(selected_lang)
    user_lang = detect_language(user_input, lang)
    intent = classify_player_intent(user_input)
    delta_f, delta_s, delta_e = roll_delta_for_intent(intent)
    bank = MOCK_REPLY_BANK.get(lang, MOCK_REPLY_BANK["中文"])
    pool = bank.get(intent["name"], bank["default"])
    reply = random.choice(pool)

    if intent["name"] == "default" and len(user_input) <= 12 and random.random() < 0.35:
        if lang == "English":
            reply = (
                f"<think>He said '{user_input}'. A tiny phrase, but it still belongs to me now. "
                "Do not smother it. Let it breathe.</think>"
                f"You just said \"{user_input}\"... I heard it, my love. Say another small thing for me."
            )
        elif lang == "日本語":
            reply = (
                f"<think>彼は『{user_input}』と言った。小さな言葉でも、今は私のもの。壊さないように抱えておく。</think>"
                f"今、『{user_input}』って言ったね。ちゃんと聞こえたよ。もう少しだけ、紗希に声を聞かせて。"
            )
        else:
            reply = (
                f"<think>他刚才说了『{user_input}』。很短，可这是他主动交给我的声音。别贪心，先把这一秒留住。</think>"
                f"亲爱的刚才说\"{user_input}\"……纱希听见了哦。再说一句给我，好不好？"
            )

    if translation_required(lang, user_lang):
        reply += build_offline_translation_line(intent["name"], user_lang, reply)

    suffix = LANGUAGE_PROFILES[lang]["fallback_suffix"].format(
        delta_f=delta_f,
        delta_s=delta_s,
        delta_e=delta_e,
    )
    return f"{reply}{suffix}"


# ---------------------------------------------------------------------------
# Background API fetcher
# ---------------------------------------------------------------------------

def fetch_api_response(chat_history, api_key, base_url, model_name,
                       cycle_id, game_state, ui_queue):
    """Retrieve Saki's response via the LLM API in a background thread.

    Parameters
    ----------
    chat_history : list[dict]
        The full message history (role/content pairs).
    api_key : str
        API key (empty string means mock mode).
    base_url : str
        Base URL for the chat completions endpoint.
    model_name : str
        Model identifier (e.g. "deepseek-v4-flash").
    cycle_id : int
        Reincarnation token -- stale results are discarded.
    game_state : core.game_state.GameState
        Used to check cycle_id match before enqueuing.
    ui_queue : queue.Queue
        The application's UI dispatch queue.

    Queues
    ------
    On success        -> ("API_SUCCESS", reply_text, cycle_id)
    On API error      -> ("API_FALLBACK", (user_input, err_detail), cycle_id)
    When no API key   -> ("API_MOCK", mock_reply, cycle_id)
    """
    if cycle_id != game_state.cycle_id:
        return

    if not api_key:
        time.sleep(random.uniform(0.6, 1.2))
        if cycle_id != game_state.cycle_id:
            return
        mock_reply = _generate_mock_reply(
            game_state.last_user_input,
            game_state.cached_lang,
        )
        ui_queue.put((cycle_id, "API_MOCK", mock_reply))
        return

    if not HAS_REQUESTS:
        ui_queue.put((cycle_id, "API_ERROR",
                      "Missing requests package; install with: pip install requests"))
        return

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": chat_history,
            "temperature": 0.95,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=25,
                proxies={"http": None, "https": None},
            )
        except Exception as conn_err:
            err_str = str(conn_err).lower()
            if "proxy" in err_str or "proxyerror" in err_str:
                print("[Self-healing] Proxy error detected, retrying with direct connection...")
                response = requests.post(
                    url, headers=headers, json=payload, timeout=25,
                    proxies={"http": None, "https": None},
                )
            else:
                raise conn_err

        if response.status_code == 200:
            if cycle_id != game_state.cycle_id:
                return
            result_json = response.json()
            reply = result_json["choices"][0]["message"]["content"]
            ui_queue.put((cycle_id, "API_SUCCESS", reply))
        else:
            raise Exception(
                f"HTTP status: {response.status_code}, body: {response.text}"
            )

    except Exception as err:
        print(f"[API Request Error] {err}")
        time.sleep(0.5)
        if cycle_id != game_state.cycle_id:
            return
        ui_queue.put(
            (cycle_id, "API_FALLBACK",
             (game_state.last_user_input, str(err)))
        )
