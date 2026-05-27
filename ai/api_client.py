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
    pool = bank.get(intent["name"], bank.get("affection", list(bank.values())[0] if bank else []))
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

        # Robust retry wrapper (up to 2 attempts, timeout=50s) to handle DeepSeek congestion
        response = None
        last_err = None
        for attempt in range(1, 3):
            if cycle_id != game_state.cycle_id:
                return
            try:
                print(f"[API Request] Attempt {attempt} to fetch Saki's reply (timeout=50)...")
                response = requests.post(
                    url, headers=headers, json=payload, timeout=50,
                    proxies={"http": None, "https": None},
                )
                if response.status_code == 200:
                    break
                else:
                    raise Exception(f"HTTP status: {response.status_code}, body: {response.text}")
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                print(f"[API Request] Attempt {attempt} failed: {e}")
                if "proxy" in err_str or "proxyerror" in err_str:
                    print("[Self-healing] Proxy error detected, retrying next attempt with direct connection...")
                time.sleep(1.0)

        if response is None or response.status_code != 200:
            if last_err:
                raise last_err
            else:
                raise Exception("API request failed after retries.")

        if response.status_code == 200:
            if cycle_id != game_state.cycle_id:
                return
            result_json = response.json()
            reply = result_json["choices"][0]["message"]["content"]

            # ---- Check and Auto-Heal Translation if Required ----
            lang = normalize_language(game_state.cached_lang)
            user_lang = detect_language(game_state.last_user_input, lang)

            if translation_required(lang, user_lang):
                # Avoid circular import at top level
                from ai.translator import parse_api_response
                from resources.game_constants import has_terminal_parenthetical_translation

                # Parse to see if translation is already present
                parsed = parse_api_response(reply, game_state.last_user_input, game_state)
                spoken_clean = parsed["spoken"].strip()

                # Check if it has a terminal parenthetical translation
                if not has_terminal_parenthetical_translation(spoken_clean, user_lang):
                    # Make a quick secondary API call to translate the spoken text
                    user_lang_name = "简体中文" if user_lang == "中文" else user_lang
                    source_lang_name = "日本語" if lang == "日本語" else lang

                    print(f"[Self-healing Translation] Translation missing from LLM response. Performing online translation via LLM...")

                    translation_payload = {
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    f"You are a precise, immersive translator for Saki, a text adventure yandere character. "
                                    f"Translate the following {source_lang_name} speech into natural, character-accurate {user_lang_name}. "
                                    f"Keep Saki's yandere tone, sweet but dangerous style. "
                                    f"Output ONLY the final translated text enclosed in full-width brackets `（ ）`, without any explanations, narration, or extra text."
                                )
                            },
                            {
                                "role": "user",
                                "content": spoken_clean
                            }
                        ],
                        "temperature": 0.5,
                    }

                    translation_text = None
                    trans_last_err = None
                    for trans_attempt in range(1, 3):
                        if cycle_id != game_state.cycle_id:
                            return
                        try:
                            print(f"[Self-healing Translation] Attempt {trans_attempt} to translate Saki's reply (timeout=30)...")
                            trans_response = requests.post(
                                url, headers=headers, json=translation_payload, timeout=30,
                                proxies={"http": None, "https": None},
                            )
                            if trans_response.status_code == 200:
                                trans_result = trans_response.json()
                                translation_text = trans_result["choices"][0]["message"]["content"].strip()
                                break
                            else:
                                raise Exception(f"HTTP status: {trans_response.status_code}, body: {trans_response.text}")
                        except Exception as e:
                            trans_last_err = e
                            print(f"[Self-healing Translation] Attempt {trans_attempt} failed: {e}")
                            time.sleep(1.0)

                    if translation_text:
                        # Ensure translation is enclosed in parentheses
                        if not (translation_text.startswith("（") and translation_text.endswith("）")):
                            translation_text = f"（{translation_text.strip('（）()')}）"
                        print(f"[Self-healing Translation] Successfully generated online translation: {translation_text}")
                    else:
                        # Character-accurate immersive fallback messages for translation timeouts to maintain immersion
                        print(f"[Self-healing Translation Error] Failed to generate translation online after retries: {trans_last_err}")
                        if user_lang == "中文":
                            translation_text = "（亲爱的……纱希刚才说的那些话，翻译好像在网络中迷路了。不过别担心，纱希的心意是永远不会迷路的哦……❤）"
                        elif user_lang == "English":
                            translation_text = "（My love... Saki's translation seems to have gotten lost in the network. But don't worry, Saki's heart will never lose its way to you...❤）"
                        elif user_lang == "日本語":
                            translation_text = "（あなた……紗希の翻訳がネットで迷子になっちゃったみたい。でも心配しないで、私の想いは絶対に迷子にならないから……❤）"
                        else:
                            translation_text = "（Translation loading...）"

                    # Reconstruct the reply with translation
                    think_part = f"<think>{parsed['think']}</think>\n" if parsed["think"] else ""

                    delta_part = ""
                    if parsed["delta"]:
                        delta_part = f"\n||{json.dumps(parsed['delta'])}||"

                    reply = f"{think_part}{spoken_clean}\n{translation_text}{delta_part}"

            ui_queue.put((cycle_id, "API_SUCCESS", reply))

    except Exception as err:
        print(f"[API Request Error] {err}")
        time.sleep(0.5)
        if cycle_id != game_state.cycle_id:
            return
        ui_queue.put(
            (cycle_id, "API_FALLBACK",
             (game_state.last_user_input, str(err)))
        )
