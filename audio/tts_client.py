# -*- coding: utf-8 -*-
"""
Standalone GPT-SoVITS TTS client: probe the best endpoint and synthesize
speech as raw WAV bytes.  No tkinter or pygame dependencies.
"""

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from resources.game_constants import (
    clean_text_for_tts,
    language_to_tts_code,
    detect_language,
    build_tts_request_params,
    TTS_QUALITY_PARAMS,
)


def probe_tts_endpoint(gpt_sovits_url, refer_wav_path, prompt_text):
    """
    Probe available TTS endpoints on the GPT-SoVITS server and return the
    first working path (e.g. "/tts", "/tts_to_audio", or "").
    Returns the default "/tts" if nothing is reachable.
    """
    if not HAS_REQUESTS:
        return "/tts"

    url = gpt_sovits_url.rstrip("/")
    endpoints = ["/tts", "/tts_to_audio", ""]

    ref_lang = detect_language(prompt_text)
    prompt_lang_code = language_to_tts_code(ref_lang)
    params = build_tts_request_params(
        refer_wav_path,
        prompt_text,
        prompt_lang_code,
        "hello",
        "zh",
        quality=False,
    )

    for ep in endpoints:
        target_url = f"{url}{ep}"
        try:
            res = requests.get(target_url, params=params, timeout=2.5,
                              proxies={"http": None, "https": None})
            if res.status_code == 200:
                print(f"[tts] endpoint probe succeeded: {target_url}")
                return ep
        except Exception:
            pass

    print("[tts] probe finished, no active endpoint found; defaulting to /tts")
    return "/tts"


def synthesize_speech(text, refer_wav_path, prompt_text, gpt_sovits_url,
                      target_lang_code, working_endpoint):
    """
    Send a synthesis request to GPT-SoVITS and return the raw WAV bytes.

    Returns the bytes on success, or None on any failure.
    Handles quality-parameter fallback automatically.
    """
    if not HAS_REQUESTS:
        return None

    cleaned = clean_text_for_tts(text)
    if not cleaned:
        print("[tts] text empty after cleaning; skipping synthesis")
        return None

    ref_lang = detect_language(prompt_text)
    prompt_lang_code = language_to_tts_code(ref_lang)

    target_url = f"{gpt_sovits_url.rstrip('/')}{working_endpoint}"

    # High-quality attempt first
    params = build_tts_request_params(
        refer_wav_path,
        prompt_text,
        prompt_lang_code,
        cleaned,
        target_lang_code,
        quality=True,
    )

    print(
        f"[tts] synthesizing: {target_url} "
        f"lang={target_lang_code} ref_lang={prompt_lang_code} text={cleaned}"
    )

    try:
        res = requests.get(target_url, params=params, timeout=15,
                          proxies={"http": None, "https": None})
    except Exception as ex:
        print(f"[tts] synthesis request failed: {ex}")
        return None

    # Fallback to basic params on non-200
    if res is not None and res.status_code not in (200,):
        fallback_params = build_tts_request_params(
            refer_wav_path,
            prompt_text,
            prompt_lang_code,
            cleaned,
            target_lang_code,
            quality=False,
        )
        print(f"[tts] quality params rejected (HTTP {res.status_code}); retrying with basic params")
        try:
            res = requests.get(target_url, params=fallback_params, timeout=15,
                              proxies={"http": None, "https": None})
        except Exception as ex:
            print(f"[tts] fallback request failed: {ex}")
            return None

    if res and res.status_code == 200 and len(res.content) > 1000:
        return res.content

    if res is not None:
        print(f"[tts] synthesis failed: HTTP {res.status_code}, content size {len(res.content)}")
    else:
        print("[tts] synthesis failed: could not reach GPT-SoVITS server")

    return None
