# -*- coding: utf-8 -*-
"""
MainWindow -- the primary game application window that owns all UI widgets,
manages game state, processes API responses, drives typewriter/TTS, and
orchestrates all horror/glitch visual effects.

Built on top of the modular ai / audio / core / resources / visual_fx / ui
packages extracted from yandere_game.py.
"""

import os
import sys
import time
import math
import random
import queue
import json
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from resources.localization import LOCALIZATION
from resources.game_constants import (
    normalize_language,
    detect_language,
    classify_player_intent,
    roll_delta_for_intent,
    coerce_int,
    coerce_bool,
    clamp_to_range,
    clean_text_for_tts,
    language_to_tts_code,
    build_tts_request_params,
    same_language,
    translation_required,
    build_offline_translation_line,
    ensure_readability_translation,
    strip_terminal_parenthetical_translation,
    extract_terminal_parenthetical_translation,
    has_terminal_parenthetical_translation,
    build_translation_rule,
    glitch_text,
    LANGUAGE_PROFILES,
    MOCK_REPLY_BANK,
    API_ERROR_REPLIES,
    INITIAL_GREETINGS,
    GLITCH_LOCALIZATION,
    TTS_QUALITY_PARAMS,
    SUPPORTED_LANGUAGES,
)

from core.config import load_config, save_config
from core.game_state import (
    GameState,
    build_role_simulation_prompt,
    normalize_delta_payload,
    _calculate_fallback_deltas,
)

from ai.api_client import fetch_api_response
from ai.prompt_builder import get_system_prompt
from ai.translator import parse_api_response

from audio.sound_manager import SoundManager
from audio.tts_client import probe_tts_endpoint, synthesize_speech
from audio.heartbeat_gen import generate_heartbeat_wav

from visual_fx import ProceduralFX, ParticleEngine, OverlayManager, get_widget_size
from visual_fx.glitch_controller import GlitchController

from ui.styles import configure_styles
from ui.custom_widgets import PlaceholderEntry
from ui.ecg_canvas import ECGCanvas

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ============================================================================
#               Global Asynchronous Save/Load Slots Functions
# ============================================================================
_ACTIVE_APP_INSTANCE = None

def save_slot1():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.save_slot1()

def save_slot2():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.save_slot2()

def save_slot3():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.save_slot3()

def save_slot4():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.save_slot4()

def save_slot5():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.save_slot5()

def load_slot1():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.load_slot1()

def load_slot2():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.load_slot2()

def load_slot3():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.load_slot3()

def load_slot4():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.load_slot4()

def load_slot5():
    if _ACTIVE_APP_INSTANCE:
        _ACTIVE_APP_INSTANCE.load_slot5()


DEFAULT_LANGUAGE_VOICES = {
    "中文": {
        "refer_wav_path": "models/hua/huahuo.wav_0000061760_0000188480.wav",
        "prompt_text": "你要是有什么危险的差事要办，尽管来找我。",
        "gpt_weights_path": "models/Huahuo_Yandere-e15.ckpt",
        "sovits_weights_path": "models/Huahuo_Yandere_e10_s440.pth"
    },
    "日本語": {
        "refer_wav_path": "models/mi/mita.wav_0000000000_0000261440.wav",
        "prompt_text": "どうして、また、た、わかった、またか、中身が気になるんでしょ?",
        "gpt_weights_path": "models/mita-e15.ckpt",
        "sovits_weights_path": "models/mita_e10_s860.pth"
    },
    "English": {
        "refer_wav_path": "models/hua/huahuo.wav_0000061760_0000188480.wav",
        "prompt_text": "你要是有什么危险的差事要办，尽管来找我。",
        "gpt_weights_path": "models/Huahuo_Yandere-e15.ckpt",
        "sovits_weights_path": "models/Huahuo_Yandere_e10_s440.pth"
    }
}


# ============================================================================
#                            MainWindow Class
# ============================================================================

class MainWindow:
    """The main game application window.

    Owns all tkinter widgets, manages GameState, SoundManager,
    GlitchController, OverlayManager, and the UI dispatch queue.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("纱希...对你的爱...永远不会消失...")
        self.root.geometry("1100x800")
        self.root.minsize(500, 450)
        self.root.configure(bg="#000000")

        # ---- config ----
        self.config = load_config()

        # ---- game state (core RPG stats + lang cache) ----
        self.state = GameState()
        self.state.cached_lang = normalize_language(
            self.config.get("selected_language", "中文")
        )

        # ---- language UI binding (StringVar kept on main thread only) ----
        self.selected_language = tk.StringVar(
            value=normalize_language(self.config.get("selected_language", "中文"))
        )
        self.user_explicitly_selected_lang = "selected_language" in self.config

        # ---- TTS / audio config ----
        self.gpt_sovits_url = self.config.get("gpt_sovits_url", "http://127.0.0.1:9880")
        self.refer_wav_path = self.config.get(
            "refer_wav_path",
            "models/hua/huahuo.wav_0000061760_0000188480.wav",
        )
        self.prompt_text = self.config.get("prompt_text", "你要是有什么危险的差事要办，尽量来找我。")
        self.gpt_weights_path = self.config.get("gpt_weights_path", "")
        self.sovits_weights_path = self.config.get("sovits_weights_path", "")

        # ---- horror / visual flags ----
        self.state.ecg_frenzy = False
        self.state.think_jitter = False
        self.state.shaking = False
        self.mouse_tremor_active = False
        self.mouse_pull_active = False
        self.meltdown_active = False
        self.barrage_active = False
        self.psychic_strobe_active = False
        self.state.ecg_flatline_active = False
        self.state.dripping_blood_active = False
        self.state.dripping_blood_lines = []
        self.state.scanlines_active = False
        self.state.snow_noise_active = False
        self.state.fake_error_active = False
        self.glitch_rune_active = False
        self.glitch_font_shake_active = False
        self.typewriter_speed_mult = 1.0
        self.carnage_labels = []

        # ---- internal ----
        self.chat_history = [{"role": "system", "content": ""}]
        self.ui_queue = queue.Queue()
        self.is_typing = False
        self.settings_visible = False
        self.ecg_time = 0.0

        # ---- danger words (trigger ECG frenzy + shake) ----
        self.danger_words = [
            "死", "杀", "背叛", "离开", "谁", "别的人", "小黑屋", "逃", "小刀",
            "滚", "锁", "洗澡", "地下室", "老子",
        ]

        # ---- procedural visual FX ----
        self.overlay_mgr = OverlayManager(self.root)
        self._particle_engine = None
        self._border_pulse_active = False
        self._flood_canvas_ref = None

        # ---- glitch controller (stub; wire later if needed) ----
        self.glitch_ctrl = GlitchController(self)

        # ---- sound manager ----
        self.sound_mgr = SoundManager()

        # ---- queue polling ----
        self.root.after(20, self._process_ui_queue)

        # ---- styles and UI build ----
        self.style = ttk.Style()
        configure_styles(self.style)
        self._build_ui()

        # ---- start visual / audio loops ----
        self._start_ecg_animation()
        self._init_and_play_audio()
        self._start_crt_flicker_loop()
        self._start_particle_engine()
        self._start_border_pulse_loop()

        # ---- cleanup orphaned temp files ----
        self._clean_orphaned_temp_files()

        # ---- probe TTS endpoint ----
        self.working_endpoint = "/tts"
        self._probe_tts_endpoint()

        # ---- window resize monitor / escape ----
        self.root.bind("<Configure>", self._on_window_resized)
        self.root.bind("<Escape>", lambda e: self._on_esc_pressed())

        # ---- set active app instance for global save/load access ----
        global _ACTIVE_APP_INSTANCE
        _ACTIVE_APP_INSTANCE = self

        # ---- Bindings for save/load/character swap ----
        self.root.bind("<Control-F1>", lambda e: self.save_slot1())
        self.root.bind("<Control-F2>", lambda e: self.save_slot2())
        self.root.bind("<Control-F3>", lambda e: self.save_slot3())
        self.root.bind("<Control-F4>", lambda e: self.save_slot4())
        self.root.bind("<Control-F5>", lambda e: self.save_slot5())
        self.root.bind("<Alt-F1>", lambda e: self.load_slot1())
        self.root.bind("<Alt-F2>", lambda e: self.load_slot2())
        self.root.bind("<Alt-F3>", lambda e: self.load_slot3())
        self.root.bind("<Alt-F4>", lambda e: self._on_alt_f4())
        self.root.bind("<Alt-F5>", lambda e: self.load_slot5())
        self.root.bind("<Control-Alt-c>", lambda e: self.toggle_character())
        self.root.bind("<F12>", lambda e: self.toggle_character())

        # ---- Bind entry keypress hijack for 4th wall break ----
        self.entry_input.bind("<KeyPress>", self._on_entry_key_press)

        # ---- Start background fourth-wall monitor ----
        self._start_fourth_wall_monitor()

        # ---- splash screen ----
        self.root.after(100, self._show_splash_screen)

    # ========================================================================
    #  Queue helpers
    # ========================================================================

    def _queue_ui(self, action, data=None, cycle_id=None):
        """Enqueue a UI action with a reincarnation token so stale results are discarded."""
        if cycle_id is None:
            cycle_id = self.state.cycle_id
        self.ui_queue.put((cycle_id, action, data))

    def _clear_ui_queue(self):
        """Drain all pending UI actions."""
        try:
            while True:
                self.ui_queue.get_nowait()
        except queue.Empty:
            pass

    def _enqueue_saki_response(self, text):
        """Queue an immediate response from Saki (e.g. initial greeting)."""
        self._set_typing_state(True)
        self._queue_ui("API_SUCCESS", text)

    # ========================================================================
    #  System prompt (delegates to ai.prompt_builder)
    # ========================================================================

    def _get_dynamic_system_prompt(self):
        char_id = getattr(self.state, "current_char_id", "saki")
        base_prompt = get_system_prompt(self.state)

        # Check if it's a custom character from custom_characters.json
        custom_chars = {}
        if os.path.exists("custom_characters.json"):
            try:
                with open("custom_characters.json", "r", encoding="utf-8") as f:
                    custom_chars = json.load(f)
            except Exception:
                pass

        if char_id in custom_chars:
            cdata = custom_chars[char_id]
            name = cdata.get("name", "自定义角色")
            age = cdata.get("age", "18")
            personality = cdata.get("personality", "偏执、极度敏感的病娇，占有欲极强")
            main_story = cdata.get("main_story", "将你关在密室里")
            character_plot = cdata.get("character_plot", "只要你顺从就温柔，一旦你想走就爆发疯狂")
            world_view = cdata.get("world_view", "阴暗冷酷的地牢")

            prompt = base_prompt
            prompt = prompt.replace("扮演纱希 Saki", f"扮演{name}")
            prompt = prompt.replace("扮演纱希Saki", f"扮演{name}")
            prompt = prompt.replace("扮演Saki", f"扮演{name}")
            prompt = prompt.replace("扮演 纱希 Saki", f"扮演{name}")
            prompt = prompt.replace("纱希 Saki", name)
            prompt = prompt.replace("Saki", name)
            prompt = prompt.replace("纱希", name)
            prompt = prompt.replace("病娇少女", "病娇角色")
            prompt = prompt.replace("她对玩家有强烈依恋", "该角色对玩家有强烈依恋")
            prompt = prompt.replace("她对玩家", "该角色对玩家")
            prompt = prompt.replace("她", "该角色")
            prompt = prompt.replace("乖猫咪", "心爱之人")

            injection = (
                f"\n\n【自定义角色脑回路设定】\n"
                f"- 角色姓名：{name}\n"
                f"- 角色年龄：{age}\n"
                f"- 角色性格：{personality}\n"
                f"- 故事主线：{main_story}\n"
                f"- 人物剧情：{character_plot}\n"
                f"- 世界观：{world_view}\n\n"
                f"注意：你现在扮演的是 {name}。你必须严格按照以上性格、背景、主线和剧情设定来进行模拟。"
                f"你的台词和语气必须极其契合该角色，并保持高焦虑值/高疑心值时的偏执与病娇特质。"
            )

            if "【输出的结构具体示例" in prompt:
                parts = prompt.split("【输出的结构具体示例")
                prompt = parts[0] + injection + "\n\n【输出的结构具体示例" + parts[1]
            elif "【OUTPUT STRUCTURE" in prompt:
                parts = prompt.split("【OUTPUT STRUCTURE")
                prompt = parts[0] + injection + "\n\n【OUTPUT STRUCTURE" + parts[1]
            else:
                prompt += injection
        else:
            filename = f"{char_id}_settings.txt"
            if not os.path.exists(filename):
                try:
                    default_content = (
                        "纱希是性格极端、敏感的病娇少女。她对玩家抱有病态的、毁灭性的爱与占有欲，对你的一言一行都会极度敏感地过度解读。\n"
                        "她害怕失去你，表层温柔顺从，内里却充满强烈的不安全感与随时可能爆发的疯狂狂躁。\n"
                        "如果发现你想逃跑或提起别人，她会瞬间黑化，用极度压抑或狂暴的态度面对你，甚至产生自毁与毁灭你的可怕念头。\n"
                    )
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(default_content)
                except Exception as e:
                    print(f"[写入角色设定文件失败] {e}")

            char_setting = ""
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        char_setting = f.read().strip()
                except Exception as e:
                    print(f"[读取角色设定文件失败] {e}")

            prompt = base_prompt
            injection = f"\n\n【纱希专属性格作息设定】\n{char_setting}\n"
            if "【输出的结构具体示例" in prompt:
                parts = prompt.split("【输出的结构具体示例")
                prompt = parts[0] + injection + "\n\n【输出的结构具体示例" + parts[1]
            elif "【OUTPUT STRUCTURE" in prompt:
                parts = prompt.split("【OUTPUT STRUCTURE")
                prompt = parts[0] + injection + "\n\n【OUTPUT STRUCTURE" + parts[1]
            else:
                prompt += injection

        # 2. Local insult emotional back-attack injection
        if getattr(self.state, "local_insult_back_attack", False):
            prompt += (
                "\n\n【系统提示（强制要求）：玩家刚刚对你说了极具侮辱和排斥的话，请立刻对此表现出极其偏执、心碎和暴怒的情绪！"
                "内心痛苦失控，说话时流露出受伤而疯狂的神色。同时，你末尾输出的 JSON 变化值（delta）中，"
                "必须将好感度 favorability 设为大幅负数（例如 -20 到 -45 的负整数），将疑心度 suspicion 设为大幅正数（例如 +15 到 +40 的正整数）！】\n"
            )
            # Reset flag
            self.state.local_insult_back_attack = False

        # 3. Local submission emotional prompt injection
        if getattr(self.state, "local_submission_prompt", False):
            prompt += (
                "\n\n【系统提示（玩家臣服顺从）：玩家的精神已被你彻底击垮，他不仅没有反抗你的键盘劫持，"
                "反而主动发送了你逼迫他打出的执念之语！请立刻感到无与伦比的病态狂喜与彻底的征服满足感！"
                "在回复中用最温柔、极度宠溺的语气安抚他，并且你末尾输出的 JSON 中，"
                "必须将好感 favorability 设为大幅正数（如 +15 到 +30），将疑心 suspicion 设为大幅负数（如 -20 到 -40）！】\n"
            )
            # Reset flag
            self.state.local_submission_prompt = False

        return prompt

    # ========================================================================
    #  Audio init
    # ========================================================================

    def _init_and_play_audio(self):
        if not HAS_PYGAME:
            lang = normalize_language(self.selected_language.get())
            self._write_chat_log(LOCALIZATION[lang]["sys_audio_missing"], "system")
            return

        def audio_thread_worker():
            self.sound_mgr.init_heartbeat("heartbeat.wav")

        threading.Thread(target=audio_thread_worker, daemon=True).start()

    # ========================================================================
    #  TTS endpoint probing
    # ========================================================================

    def _probe_tts_endpoint(self):
        if not HAS_REQUESTS:
            return

        def prober():
            abs_refer_wav = os.path.abspath(self.refer_wav_path) if self.refer_wav_path else ""
            self.working_endpoint = probe_tts_endpoint(
                self.gpt_sovits_url, abs_refer_wav, self.prompt_text
            )

        threading.Thread(target=prober, daemon=True).start()

    # ========================================================================
    #  Cleanup orphaned temp files
    # ========================================================================

    def _clean_orphaned_temp_files(self):
        try:
            for file in os.listdir("."):
                if file.startswith("temp_saki_") and file.endswith(".wav"):
                    try:
                        os.remove(file)
                    except Exception:
                        pass
        except Exception:
            pass

    # ========================================================================
    #  ECG animation (delegates to ECGCanvas)
    # ========================================================================

    def _start_ecg_animation(self):
        """Called from __init__ -- the ECGCanvas handles its own animation loop."""
        # The canvas was created in _build_ui, so the animation is already running.
        pass

    # ========================================================================
    #  Particle engine
    # ========================================================================

    def _start_particle_engine(self):
        self.canvas_ecg.start_particle_engine(count=30)

    def _stop_particle_engine(self):
        self.canvas_ecg.stop_particle_engine()

    # ========================================================================
    #  Border pulse loop
    # ========================================================================

    def _start_border_pulse_loop(self):
        # 彻底关停后台高频红边闪烁循环，杜绝任何持续性背景乱闪，完美契合用户安静高级的设计诉求
        pass

    # ========================================================================
    #  CRT flicker loop
    # ========================================================================

    def _start_crt_flicker_loop(self):
        # 彻底关停后台高频CRT背景闪动循环，防止任何刺眼背景闪烁，只保留老式静止暗黑质感
        pass

    # ========================================================================
    #  Panel fade-in animation
    # ========================================================================

    def _animate_panel_fade_in(self):
        labels = []
        for child in self.settings_frame.winfo_children():
            if isinstance(child, tk.Label):
                labels.append(child)
            elif isinstance(child, tk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, (tk.Label, tk.Button)):
                        labels.append(sub)

        steps = 10
        delay = 40

        def fade(step=0):
            if step > steps:
                return
            ratio = step / steps
            gray_val = int(45 + ratio * 57)
            color_gray = f"#{gray_val:02x}{gray_val:02x}{gray_val:02x}"
            red_val = int(50 + ratio * 205)
            color_red = f"#{red_val:02x}0000"
            for lbl in labels:
                try:
                    text = lbl.cget("text")
                    if text in ("语音状态:", "TTS Status:", "音声状态:"):
                        lbl.config(fg=color_gray)
                    elif any(kw in str(text) for kw in ["API", "MODEL", "TTS", "参考", "模型", "Model", "Ref"]):
                        lbl.config(fg=color_gray)
                    elif "热加载" in str(text) or "加载成功" in str(text) or "Loaded" in str(text):
                        pass
                    else:
                        lbl.config(fg=color_red)
                except Exception:
                    pass
            self.root.after(delay, lambda: fade(step + 1))

        fade()

    # ========================================================================
    #  UI dispatch loop (runs every 20ms on main thread)
    # ========================================================================

    def _process_ui_queue(self):
        try:
            while True:
                item = self.ui_queue.get_nowait()
                if len(item) == 3:
                    msg_cycle, action, data = item
                    if msg_cycle != self.state.cycle_id:
                        continue
                else:
                    action, data = item
                if action == "TRIGGER_MOVE":
                    self.root.geometry(f"+{data[0]}+{data[1]}")
                else:
                    self._dispatch_ordinary_action(action, data)
        except queue.Empty:
            pass
        self.root.after(20, self._process_ui_queue)

    # ========================================================================
    #  Central action dispatcher
    # ========================================================================

    def _dispatch_ordinary_action(self, action, data):
        if action == "API_SUCCESS":
            raw_text = data
            parsed = parse_api_response(raw_text, self.state.last_user_input, self.state)
            think_content = parsed["think"]
            spoken_text = parsed["spoken"]
            delta_data = parsed["delta"]

            delta_data = normalize_delta_payload(delta_data)
            if not delta_data:
                delta_data = _calculate_fallback_deltas(self.state.last_user_input)
            else:
                for key in ("favorability", "suspicion", "escape_rate"):
                    if key in delta_data:
                        delta_data[key] = clamp_to_range(delta_data[key], -100, 100)

            self._update_game_stats(delta_data)
            self.trigger_glitch_effect()
            self._start_typewriter_effect(think_content, spoken_text)

        elif action == "API_MOCK":
            raw_text = data
            self._write_chat_log("[local fallback]\n", "system")
            parsed = parse_api_response(raw_text, self.state.last_user_input, self.state)
            think_content = parsed["think"]
            spoken_text = parsed["spoken"]
            delta_data = parsed["delta"]

            delta_data = normalize_delta_payload(delta_data)
            if not delta_data:
                delta_data = _calculate_fallback_deltas(self.state.last_user_input)

            self._update_game_stats(delta_data)
            self._start_typewriter_effect(think_content, spoken_text)

        elif action == "API_FALLBACK":
            user_input, err_detail = data
            lang = normalize_language(self.selected_language.get())
            self._write_chat_log(
                LOCALIZATION[lang]["sys_fallback"].format(err=err_detail), "system"
            )
            mock_reply = self._generate_mock_reply(user_input)
            self._queue_ui("API_MOCK", mock_reply)

        elif action == "API_ERROR":
            lang = normalize_language(self.selected_language.get())
            error_msg = API_ERROR_REPLIES[lang]
            self._write_chat_log(
                LOCALIZATION[lang]["sys_api_error_title"].format(err=data), "system"
            )
            self._start_typewriter_effect("", error_msg)

        elif action == "CHAR_RENDER":
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, data, "saki")
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

        elif action == "CHAR_RENDER_THINK":
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, data, "think")
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

        elif action == "CHAR_RENDER_RUNE":
            rune, correct_char = data
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, rune, "saki")
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

            def restore_char():
                self.chat_text.config(state=tk.NORMAL)
                try:
                    pos = self.chat_text.index("end-2c")
                    self.chat_text.delete(pos)
                    self.chat_text.insert(pos, correct_char, "saki")
                except Exception:
                    pass
                self.chat_text.config(state=tk.DISABLED)

            self.root.after(100, restore_char)

        elif action == "CHAR_RENDER_TAGGED":
            char, tag = data
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, char, tag)
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

        elif action == "TTS_STATUS_UPDATE":
            msg, color = data
            self.lbl_tts_status.config(text=msg, fg=color)

        elif action == "TRIGGER_LOAD_WEIGHTS":
            weight_type, filepath = data
            self._async_load_weights(weight_type, filepath)

        elif action == "TRIGGER_SHAKE":
            self._start_physical_shake()

        elif action == "TRIGGER_GLITCH":
            self.trigger_glitch_effect()

        elif action == "TRIGGER_STROBE":
            self._psychic_strobe(300, 1300)

        elif action == "TRIGGER_BARRAGE":
            self._start_obsessive_barrage(1.0)

        elif action == "TRIGGER_MELT_OVERLAY":
            self._trigger_melt_overlay(1200)

        elif action == "TRIGGER_MOUSE_TREMOR":
            self._trigger_mouse_tremor(1500)

        elif action == "TRIGGER_FAKE_ERROR":
            self._trigger_fake_error_popup()

        elif action == "TRIGGER_MELTDOWN":
            self._start_widget_meltdown(1.5)

        elif action == "TRIGGER_MOUSE_PULL":
            self._start_mouse_magnetic_pull(1.5)

        elif action == "CHAR_RENDER_CARNAGE":
            self._render_overlapping_text(data)

        elif action == "RENDER_DONE":
            final_text = data
            self._set_typing_state(False)
            self.glitch_rune_active = False
            self.glitch_font_shake_active = False
            self.chat_history.append({"role": "assistant", "content": final_text})
            if self.state.pending_ending:
                self._show_ending_overlay(final_text)
            else:
                self._on_dialogue_completed()

    # ========================================================================
    #  On send (user input)
    # ========================================================================

    def _on_send(self):
        if self.is_typing or self.state.game_over:
            return

        # 立即在发送新消息前紧急清理所有上一轮的黑屏遮罩与视觉残留，实现绝对干净自愈
        self._emergency_clear_overlays()

        user_text = self.entry_input.get().strip()
        if not user_text:
            return

        # ---- 第四面墙劫持顺从判定 (Fourth-Wall Hijack Submission Check) ----
        # If the input contains hijacked text keywords, it means the player has submitted to the fourth-wall hijack!
        # Saki phrases: "你走不掉", "不许看", "只许看我"
        hijack_phrases = ["你走不掉", "不许看", "只许看我", "の", "だ"]
        if getattr(self, "input_hijacked", False) and (any(p in user_text for p in hijack_phrases) or len(user_text) >= 15):
            print(f"[情绪反弹 - 臣服顺从] 玩家在劫持状态下发送了执念文字: '{user_text}'")
            # 1. 疑心度瞬间暴跌 30点 (解脱劫持阈值)
            self.state.suspicion = max(0, self.state.suspicion - 30)
            # 2. 逃脱率降低 15点
            self.state.escape_rate = max(0, self.state.escape_rate - 15)
            # 3. 好感度增加 20点
            self.state.favorability = min(100, self.state.favorability + 20)

            # 4. 彻底重置键盘劫持状态，让玩家重获输入自由！
            self.input_hijacked = False
            self.hijack_char_index = 0
            self.current_hijack_phrase = None

            # 5. 触发专属性格 Prompt 反馈
            self.state.local_submission_prompt = True

            # 6. 同步刷新 UI 属性栏
            self._sync_stats_to_gui()
        else:
            # ---- 逻辑层纠偏：情绪反向暴击 (Favorability Numerical Fix) ----
            severe_insults = [
                "滚", "老子", "呸", "赶紧滚", "去死", "去死吧", "死老太婆", "变态", "神经病",
                "疯子", "贱人", "垃圾", "bitch", "fuck", "go away"
            ]
            cold_rejections = [
                "不喜欢", "不爱", "讨厌", "嫌弃", "烦你", "真烦", "恨你", "不配",
                "别碰我", "恶心", "离我远点", "不要你", "不要喜欢我", "hate you", "don't like"
            ]

            triggered = False
            if any(kw in user_text for kw in severe_insults) or any(kw in user_text.lower() for kw in ["fuck", "bitch", "go away"]):
                print(f"[情绪反向暴击 - 极端侮辱] 玩家输入: '{user_text}'")
                self.state.favorability = max(0, self.state.favorability - 40)
                self.state.suspicion = min(100, self.state.suspicion + 50)
                self.state.local_insult_back_attack = True
                triggered = True
            elif any(kw in user_text for kw in cold_rejections) or any(kw in user_text.lower() for kw in ["hate you", "don't like", "dislike"]):
                print(f"[情绪反向暴击 - 冷淡拒绝] 玩家输入: '{user_text}'")
                self.state.favorability = max(0, self.state.favorability - 25)
                self.state.suspicion = min(100, self.state.suspicion + 30)
                self.state.local_insult_back_attack = True
                triggered = True

            if triggered:
                # Update stats dynamically in the UI
                self._sync_stats_to_gui()

        # ---- first-message language detection ----
        if not self.state.first_msg_detected:
            self.state.first_msg_detected = True
            if not self.user_explicitly_selected_lang:
                detected_lang = detect_language(
                    user_text, normalize_language(self.selected_language.get())
                )
                self.selected_language.set(detected_lang)
                self.state.cached_lang = detected_lang
                self.config["selected_language"] = detected_lang
                save_config(self.config)
                self._update_ui_language()

        # ---- clean up previous carnage labels ----
        if hasattr(self, "carnage_labels") and self.carnage_labels:
            for lbl in self.carnage_labels:
                try:
                    lbl.destroy()
                except Exception:
                    pass
            self.carnage_labels.clear()

        # ---- advance dialogue session ----
        self.state.dialogue_session_id += 1

        self.state.last_user_input = user_text
        self.entry_input.delete(0, tk.END)

        lang = normalize_language(self.selected_language.get())
        user_prefix = LOCALIZATION[lang]["user_prefix"]
        self._write_chat_log(f"{user_prefix}{user_text}\n", "user")
        self.chat_history.append({"role": "user", "content": user_text})

        # ---- save & read credentials on main thread (thread-safety step 5) ----
        self._save_all_settings()
        api_key = self.entry_key.get_actual_value()
        base_url = self.entry_base.get_actual_value() or "https://api.deepseek.com"
        model_name = self.entry_model.get_actual_value() or "deepseek-v4-flash"

        # ---- collapse settings if key present ----
        if api_key:
            self.top_bar.pack_forget()
            self.settings_frame.pack_forget()
            self.settings_visible = False

        self.chat_history[0]["content"] = self._get_dynamic_system_prompt()
        self._set_typing_state(True)

        api_thread = threading.Thread(
            target=fetch_api_response,
            args=(
                list(self.chat_history),
                api_key,
                base_url,
                model_name,
                self.state.cycle_id,
                self.state,
                self.ui_queue,
            ),
            daemon=True,
        )
        api_thread.start()

    # ========================================================================
    #  Typewriter + TTS
    # ========================================================================

    def _start_typewriter_effect(self, think_text, spoken_text):
        self.state.dialogue_session_id += 1
        current_session = self.state.dialogue_session_id
        current_cycle = self.state.cycle_id

        lang = normalize_language(self.selected_language.get())
        think_prefix = LOCALIZATION[lang]["think_prefix"]
        think_suffix = LOCALIZATION[lang]["think_suffix"]
        saki_prefix = LOCALIZATION[lang]["saki_prefix"]

        def typewriter_worker():
            selected_lang = self.state.cached_lang  # thread-safe (step 3)
            user_lang = detect_language(getattr(self.state, "last_user_input", ""), selected_lang)
            visual_text = (
                strip_terminal_parenthetical_translation(spoken_text, user_lang)
                or spoken_text
            )
            contains_danger = any(word in visual_text for word in self.danger_words)
            shaked = False

            if contains_danger:
                self.state.ecg_frenzy = True

            time.sleep(0.2)

            if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                return

            if think_text:
                self.state.think_jitter = True
                self._queue_ui("CHAR_RENDER_THINK", think_prefix, current_cycle)
                for char in think_text:
                    if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                        return
                    self._queue_ui("CHAR_RENDER_THINK", char, current_cycle)
                    delay = random.uniform(0.015, 0.04)
                    if char in "，。…？！,.;!?":
                        delay += 0.15
                    time.sleep(delay)
                self._queue_ui("CHAR_RENDER_THINK", think_suffix, current_cycle)
                self.state.think_jitter = False
                time.sleep(0.4)

            if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                return

            # ---- carnage trigger words (step 6: refined to truly extreme keywords ONLY) ----
            # IMPORTANT: Do NOT include words Saki uses in normal dialogue (永远, 看着我, 你是我的, etc.)
            # Only include genuinely violent/escape/extreme words that indicate critical plot moments
            danger_words_carnage = [
                "小刀", "地下室", "杀", "死", "血", "尸", "毒",
                "escape", "kill", "die", "blood",
                "殺す", "死ぬ", "血", "逃げられない", "毒",
            ]
            use_carnage = (self.state.suspicion >= 85) or any(
                w in visual_text.lower() for w in danger_words_carnage
            )

            if use_carnage:
                # Build polluted text for the overlapping scattered labels ONLY (not the chat log)
                runes = ["☠", "☣", "⛥", "🩸", "🕇", "👹", "🔪", "⛓", "🖤", "⚰", "━", "..", "？"]
                polluted_list = []
                for char in visual_text:
                    polluted_list.append(char)
                    if random.random() < 0.12:
                        polluted_list.append(random.choice(runes))
                polluted_text = "".join(polluted_list)

                self._queue_ui("TRIGGER_STROBE", None, current_cycle)
                self._queue_ui("TRIGGER_BARRAGE", 1.0, current_cycle)
                self._queue_ui("TRIGGER_MELT_OVERLAY", None, current_cycle)
                self._queue_ui("TRIGGER_MOUSE_TREMOR", None, current_cycle)
                self._queue_ui("TRIGGER_FAKE_ERROR", None, current_cycle)
                self._queue_ui("TRIGGER_MELTDOWN", None, current_cycle)
                self._queue_ui("TRIGGER_MOUSE_PULL", None, current_cycle)
                self._queue_ui("TRIGGER_SHAKE", None, current_cycle)

                if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                    return

                # Pass the CLEAN visual_text to _render_overlapping_text so the chat log stays legible
                # The polluted_text is only used for the scattered overlapping labels
                self._queue_ui("CHAR_RENDER_CARNAGE", visual_text, current_cycle)
                translation_line = extract_terminal_parenthetical_translation(spoken_text, user_lang)
                if translation_line:
                    self._queue_ui("CHAR_RENDER", f"\n{translation_line}\n", current_cycle)
                time.sleep(len(visual_text) * 0.08)
            else:
                self._queue_ui("CHAR_RENDER", saki_prefix, current_cycle)

                for idx, char in enumerate(spoken_text):
                    if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                        return
                    if getattr(self, "glitch_font_shake_active", False) and random.random() < 0.12:
                        tag_to_use = random.choice(["glitch_large", "glitch_small"])
                        self._queue_ui("CHAR_RENDER_TAGGED", (char, tag_to_use), current_cycle)
                    else:
                        self._queue_ui("CHAR_RENDER", char, current_cycle)

                    if contains_danger and not shaked:
                        current_sub = spoken_text[: idx + 1]
                        if any(word in current_sub for word in self.danger_words):
                            self._queue_ui("TRIGGER_SHAKE", None, current_cycle)
                            self._queue_ui("TRIGGER_GLITCH", None, current_cycle)
                            if random.random() < 0.4:
                                self._queue_ui("TRIGGER_STROBE", None, current_cycle)
                            if random.random() < 0.3:
                                self._queue_ui("TRIGGER_FAKE_ERROR", None, current_cycle)
                            shaked = True

                    speed_mult = getattr(self, "typewriter_speed_mult", 1.0)
                    delay = random.uniform(0.04, 0.12) * speed_mult
                    if char in "，。…？！,.;!?":
                        delay += 0.30 * speed_mult
                    time.sleep(delay)

                self._queue_ui("CHAR_RENDER", "\n", current_cycle)

            if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                return

            # ---- TTS playback (blocks until done) ----
            self._play_voice_synchronously(spoken_text, current_session)

            if current_session != self.state.dialogue_session_id or current_cycle != self.state.cycle_id:
                return

            self._queue_ui("RENDER_DONE", spoken_text, current_cycle)
            self.state.ecg_frenzy = False

        thread_typewriter = threading.Thread(target=typewriter_worker, daemon=True)
        thread_typewriter.start()

    # ========================================================================
    #  TTS playback (synchronous, in background thread)
    # ========================================================================

    def _play_voice_synchronously(self, spoken_text, session_id):
        if not HAS_PYGAME or not HAS_REQUESTS:
            return

        if session_id != self.state.dialogue_session_id:
            return

        cleaned_text = clean_text_for_tts(spoken_text)
        if not cleaned_text:
            return

        # Dynamically detect Saki's actual spoken language to prevent pronunciation conflicts (gibberish)
        detected_lang = detect_language(cleaned_text, self.state.cached_lang)
        target_lang_code = language_to_tts_code(detected_lang)

        # Retrieve the correct default references for this detected language to prevent cross-language mismatch
        ref_wav = self.refer_wav_path
        p_text = self.prompt_text

        # If using default configuration paths, dynamically hot-load/swap weights and references to match the spoken language!
        default_zh_wav = DEFAULT_LANGUAGE_VOICES["中文"]["refer_wav_path"]
        default_ja_wav = DEFAULT_LANGUAGE_VOICES["日本語"]["refer_wav_path"]
        
        is_default_ref = (
            not ref_wav or
            ref_wav == default_zh_wav or
            ref_wav == default_ja_wav or
            "huahuo.wav" in ref_wav or
            "mita.wav" in ref_wav
        )

        if is_default_ref:
            if detected_lang == "日本語":
                ref_wav = default_ja_wav
                p_text = DEFAULT_LANGUAGE_VOICES["日本語"]["prompt_text"]
                gpt_w = DEFAULT_LANGUAGE_VOICES["日本語"]["gpt_weights_path"]
                sovits_w = DEFAULT_LANGUAGE_VOICES["日本語"]["sovits_weights_path"]
                if self.gpt_weights_path != gpt_w or self.sovits_weights_path != sovits_w:
                    print(f"[Language Autodetect] Auto hot-loading Japanese Mita weights for Japanese text...")
                    self._queue_ui("TRIGGER_LOAD_WEIGHTS", ("gpt", gpt_w))
                    self._queue_ui("TRIGGER_LOAD_WEIGHTS", ("sovits", sovits_w))
                    self.gpt_weights_path = gpt_w
                    self.sovits_weights_path = sovits_w
            else:
                ref_wav = default_zh_wav
                p_text = DEFAULT_LANGUAGE_VOICES["中文"]["prompt_text"]
                gpt_w = DEFAULT_LANGUAGE_VOICES["中文"]["gpt_weights_path"]
                sovits_w = DEFAULT_LANGUAGE_VOICES["中文"]["sovits_weights_path"]
                if self.gpt_weights_path != gpt_w or self.sovits_weights_path != sovits_w:
                    print(f"[Language Autodetect] Auto hot-loading Chinese Sparkle weights for Chinese text...")
                    self._queue_ui("TRIGGER_LOAD_WEIGHTS", ("gpt", gpt_w))
                    self._queue_ui("TRIGGER_LOAD_WEIGHTS", ("sovits", sovits_w))
                    self.gpt_weights_path = gpt_w
                    self.sovits_weights_path = sovits_w

        # ---- synthesize via shared tts_client ----
        abs_refer_wav = os.path.abspath(ref_wav) if ref_wav else ""
        wav_bytes = synthesize_speech(
            cleaned_text,
            abs_refer_wav,
            p_text,
            self.gpt_sovits_url,
            target_lang_code,
            self.working_endpoint,
        )
        if wav_bytes is None:
            return

        if session_id != self.state.dialogue_session_id:
            return

        temp_file = None
        try:
            temp_file = f"temp_saki_{int(time.time() * 1000)}.wav"
            with open(temp_file, "wb") as f:
                f.write(wav_bytes)

            if session_id != self.state.dialogue_session_id:
                return

            # ---- lower heartbeat volume ----
            self.sound_mgr.set_heartbeat_volume(0.15)

            # ---- play via SoundManager ----
            channel = self.sound_mgr.play_voice_from_file(temp_file)



            # ---- block until voice finishes (max 35s safety timeout to prevent Pygame lock deadlocks) ----
            if channel:
                start_wait = time.time()
                while channel.get_busy() and not self.state.game_over:
                    if time.time() - start_wait > 35.0:
                        print("[warning] voice playback wait timeout, force unlocking.")
                        channel.stop()
                        break
                    if session_id != self.state.dialogue_session_id:
                        channel.stop()
                        return
                    time.sleep(0.1)

            # ---- restore heartbeat ----
            if not self.state.game_over:
                self.sound_mgr.set_heartbeat_volume(0.8)

        except Exception as ex:
            print(f"[sync voice playback error] {ex}")
            if not self.state.game_over:
                self.sound_mgr.set_heartbeat_volume(0.8)
        finally:
            if temp_file and os.path.exists(temp_file):
                for _ in range(5):
                    try:
                        os.remove(temp_file)
                        break
                    except Exception:
                        time.sleep(0.1)

    # ========================================================================
    #  Game stats update
    # ========================================================================

    def _update_game_stats(self, delta_data):
        """Apply delta to GameState and refresh progress bars."""
        if self.state.game_over:
            return

        self.state.apply_delta(delta_data)

        # ---- sync GUI bars ----
        self.bar_favor["value"] = self.state.favorability
        self.bar_sus["value"] = self.state.suspicion
        self.bar_esc["value"] = self.state.escape_rate

        self.lbl_favor_val.config(text=f"{self.state.favorability}")
        self.lbl_sus_val.config(text=f"{self.state.suspicion}")
        self.lbl_esc_val.config(text=f"{self.state.escape_rate}%")

        if self.state.game_over:
            return

        self._check_endings(force_final=False)

    def _check_endings(self, force_final=False):
        """Check stat thresholds for auto-game-over."""
        if self.state.game_over:
            return
        if self.state.suspicion >= 96:
            self.state.pending_ending = {"ending_type": "bad"}
            self.state.game_over = True
            return
        if self.state.favorability <= -25:
            self.state.pending_ending = {"ending_type": "bad"}
            self.state.game_over = True
            return

    def _on_dialogue_completed(self):
        if self.state.game_over:
            return

        day_changed, new_day = self.state.advance_day()
        if day_changed:
            lang = normalize_language(self.selected_language.get())
            loc = LOCALIZATION[lang]
            self.lbl_day.config(text=loc["day"].format(day=new_day))
            self._write_chat_log(loc["sys_day_transition"].format(day=new_day), "system")
            self._start_physical_shake()

    # ========================================================================
    #  Ending overlay
    # ========================================================================

    def _show_ending_overlay(self, final_text):
        if hasattr(self, "overlay") and self.overlay.winfo_exists():
            return

        self._set_typing_state(True)
        self.entry_input.config(state=tk.DISABLED)
        self.btn_send.config(state=tk.DISABLED)

        ending_info = self.state.pending_ending or {}
        ending_type = ending_info.get("ending_type", "bad")

        color_map = {"bad": "#FF0000", "good": "#FFD700", "neutral": "#FF8C00"}
        color = color_map.get(ending_type, "#8A0303")

        title = ending_info.get("ending_title", "")
        lang = normalize_language(self.selected_language.get())
        if not title and ending_type in LOCALIZATION[lang]["endings"]:
            title = LOCALIZATION[lang]["endings"][ending_type]["title"]
        if not title:
            title = "END"

        ai_story = ending_info.get("ending_story", "")
        if ai_story:
            story = f"{final_text}\n\n{ai_story}"
        else:
            story = f"{final_text}"

        self.overlay = tk.Frame(self.root, bg="#000000")
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)

        lbl_end_title = tk.Label(
            self.overlay,
            text=title,
            fg=color,
            bg="#000000",
            font=("Microsoft YaHei", 16, "bold"),
            wraplength=520,
        )
        lbl_end_title.pack(pady=(100, 15))

        ecg_overlay = tk.Canvas(self.overlay, bg="#000000", height=30, highlightthickness=0)
        ecg_overlay.pack(fill=tk.X, padx=200, pady=5)

        def pulse_anim():
            if not self.overlay.winfo_exists():
                return
            ecg_overlay.delete("all")
            ecg_overlay.create_line(0, 15, 550, 15, fill="#220000", width=1)
            self.root.after(750, pulse_anim)

        pulse_anim()

        lbl_story = tk.Label(
            self.overlay,
            text=story,
            fg="#DDDDDD",
            bg="#000000",
            font=("Microsoft YaHei", 10),
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=520,
        )
        lbl_story.pack(pady=15, padx=40)

        btn_restart = tk.Button(
            self.overlay,
            text=LOCALIZATION[lang]["restart_btn"],
            fg="#FFFFFF",
            bg="#8A0303",
            activeforeground="#FF0000",
            activebackground="#200000",
            relief=tk.SOLID,
            bd=1,
            font=("Microsoft YaHei", 11, "bold"),
            command=self._restart_game,
        )
        btn_restart.pack(pady=(20, 0), ipadx=20, ipady=6)

    # ========================================================================
    #  Restart
    # ========================================================================

    def _restart_game(self):
        self.state.cycle_id += 1
        self.state.dialogue_session_id += 1
        self._clear_ui_queue()
        self.state.pending_ending = None

        if hasattr(self, "overlay") and self.overlay.winfo_exists():
            self.overlay.destroy()

        self.overlay_mgr.force_clear()
        if self._flood_canvas_ref is not None:
            self._safe_destroy_widget(self._flood_canvas_ref)
            self._flood_canvas_ref = None

        # ---- reset horror flags ----
        self.mouse_pull_active = False
        self.meltdown_active = False
        self.barrage_active = False
        self.psychic_strobe_active = False
        self.state.ecg_flatline_active = False
        self.state.dripping_blood_active = False
        self.state.scanlines_active = False
        self.state.snow_noise_active = False
        self.state.fake_error_active = False
        self.glitch_rune_active = False
        self.glitch_font_shake_active = False
        self.typewriter_speed_mult = 1.0

        if hasattr(self, "carnage_labels") and self.carnage_labels:
            for lbl in self.carnage_labels:
                try:
                    lbl.destroy()
                except Exception:
                    pass
            self.carnage_labels.clear()

        # ---- restart audio ----
        if HAS_PYGAME:
            self.sound_mgr.stop_all()
            self.sound_mgr.init_heartbeat("heartbeat.wav")

        # ---- reset game state ----
        self.state.reset()
        self.state.cached_lang = normalize_language(self.selected_language.get())

        # ---- reset extra visual flags on state ----
        self.state.ecg_frenzy = False
        self.state.think_jitter = False
        self.state.shaking = False
        self.mouse_tremor_active = False

        # ---- sync GUI bars ----
        self.bar_favor["value"] = self.state.favorability
        self.bar_sus["value"] = self.state.suspicion
        self.bar_esc["value"] = self.state.escape_rate

        self.lbl_favor_val.config(text=f"{self.state.favorability}")
        self.lbl_sus_val.config(text=f"{self.state.suspicion}")
        self.lbl_esc_val.config(text=f"{self.state.escape_rate}%")

        lang = normalize_language(self.selected_language.get())
        self.lbl_day.config(text=LOCALIZATION[lang]["day"].format(day=self.state.current_day))

        self.chat_history = [{"role": "system", "content": self._get_dynamic_system_prompt()}]

        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)

        self._set_typing_state(False)

        # ---- restart visual loops ----
        self._start_border_pulse_loop()

        restart_cycle = self.state.cycle_id
        self.root.after(
            500,
            lambda cycle=restart_cycle: (
                self._enqueue_saki_response(
                    INITIAL_GREETINGS[normalize_language(self.selected_language.get())]
                )
                if cycle == self.state.cycle_id and not self.state.game_over
                else None
            ),
        )

    # ========================================================================
    #  Chat log helpers
    # ========================================================================

    def _write_chat_log(self, text, tag):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text, tag)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    # ========================================================================
    #  Slots-Based JSON Save / Load Logic & Dynamic Character Swapping
    # ========================================================================

    def save_slot1(self):
        self._async_save_slot(1)

    def save_slot2(self):
        self._async_save_slot(2)

    def save_slot3(self):
        self._async_save_slot(3)

    def save_slot4(self):
        self._async_save_slot(4)

    def save_slot5(self):
        self._async_save_slot(5)

    def load_slot1(self):
        self._async_load_slot(1)

    def load_slot2(self):
        self._async_load_slot(2)

    def load_slot3(self):
        self._async_load_slot(3)

    def load_slot4(self):
        self._async_load_slot(4)

    def load_slot5(self):
        self._async_load_slot(5)

    def _async_save_slot(self, slot_num):
        """Asynchronously save the current game state to a JSON file."""
        def worker():
            try:
                # Capture values from GUI thread safely
                api_key = self.entry_key.get_actual_value()
                data = {
                    "current_day": self.state.current_day,
                    "favorability": self.state.favorability,
                    "suspicion": self.state.suspicion,
                    "escape_rate": self.state.escape_rate,
                    "chat_history": self.chat_history,
                    "api_key": api_key,
                    "current_char_id": getattr(self.state, "current_char_id", "saki"),
                    "selected_language": self.state.cached_lang,
                }
                filename = f"save_slot_{slot_num}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                self.root.after(0, lambda: self._write_chat_log(f"【系统】存档 Slot {slot_num} 成功！当前角色: {data['current_char_id']}\n", "system"))
            except Exception as e:
                self.root.after(0, lambda: self._write_chat_log(f"【系统】存档 Slot {slot_num} 失败：{e}\n", "system"))

        threading.Thread(target=worker, daemon=True).start()

    def _async_load_slot(self, slot_num):
        """Asynchronously load the game state from a JSON file."""
        def worker():
            try:
                filename = f"save_slot_{slot_num}.json"
                if not os.path.exists(filename):
                    self.root.after(0, lambda: self._write_chat_log(f"【系统】读档失败：Slot {slot_num} 不存在！\n", "system"))
                    return
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)

                def apply_loaded_data():
                    self.state.current_day = data.get("current_day", 1)
                    self.state.favorability = data.get("favorability", 50)
                    self.state.suspicion = data.get("suspicion", 20)
                    self.state.escape_rate = data.get("escape_rate", 0)
                    self.chat_history = data.get("chat_history", [{"role": "system", "content": ""}])

                    loaded_key = data.get("api_key", "")
                    if loaded_key:
                        self.entry_key.delete(0, tk.END)
                        self.entry_key.insert(0, loaded_key)
                        self.entry_key.config(fg="#FF0000")

                    char_id = data.get("current_char_id", "saki")
                    self.change_character(char_id)

                    # Map UI language from slot data if available, fallback to detecting from history, then global configs
                    chosen_lang = data.get("selected_language")
                    if not chosen_lang:
                        # Try to detect from chat history
                        history = data.get("chat_history", [])
                        detected = None
                        for msg in reversed(history):
                            if msg.get("role") == "assistant":
                                content = msg.get("content", "")
                                if "<think>" in content and "</think>" in content:
                                    content = content.split("</think>")[-1]
                                # If it has Hiragana/Katakana, it is Japanese
                                if re.search(r"[぀-ゟ゠-ヿ]", content):
                                    detected = "日本語"
                                    break
                                det = detect_language(content, None)
                                if det:
                                    detected = det
                                    break
                        chosen_lang = detected or self.config.get("selected_language", "中文")

                    chosen_lang = normalize_language(chosen_lang)
                    self.selected_language.set(chosen_lang)
                    self.state.cached_lang = chosen_lang
                    self.user_explicitly_selected_lang = True

                    self.config["selected_language"] = chosen_lang
                    save_config(self.config)

                    self._update_ui_language()
                    self._sync_stats_to_gui()
                    self._restore_chat_history_to_gui()
                    self._write_chat_log(f"【系统】成功载入存档 Slot {slot_num}！当前角色: {char_id}\n", "system")

                self.root.after(0, apply_loaded_data)
            except Exception as e:
                self.root.after(0, lambda: self._write_chat_log(f"【系统】读档 Slot {slot_num} 失败：{e}\n", "system"))

        threading.Thread(target=worker, daemon=True).start()

    def change_character(self, char_id):
        """Change the active character dynamically (Prompt, Sound reference, and Dialogue colors)."""
        self.state.current_char_id = char_id

        # 1. Read custom characters
        custom_chars = {}
        if os.path.exists("custom_characters.json"):
            try:
                with open("custom_characters.json", "r", encoding="utf-8") as f:
                    custom_chars = json.load(f)
            except Exception:
                pass

        if char_id in custom_chars:
            cdata = custom_chars[char_id]
            name = cdata.get("name", "自定义角色")
            chat_color = cdata.get("chat_color", "#FF3399")
            ref_wav = cdata.get("refer_wav_path", "")
            prompt_t = cdata.get("prompt_text", "")
            gpt_w = cdata.get("gpt_weights_path", "")
            sovits_w = cdata.get("sovits_weights_path", "")

            # Update tag color
            self.chat_text.tag_config("saki", foreground=chat_color)

            # Update entries in configs
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, ref_wav)
            self.entry_refer_wav.config(fg=chat_color)
            self.refer_wav_path = ref_wav

            self.entry_prompt_text.delete(0, tk.END)
            self.entry_prompt_text.insert(0, prompt_t)
            self.entry_prompt_text.config(fg=chat_color)
            self.prompt_text = prompt_t

            if gpt_w:
                self.entry_gpt_weights.delete(0, tk.END)
                self.entry_gpt_weights.insert(0, gpt_w)
                self.entry_gpt_weights.config(fg=chat_color)
                self.gpt_weights_path = gpt_w
            if sovits_w:
                self.entry_sovits_weights.delete(0, tk.END)
                self.entry_sovits_weights.insert(0, sovits_w)
                self.entry_sovits_weights.config(fg=chat_color)
                self.sovits_weights_path = sovits_w

            self.lbl_refer_wav_title.config(fg=chat_color)
            print(f"[切换角色] 已切换至自定义角色: {name}")

            # Trigger weights hotload if exists
            if gpt_w and os.path.exists(gpt_w):
                self._async_load_weights("gpt", gpt_w)
            if sovits_w and os.path.exists(sovits_w):
                self._async_load_weights("sovits", sovits_w)

        else:
            # Dynamic dialogue color: Crimson red for Saki
            self.chat_text.tag_config("saki", foreground="#CC0000")

            # Load references in GUI
            self.entry_refer_wav.delete(0, tk.END)
            saki_wav = self.config.get("refer_wav_path") or ""
            if not saki_wav:
                saki_wav = DEFAULT_LANGUAGE_VOICES["中文"]["refer_wav_path"]
            self.entry_refer_wav.insert(0, saki_wav)
            self.entry_refer_wav.config(fg="#FF0000")
            self.refer_wav_path = saki_wav

            saki_prompt = self.config.get("prompt_text") or "你要是有什么危险的差事要办，尽管来找我。"
            self.entry_prompt_text.delete(0, tk.END)
            self.entry_prompt_text.insert(0, saki_prompt)
            self.entry_prompt_text.config(fg="#FF0000")
            self.prompt_text = saki_prompt

            self.lbl_refer_wav_title.config(fg="#FF0000")
            print(f"[切换角色] 已切换至纱希 (Saki)")

        # Sync System prompt content directly in history
        self.chat_history[0]["content"] = self._get_dynamic_system_prompt()

    def toggle_character(self):
        """Toggle between Saki and custom characters."""
        char_ids = ["saki"]
        custom_chars = {}
        if os.path.exists("custom_characters.json"):
            try:
                with open("custom_characters.json", "r", encoding="utf-8") as f:
                    custom_chars = json.load(f)
                for k in custom_chars:
                    if k not in char_ids:
                        char_ids.append(k)
            except Exception:
                pass

        current_char = getattr(self.state, "current_char_id", "saki")
        if current_char not in char_ids:
            current_char = "saki"

        cur_idx = char_ids.index(current_char)
        next_idx = (cur_idx + 1) % len(char_ids)
        next_char = char_ids[next_idx]

        self.change_character(next_char)

        char_display = {
            "saki": "纱希 (Saki)"
        }
        if next_char in custom_chars:
            char_display[next_char] = f"{custom_chars[next_char].get('name', '自定义角色')} ({next_char})"

        self._write_chat_log(f"【系统】已切换角色至：{char_display.get(next_char, next_char)} (按 F12 再次切换)\n", "system")

    def _sync_stats_to_gui(self):
        """Synchronize the current game state values directly into Tkinter UI widgets."""
        self.bar_favor["value"] = self.state.favorability
        self.bar_sus["value"] = self.state.suspicion
        self.bar_esc["value"] = self.state.escape_rate

        self.lbl_favor_val.config(text=f"{self.state.favorability}")
        self.lbl_sus_val.config(text=f"{self.state.suspicion}")
        self.lbl_esc_val.config(text=f"{self.state.escape_rate}%")

        lang = normalize_language(self.selected_language.get())
        loc = LOCALIZATION[lang]
        self.lbl_day.config(text=loc["day"].format(day=self.state.current_day))

    def _restore_chat_history_to_gui(self):
        """Redraw all past dialogues from self.chat_history into the chat widget."""
        print(f"[Memory Restore] Beginning restoration. History length: {len(self.chat_history)}")
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)

        lang = normalize_language(self.selected_language.get())
        print(f"[Memory Restore] Target interface language: {lang}")
        think_prefix = LOCALIZATION[lang]["think_prefix"]
        think_suffix = LOCALIZATION[lang]["think_suffix"]
        saki_prefix = LOCALIZATION[lang]["saki_prefix"]
        user_prefix = LOCALIZATION[lang]["user_prefix"]

        # Skip the system instruction prompt
        for idx, msg in enumerate(self.chat_history[1:], start=1):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if not content:
                print(f"[Memory Restore] Skipping item {idx} due to empty content")
                continue

            print(f"[Memory Restore] Processing item {idx}: role={role}, content_len={len(content)}")

            if role == "user":
                self._write_chat_log(f"{user_prefix}{content}\n", "user")
            elif role == "assistant":
                parsed = parse_api_response(content, "", self.state)
                think_content = parsed.get("think", "")
                spoken_text = parsed.get("spoken", "")
                
                if think_content:
                    self._write_chat_log(f"{think_prefix}{think_content}{think_suffix}", "think")
                
                self._write_chat_log(saki_prefix, "saki")
                self._write_chat_log(f"{spoken_text}\n", "saki")

    def _disconnect_to_splash(self):
        """Tear down gameplay and return to startup screen."""
        self._emergency_clear_overlays()
        self.state.game_over = False
        self.sound_mgr.stop_voice()
        self._show_splash_screen()

    def _on_splash_settings_clicked(self):
        """Pop up the Custom Character Profile input editor directly from the Splash screen."""
        pop = tk.Toplevel(self.root)
        pop.title("自定义角色脑回路配置")
        pop.geometry("640x720")
        pop.configure(bg="#000000")
        pop.resizable(False, False)
        pop.transient(self.root)
        pop.grab_set()

        lbl_title = tk.Label(
            pop, text="[ ⚙ 自定义神经角色脑回路配置 ]", fg="#FF0000", bg="#000000",
            font=("Consolas", 12, "bold")
        )
        lbl_title.pack(pady=15)

        form = tk.Frame(pop, bg="#000000")
        form.pack(fill=tk.BOTH, expand=True, padx=30)

        row_idx = 0
        def add_field(label_text, is_large=False):
            nonlocal row_idx
            lbl = tk.Label(form, text=label_text, fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
            lbl.grid(row=row_idx, column=0, sticky=tk.W, pady=3)

            if is_large:
                text_widget = tk.Text(form, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000",
                                     relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9), height=3, width=50, wrap=tk.WORD)
                text_widget.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
                row_idx += 1
                return text_widget
            else:
                entry_widget = tk.Entry(form, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000",
                                       relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9), width=50)
                entry_widget.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
                row_idx += 1
                return entry_widget

        ent_name = add_field("角色姓名 (Name):")
        ent_age = add_field("角色年龄 (Age):")
        txt_personality = add_field("性格设定 (Personality):", is_large=True)
        txt_story = add_field("背景与故事主线 (Story):", is_large=True)
        txt_plot = add_field("特有交互剧情 (Plot):", is_large=True)
        txt_world = add_field("所处世界观 (World):", is_large=True)
        ent_color = add_field("聊天文字颜色 (Color):")

        # WAV Reference with browse
        lbl_wav = tk.Label(form, text="参考音频 (.wav):", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
        lbl_wav.grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        wav_frame = tk.Frame(form, bg="#000000")
        wav_frame.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
        ent_wav = tk.Entry(wav_frame, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9))
        ent_wav.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def browse_wav():
            fn = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
            if fn:
                ent_wav.delete(0, tk.END)
                ent_wav.insert(0, fn)
        btn_browse = tk.Button(wav_frame, text="浏览", fg="#8A0303", bg="#0D0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8), command=browse_wav)
        btn_browse.pack(side=tk.RIGHT, padx=(5, 0))
        row_idx += 1

        ent_text = add_field("参考音频文本 (Text):")

        # Weights paths
        lbl_gpt = tk.Label(form, text="GPT 权重 (.ckpt):", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
        lbl_gpt.grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        gpt_frame = tk.Frame(form, bg="#000000")
        gpt_frame.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
        ent_gpt = tk.Entry(gpt_frame, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9))
        ent_gpt.pack(side=tk.LEFT, fill=tk.X, expand=True)
        def browse_gpt():
            fn = filedialog.askopenfilename(filetypes=[("Weights files", "*.ckpt")])
            if fn:
                ent_gpt.delete(0, tk.END)
                ent_gpt.insert(0, fn)
        btn_bgpt = tk.Button(gpt_frame, text="浏览", fg="#8A0303", bg="#0D0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8), command=browse_gpt)
        btn_bgpt.pack(side=tk.RIGHT, padx=(5, 0))
        row_idx += 1

        lbl_sovits = tk.Label(form, text="SoVITS 权重 (.pth):", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
        lbl_sovits.grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        sovits_frame = tk.Frame(form, bg="#000000")
        sovits_frame.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
        ent_sovits = tk.Entry(sovits_frame, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9))
        ent_sovits.pack(side=tk.LEFT, fill=tk.X, expand=True)
        def browse_sovits():
            fn = filedialog.askopenfilename(filetypes=[("Weights files", "*.pth")])
            if fn:
                ent_sovits.delete(0, tk.END)
                ent_sovits.insert(0, fn)
        btn_bsovits = tk.Button(sovits_frame, text="浏览", fg="#8A0303", bg="#0D0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8), command=browse_sovits)
        btn_bsovits.pack(side=tk.RIGHT, padx=(5, 0))
        row_idx += 1

        form.columnconfigure(1, weight=1)

        # Load existing custom character data if exists
        custom_data = {}
        if os.path.exists("custom_characters.json"):
            try:
                with open("custom_characters.json", "r", encoding="utf-8") as f:
                    custom_data = json.load(f)
            except Exception:
                pass

        cdata = custom_data.get("custom", custom_data.get("sparkle", {}))
        ent_name.insert(0, cdata.get("name", "花火"))
        ent_age.insert(0, cdata.get("age", "18"))
        txt_personality.insert("1.0", cdata.get("personality", "小恶魔、变幻莫测、疯狂、腹黑，极度热爱捉弄玩家"))
        txt_story.insert("1.0", cdata.get("main_story", "她是假面愚者的成员，将玩家关进了一个布满迷幻霓虹与马戏团玩具的游乐园密室，用各种虚实难辨的游戏爱着你"))
        txt_plot.insert("1.0", cdata.get("character_plot", "每当你表现出顺从，她就会露出天真烂漫的笑容；而一旦你试图逃跑，她就会微笑着摆弄炸弹引爆器"))
        txt_world.insert("1.0", cdata.get("world_view", "一个充满迷幻霓虹、马戏团狂欢和荒诞黑色幽默的虚无主义都市"))
        ent_color.insert(0, cdata.get("chat_color", "#FF3399"))
        ent_wav.insert(0, cdata.get("refer_wav_path", "D:/花火/yingping/huahuo.wav_0000000000_0000061760.wav"))
        ent_text.insert(0, cdata.get("prompt_text", "独向昭谈至恶龙一阁著文章。"))
        ent_gpt.insert(0, cdata.get("gpt_weights_path", "D:/花火/Huahuo_Yandere-e10.ckpt"))
        ent_sovits.insert(0, cdata.get("sovits_weights_path", "D:/花火/Huahuo_Yandere_e10_s440.pth"))

        def save_custom_char():
            cdata_new = {
                "name": ent_name.get().strip() or "自定义角色",
                "age": ent_age.get().strip() or "18",
                "personality": txt_personality.get("1.0", tk.END).strip(),
                "main_story": txt_story.get("1.0", tk.END).strip(),
                "character_plot": txt_plot.get("1.0", tk.END).strip(),
                "world_view": txt_world.get("1.0", tk.END).strip(),
                "chat_color": ent_color.get().strip() or "#FF3399",
                "refer_wav_path": ent_wav.get().strip(),
                "prompt_text": ent_text.get().strip(),
                "gpt_weights_path": ent_gpt.get().strip(),
                "sovits_weights_path": ent_sovits.get().strip(),
            }
            custom_data["custom"] = cdata_new
            try:
                with open("custom_characters.json", "w", encoding="utf-8") as f:
                    json.dump(custom_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("成功", "自定义角色脑波参数保存成功！")
                pop.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存自定义角色脑回路失败：{e}")

        btn_save = tk.Button(
            pop, text="保存角色配置", fg="#2ECC71", bg="#001F00", activeforeground="#2ECC71", activebackground="#053005",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 10, "bold"), width=20, height=2,
            command=save_custom_char
        )
        btn_save.pack(pady=15)

    def _load_slot_from_splash(self, slot_num):
        """Instantly load gameplay slot directly from Splash screen, bypassing greetings."""
        self._sync_api_from_splash()
        filename = f"save_slot_{slot_num}.json"
        if not os.path.exists(filename):
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Apply loaded states
            self.state.current_day = data.get("current_day", 1)
            self.state.favorability = data.get("favorability", 50)
            self.state.suspicion = data.get("suspicion", 20)
            self.state.escape_rate = data.get("escape_rate", 0)
            self.chat_history = data.get("chat_history", [{"role": "system", "content": ""}])

            loaded_key = data.get("api_key", "")
            if loaded_key:
                self.entry_key.delete(0, tk.END)
                self.entry_key.insert(0, loaded_key)
                self.entry_key.config(fg="#FF0000")

            # Map UI language from slot data if available, fallback to detecting from history, then global configs
            chosen_lang = data.get("selected_language")
            if not chosen_lang:
                # Try to detect from chat history
                history = data.get("chat_history", [])
                detected = None
                for msg in reversed(history):
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "")
                        if "<think>" in content and "</think>" in content:
                            content = content.split("</think>")[-1]
                        # If it has Hiragana/Katakana, it is Japanese
                        if re.search(r"[぀-ゟ゠-ヿ]", content):
                            detected = "日本語"
                            break
                        det = detect_language(content, None)
                        if det:
                            detected = det
                            break
                chosen_lang = detected or self.config.get("selected_language", "中文")

            chosen_lang = normalize_language(chosen_lang)
            self.selected_language.set(chosen_lang)
            self.state.cached_lang = chosen_lang
            self.user_explicitly_selected_lang = True

            self.config["selected_language"] = chosen_lang
            save_config(self.config)

            # Swap character - moved here to ensure state.cached_lang is updated to slot's true language (e.g. Japanese)
            # before _get_dynamic_system_prompt is evaluated inside change_character
            char_id = data.get("current_char_id", "saki")
            self.change_character(char_id)

            self._update_ui_language()
            self._sync_stats_to_gui()
            self._restore_chat_history_to_gui()

            # Destroy splash screen smoothly
            if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
                self.splash_frame.destroy()

            self._write_chat_log(f"【系统】脑机突触建立成功！已从 Slot {slot_num} 恢复神经记忆回路。\n", "system")
            print(f"[Splash Load] Successfully loaded memory Slot {slot_num}")
        except Exception as e:
            messagebox.showerror("载入失败", f"无法唤醒该插槽的记忆电位：{e}")

    def _delete_slot_from_splash(self, slot_num):
        """Confirm and physically delete a save slot file directly from Splash screen, then refresh."""
        if messagebox.askyesno("删除确认", f"您确定要永久删除记忆槽位 {slot_num} 吗？"):
            fn = f"save_slot_{slot_num}.json"
            if os.path.exists(fn):
                try:
                    os.remove(fn)
                    print(f"[删除存档] 已删除 {fn}")
                except Exception as e:
                    print(f"[删除存档失败] {e}")
            self._show_splash_screen()

    # ========================================================================
    #  Settings toggle
    # ========================================================================

    def _toggle_settings(self):
        if self.settings_visible:
            self.top_bar.pack_forget()
            self.settings_frame.pack_forget()
            self.settings_visible = False
            self.btn_toggle_settings.config(text="[ 展开配置通道 ]", fg="#666666")
        else:
            self.top_bar.pack(before=self.canvas_ecg, fill=tk.X, padx=10, pady=5)
            self.settings_frame.pack(before=self.canvas_ecg, fill=tk.X, padx=10, pady=5)
            self.btn_toggle_settings.config(text="[ 收起配置通道 ]", fg="#8A0303")
            self.settings_visible = True
            self._animate_panel_fade_in()

    # ========================================================================
    #  Splash screen
    # ========================================================================

    def _show_splash_screen(self):
        if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
            self.splash_frame.destroy()
        self.splash_frame = tk.Frame(self.root, bg="#000000")
        self.splash_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.splash_frame.lift()

        # Premium sci-fi hacker-terminal header
        lbl_splash_title = tk.Label(
            self.splash_frame,
            text="纱希 (Saki) - Terminal A.I.",
            fg="#FF0033",
            bg="#000000",
            font=("Consolas", 26, "bold"),
        )
        lbl_splash_title.pack(pady=(40, 5))

        lbl_splash_sys_status = tk.Label(
            self.splash_frame,
            text="● SYSTEM OVERLORD STATUS: ONLINE  |  NEURAL COUPLING STABLE",
            fg="#00FF66",
            bg="#000000",
            font=("Consolas", 8, "bold")
        )
        lbl_splash_sys_status.pack(pady=(0, 15))

        lbl_splash_subtitle = tk.Label(
            self.splash_frame,
            text="[ 请选择与纱希脑机接口建立连接的语言 ]\n[ Select Saki's Interface & Voice Language ]",
            fg="#8A0303",
            bg="#000000",
            font=("Microsoft YaHei", 10, "bold"),
            justify=tk.CENTER,
        )
        lbl_splash_subtitle.pack(pady=(0, 15))

        btn_frame = tk.Frame(self.splash_frame, bg="#000000")
        btn_frame.pack(pady=5)

        langs = [
            ("简体中文", "中文"),
            ("English", "English"),
            ("日本語", "日本語"),
        ]

        for text, lang_val in langs:
            btn = tk.Button(
                btn_frame,
                text=text,
                fg="#FF3333",
                bg="#080000",
                activeforeground="#FF0000",
                activebackground="#150000",
                relief=tk.SOLID,
                bd=1,
                font=("Microsoft YaHei", 11, "bold"),
                width=18,
                height=2,
                command=lambda l=lang_val: self._start_game_with_language(l),
            )
            btn.pack(side=tk.LEFT, padx=12)
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg="#FF0000", bg="#180000", highlightbackground="#FF0000"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="#FF3333", bg="#080000", highlightbackground="#222222"))

        # LabelFrame for API Connection Settings
        from ui.custom_widgets import PlaceholderEntry

        api_frame = tk.LabelFrame(
            self.splash_frame,
            text="  🛡️ 脑机接口通信协议配置 / Synapse Connection Settings  ",
            fg="#FF0033",
            bg="#000000",
            font=("Consolas", 10, "bold"),
            relief=tk.SOLID,
            bd=1,
            padx=15,
            pady=10
        )
        api_frame.pack(fill=tk.X, padx=80, pady=15)

        # Grid inside LabelFrame
        lbl_splash_key = tk.Label(
            api_frame, text="API Key:", fg="#888888", bg="#000000",
            font=("Consolas", 9, "bold"), anchor=tk.W, width=10
        )
        lbl_splash_key.grid(row=0, column=0, sticky=tk.W, pady=3)

        self.entry_splash_key = PlaceholderEntry(
            api_frame, placeholder="在此输入你的 API Key (Enter API Key)",
            placeholder_color="#444444", default_color="#FF0000", show_char="*",
            bg="#0A0000", fg="#FF3333", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9), width=50
        )
        self.entry_splash_key.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=3)
        if self.config.get("api_key"):
            self.entry_splash_key.delete(0, tk.END)
            self.entry_splash_key.insert(0, self.config["api_key"])
            self.entry_splash_key.config(fg="#FF3333", show="*")

        lbl_splash_base = tk.Label(
            api_frame, text="API Base:", fg="#888888", bg="#000000",
            font=("Consolas", 9, "bold"), anchor=tk.W, width=10
        )
        lbl_splash_base.grid(row=1, column=0, sticky=tk.W, pady=3)

        self.entry_splash_base = PlaceholderEntry(
            api_frame, placeholder="默认: https://api.deepseek.com (Default URL)",
            placeholder_color="#444444", default_color="#FF0000",
            bg="#0A0000", fg="#FF3333", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9), width=50
        )
        self.entry_splash_base.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=3)
        if self.config.get("api_base"):
            self.entry_splash_base.delete(0, tk.END)
            self.entry_splash_base.insert(0, self.config["api_base"])
            self.entry_splash_base.config(fg="#FF3333")

        # Row 2: Test connection button and status label
        test_frame = tk.Frame(api_frame, bg="#000000")
        test_frame.grid(row=2, column=1, sticky=tk.EW, pady=(5, 0))

        btn_test_conn = tk.Button(
            test_frame, text=" 📡 测试 API 联通性 / Test Connection ", fg="#FF3333", bg="#100000",
            activeforeground="#FF0000", activebackground="#200000",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"),
            command=self._test_api_connection
        )
        btn_test_conn.pack(side=tk.LEFT)
        btn_test_conn.bind("<Enter>", lambda e, b=btn_test_conn: b.config(fg="#FF0000", bg="#200000"))
        btn_test_conn.bind("<Leave>", lambda e, b=btn_test_conn: b.config(fg="#FF3333", bg="#100000"))

        self.lbl_test_status = tk.Label(
            test_frame, text="[ 状态: 未测试 / Ready ]", fg="#888888", bg="#000000",
            font=("Microsoft YaHei", 8, "bold")
        )
        self.lbl_test_status.pack(side=tk.LEFT, padx=15)

        api_frame.columnconfigure(1, weight=1)

        # Custom Character & Slots Section
        mid_frame = tk.Frame(self.splash_frame, bg="#000000")
        mid_frame.pack(fill=tk.X, padx=80, pady=5)

        # Custom character button on the left of separator/slots
        self.btn_splash_settings = tk.Button(
            mid_frame,
            text=" ⚙ 自定义大脑皮层参数 / Custom Character Settings ",
            fg="#FF3399",
            bg="#0D0008",
            activeforeground="#FF0099",
            activebackground="#200015",
            relief=tk.SOLID,
            bd=1,
            font=("Microsoft YaHei", 9, "bold"),
            command=self._on_splash_settings_clicked
        )
        self.btn_splash_settings.pack(anchor=tk.CENTER, pady=(0, 10))
        self.btn_splash_settings.bind("<Enter>", lambda e: self.btn_splash_settings.config(fg="#FF0099", bg="#200010"))
        self.btn_splash_settings.bind("<Leave>", lambda e: self.btn_splash_settings.config(fg="#FF3399", bg="#0D0008"))

        # LabelFrame for Save slots
        slots_frame = tk.LabelFrame(
            self.splash_frame,
            text="  💾 脑机接口历史记忆载入 / Memory Slot Management  ",
            fg="#00FF66",
            bg="#000000",
            font=("Consolas", 10, "bold"),
            relief=tk.SOLID,
            bd=1,
            padx=15,
            pady=8
        )
        slots_frame.pack(fill=tk.X, padx=80, pady=5)

        slots_container = tk.Frame(slots_frame, bg="#000000")
        slots_container.pack(fill=tk.X, pady=2)

        for idx in range(1, 6):
            fn = f"save_slot_{idx}.json"
            slot_desc = f"BANK {idx} : [ VACANT SLOT ] - 空白记忆区间 - (Empty Memory Slot)"
            has_save = False

            if os.path.exists(fn):
                has_save = True
                try:
                    with open(fn, "r", encoding="utf-8") as f:
                        sdata = json.load(f)
                    char_id = sdata.get("current_char_id", "saki")
                    char_name = "纱希 (Saki)" if char_id == "saki" else f"自定义 ({char_id})"
                    day = sdata.get("current_day", 1)
                    favor = sdata.get("favorability", 50)
                    sus = sdata.get("suspicion", 20)
                    slot_desc = f"BANK {idx} : [ ACTIVE ] 第 {day} 天 | 好感: {favor}% 疑心: {sus}% | 神经宿主: {char_name}"
                except Exception:
                    slot_desc = f"BANK {idx} : [ CORRUPTED ] 已占用 (读取错误)"

            slot_row = tk.Frame(slots_container, bg="#000000")
            slot_row.pack(fill=tk.X, pady=3)

            lbl_desc = tk.Label(
                slot_row, text=slot_desc, fg="#00FF66" if has_save else "#333333", bg="#000000",
                font=("Consolas", 9, "bold" if has_save else "normal"), anchor=tk.W
            )
            lbl_desc.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def make_load_cmd(slot_num):
                return lambda: self._load_slot_from_splash(slot_num)

            btn_load = tk.Button(
                slot_row, text=" 载入突触 ", fg="#00FF66" if has_save else "#333333", bg="#000000",
                activeforeground="#00FF66", activebackground="#001805",
                relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"), width=12,
                state=tk.NORMAL if has_save else tk.DISABLED,
                command=make_load_cmd(idx)
            )
            btn_load.pack(side=tk.RIGHT)
            if has_save:
                btn_load.bind("<Enter>", lambda e, b=btn_load: b.config(fg="#00FF66", bg="#002208"))
                btn_load.bind("<Leave>", lambda e, b=btn_load: b.config(fg="#00FF66", bg="#000000"))

            if has_save:
                def make_delete_cmd(slot_num):
                    return lambda: self._delete_slot_from_splash(slot_num)
                btn_delete = tk.Button(
                    slot_row, text=" 删除 ", fg="#FF3333", bg="#000000",
                    activeforeground="#FFFFFF", activebackground="#E74C3C",
                    relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"), width=8,
                    command=make_delete_cmd(idx)
                )
                btn_delete.pack(side=tk.RIGHT, padx=(0, 6))
                btn_delete.bind("<Enter>", lambda e, b=btn_delete: b.config(fg="#FFFFFF", bg="#800000"))
                btn_delete.bind("<Leave>", lambda e, b=btn_delete: b.config(fg="#FF3333", bg="#000000"))

    def _sync_api_from_splash(self):
        """Sync values from splash screen API entries to self.config and save."""
        if hasattr(self, "entry_splash_key"):
            key_val = self.entry_splash_key.get_actual_value().strip()
            self.config["api_key"] = key_val
            if hasattr(self, "entry_key") and self.entry_key.winfo_exists():
                self.entry_key.delete(0, tk.END)
                self.entry_key.insert(0, key_val)
                if key_val:
                    self.entry_key.config(fg="#FF0000", show="*")
                else:
                    self.entry_key._show_placeholder()

        if hasattr(self, "entry_splash_base"):
            base_val = self.entry_splash_base.get_actual_value().strip()
            self.config["api_base"] = base_val
            if hasattr(self, "entry_base") and self.entry_base.winfo_exists():
                self.entry_base.delete(0, tk.END)
                self.entry_base.insert(0, base_val)
                if base_val:
                    self.entry_base.config(fg="#FF0000")
                else:
                    self.entry_base._show_placeholder()

        save_config(self.config)

    def _test_api_connection_from_settings(self):
        key = self.entry_key.get_actual_value().strip()
        base = self.entry_base.get_actual_value().strip() or "https://api.deepseek.com"

        if not key:
            messagebox.showwarning("测试失败", "请先在上方输入 API Key！")
            return

        self.btn_test_api_settings.config(text=" 测试中... ", state=tk.DISABLED)

        def run_test():
            import requests
            url = f"{base.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            model = self.entry_model.get_actual_value().strip() or "deepseek-v4-flash"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5,
                "temperature": 0.0,
            }

            start_time = time.time()
            try:
                response = requests.post(
                    url, headers=headers, json=payload, timeout=10,
                    proxies={"http": None, "https": None}
                )
                elapsed = int((time.time() - start_time) * 1000)
                if response.status_code == 200:
                    result = ("SUCCESS", f"脑机突触链路连接成功！\n当前响应延迟: {elapsed}ms")
                else:
                    result = ("ERROR", f"联通性异常！HTTP 错误代码: {response.status_code}\n请检查您的 Key 或网络设置。")
            except Exception as e:
                result = ("ERROR", f"链路握手超时或网络地址无效：\n{e}")

            def update_ui():
                self.btn_test_api_settings.config(text=" 测试连接 ", state=tk.NORMAL)
                if result[0] == "SUCCESS":
                    messagebox.showinfo("测试成功", result[1])
                else:
                    messagebox.showerror("测试失败", result[1])
            self.root.after(0, update_ui)

        threading.Thread(target=run_test, daemon=True).start()

    def _test_api_connection(self):
        key = self.entry_splash_key.get_actual_value().strip()
        base = self.entry_splash_base.get_actual_value().strip() or "https://api.deepseek.com"

        if not key:
            self.lbl_test_status.config(text="[ 状态: ⚠️ 请先输入 API Key ]", fg="#E67E22")
            return

        self.lbl_test_status.config(text="[ 状态: 📡 正在建立神经突触链路... ]", fg="#F1C40F")

        # Start background test thread
        thread = threading.Thread(target=self._run_api_test, args=(key, base), daemon=True)
        thread.start()

    def _run_api_test(self, key, base):
        import requests
        url = f"{base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        model = self.config.get("model_name", "deepseek-v4-flash") or "deepseek-v4-flash"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
            "temperature": 0.0,
        }

        start_time = time.time()
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=10,
                proxies={"http": None, "https": None}
            )
            elapsed = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                status_text = f"[ 状态: 🟢 链路连接成功 ({elapsed}ms) ]"
                status_color = "#2ECC71"
            else:
                status_text = f"[ 状态: 🔴 错误 {response.status_code} (请检查配置) ]"
                status_color = "#E74C3C"
        except Exception as e:
            status_text = f"[ 状态: 🔴 链路超时或地址错误 ]"
            status_color = "#E74C3C"

        self.root.after(0, lambda: self.lbl_test_status.config(text=status_text, fg=status_color))

    def _start_game_with_language(self, chosen_lang):
        self._sync_api_from_splash()
        chosen_lang = normalize_language(chosen_lang)
        self.selected_language.set(chosen_lang)
        self.state.cached_lang = chosen_lang  # step 2
        self.user_explicitly_selected_lang = True

        # Perform a complete reset of all game state, chat history, and visual effects to start fresh (HoI4 style)
        self._restart_game()

        self.config["selected_language"] = chosen_lang
        self._load_language_default_voice(chosen_lang)
        save_config(self.config)

        self._update_ui_language()

        if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
            self.splash_frame.destroy()

    # ========================================================================

    # ========================================================================
    #  Fourth-Wall Break & Typing Hijack Mechanisms
    # ========================================================================

    def _start_fourth_wall_monitor(self):
        """Start the background thread monitoring suspicion / escape_rate for fourth-wall break."""
        def monitor_worker():
            while True:
                if self.state.game_over:
                    time.sleep(1.0)
                    continue

                suspicion = self.state.suspicion
                escape_rate = self.state.escape_rate

                # High anxiety threshold (>= 75)
                if suspicion >= 75 or escape_rate >= 75:
                    if not getattr(self, "input_hijacked", False):
                        self.input_hijacked = True
                        self.hijack_char_index = 0
                        self.current_hijack_phrase = None
                        print(f"[第四面墙] 焦虑值爆涨 (疑心={suspicion}, 逃脱={escape_rate})，已启动输入框劫持！")
                else:
                    if getattr(self, "input_hijacked", False):
                        self.input_hijacked = False
                        self.hijack_char_index = 0
                        self.current_hijack_phrase = None
                        print("[第四面墙] 焦虑值正常，解除输入框劫持。")

                time.sleep(0.4)

        t = threading.Thread(target=monitor_worker, daemon=True)
        t.start()

    def _on_entry_key_press(self, event):
        """Hijack entry keypress when anxiety level is critical (>= 75)."""
        if getattr(self, "input_hijacked", False):
            # Let functional/navigation keys pass so the player can submit, navigate, etc.
            if event.keysym in ("Return", "Tab", "Escape", "Right", "Left", "Up", "Down"):
                return None

            if event.keysym == "BackSpace":
                # Physically block backspacing for extra creepy physical oppression
                return "break"

            phrase = "你走不掉的你走不掉的你走不掉的你走不掉 the 你走不掉的你走不掉的你走不掉的……"

            # Cache the phrase for consistency during this single sentence
            if not getattr(self, "current_hijack_phrase", None):
                self.current_hijack_phrase = phrase
            phrase = self.current_hijack_phrase

            # Get the next character in sequence
            idx = getattr(self, "hijack_char_index", 0)
            char_to_insert = phrase[idx % len(phrase)]
            self.entry_input.insert(tk.INSERT, char_to_insert)
            self.hijack_char_index = idx + 1

            # Play high-pitch tension feedback click
            self.sound_mgr.play_beep(random.randint(600, 750), 30)

            # Prevent the default keyboard typing behavior
            return "break"
        return None

    def _set_typing_state(self, is_typing):
        self.is_typing = is_typing
        loc = LOCALIZATION[normalize_language(self.selected_language.get())]
        if not hasattr(self, "anti_escape_frame"):
            if is_typing:
                self.entry_input.config(state=tk.DISABLED)
                self.btn_send.config(state=tk.DISABLED, text=loc["speaking"])
                self.root.config(cursor="watch")
            else:
                self.entry_input.config(state=tk.NORMAL)
                self.btn_send.config(state=tk.NORMAL, text=loc["respond"])
                self.root.config(cursor="")
                self.entry_input.focus_set()

    # ========================================================================
    #  Mock reply generator
    # ========================================================================

    def _generate_mock_reply(self, user_input):
        lang = normalize_language(self.selected_language.get())
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

    # ========================================================================
    #  Anti-escape / window resize
    # ========================================================================

    def _on_window_resized(self, event=None):
        if event and str(event.widget) != ".":
            return
        if self.state.game_over:
            return
        width = self.root.winfo_width()
        if width <= 200:
            return

        is_zoomed = self.root.state() == "zoomed"
        is_fullscreen = bool(self.root.attributes("-fullscreen"))

        if width < 1000 and not is_zoomed and not is_fullscreen:
            self._show_anti_escape_warning(True)
        else:
            self._show_anti_escape_warning(False)

    def _show_anti_escape_warning(self, show):
        if show:
            if hasattr(self, "anti_escape_frame") and self.anti_escape_frame.winfo_exists():
                return
            self.entry_input.config(state=tk.DISABLED)
            self.btn_send.config(state=tk.DISABLED)

            self.anti_escape_frame = tk.Frame(self.root, bg="#1A0000")
            self.anti_escape_frame.place(x=0, y=0, relwidth=1, relheight=1)
            self.anti_escape_frame.lift()

            lbl_warning = tk.Label(
                self.anti_escape_frame,
                text=LOCALIZATION[normalize_language(self.selected_language.get())]["anti_escape"],
                fg="#FF0000",
                bg="#1A0000",
                font=("Microsoft YaHei", 16, "bold"),
                justify=tk.CENTER,
            )
            lbl_warning.pack(expand=True)

            def pulse_text(state=0):
                if not hasattr(self, "anti_escape_frame") or not self.anti_escape_frame.winfo_exists():
                    return
                colors = ["#FF0000", "#CC0000", "#990000", "#660000", "#990000", "#CC0000"]
                lbl_warning.config(fg=colors[state % len(colors)])
                self.root.after(200, lambda: pulse_text(state + 1))

            pulse_text()
        else:
            if hasattr(self, "anti_escape_frame") and self.anti_escape_frame.winfo_exists():
                self.anti_escape_frame.destroy()
                if hasattr(self, "anti_escape_frame"):
                    delattr(self, "anti_escape_frame")

                if not self.is_typing and not self.state.game_over:
                    self.entry_input.config(state=tk.NORMAL)
                    self.btn_send.config(state=tk.NORMAL)
                    self.entry_input.focus_set()

    def _emergency_clear_overlays(self):
        self.overlay_mgr.force_clear()
        if hasattr(self, "_flood_canvas_ref") and self._flood_canvas_ref is not None:
            self._safe_destroy_widget(self._flood_canvas_ref)
            self._flood_canvas_ref = None
        self.barrage_active = False

    def _load_language_default_voice(self, lang):
        """Automatically load default reference audio, texts, and hot-load models based on chosen language."""
        if lang not in DEFAULT_LANGUAGE_VOICES:
            return

        vcfg = DEFAULT_LANGUAGE_VOICES[lang]
        ref_wav = vcfg.get("refer_wav_path", "")
        prompt_t = vcfg.get("prompt_text", "")
        gpt_w = vcfg.get("gpt_weights_path", "")
        sovits_w = vcfg.get("sovits_weights_path", "")

        # Auto-fill GUI fields if they exist
        if hasattr(self, "entry_refer_wav") and self.entry_refer_wav.winfo_exists():
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, ref_wav)
            self.entry_refer_wav.config(fg="#FF0000")
        self.refer_wav_path = ref_wav

        if hasattr(self, "entry_prompt_text") and self.entry_prompt_text.winfo_exists():
            self.entry_prompt_text.delete(0, tk.END)
            self.entry_prompt_text.insert(0, prompt_t)
            self.entry_prompt_text.config(fg="#FF0000")
        self.prompt_text = prompt_t

        if hasattr(self, "entry_gpt_weights") and self.entry_gpt_weights.winfo_exists():
            self.entry_gpt_weights.delete(0, tk.END)
            self.entry_gpt_weights.insert(0, gpt_w)
            self.entry_gpt_weights.config(fg="#FF0000")
        self.gpt_weights_path = gpt_w

        if hasattr(self, "entry_sovits_weights") and self.entry_sovits_weights.winfo_exists():
            self.entry_sovits_weights.delete(0, tk.END)
            self.entry_sovits_weights.insert(0, sovits_w)
            self.entry_sovits_weights.config(fg="#FF0000")
        self.sovits_weights_path = sovits_w

        # Save to config
        self.config["refer_wav_path"] = ref_wav
        self.config["prompt_text"] = prompt_t
        self.config["gpt_weights_path"] = gpt_w
        self.config["sovits_weights_path"] = sovits_w

        # Trigger hot-load in the background if files exist
        if gpt_w and os.path.exists(gpt_w):
            self._async_load_weights("gpt", gpt_w)
        if sovits_w and os.path.exists(sovits_w):
            self._async_load_weights("sovits", sovits_w)

        print(f"[Language Defaults] Successfully loaded default voice model configurations for: {lang}")

    def _on_alt_f4(self):
        """Safeguard window closing on Alt-F4 by redirecting to Load Slot 4."""
        print("[Alt-F4 Intercepted] Slot 4 recovery safety active.")
        self.load_slot4()
        return "break"

    def _on_esc_pressed(self):
        """Handle ESC key pressed to notify the user, perform autosave, and open Slots Overwrite Panel."""
        if self.state.game_over:
            return

        # Write auto-save indicator in chat log
        self._write_chat_log("【系统】检测到神经断开指令！自动保存中……已成功锁定当前意识进度。\n", "system")

        # Capture current settings values
        api_key = self.entry_key.get_actual_value()

        # Save an emergency state auto-save so we have it
        try:
            emergency_data = {
                "current_day": self.state.current_day,
                "favorability": self.state.favorability,
                "suspicion": self.state.suspicion,
                "escape_rate": self.state.escape_rate,
                "chat_history": self.chat_history,
                "api_key": api_key,
                "current_char_id": getattr(self.state, "current_char_id", "saki"),
                "selected_language": self.state.cached_lang,
            }
            with open("save_slot_autosave.json", "w", encoding="utf-8") as f:
                json.dump(emergency_data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

        # Create beautiful Toplevel save dialog
        pop = tk.Toplevel(self.root)
        pop.title("神经接口断开与存档管理")
        pop.geometry("640x520")
        pop.configure(bg="#000000")
        pop.resizable(False, False)
        pop.transient(self.root)
        pop.grab_set()

        lbl_header = tk.Label(
            pop, text="[ 神经同步断开与存档面板 / Save Slots ]", fg="#FF0000", bg="#000000",
            font=("Consolas", 14, "bold")
        )
        lbl_header.pack(pady=15)

        slots_frame = tk.Frame(pop, bg="#000000")
        slots_frame.pack(fill=tk.BOTH, expand=True, padx=25)

        selected_slot_var = tk.IntVar(value=1)

        def delete_slot_in_popup(slot_num):
            if messagebox.askyesno("删除确认", f"您确定要永久删除记忆槽位 {slot_num} 吗？"):
                fn = f"save_slot_{slot_num}.json"
                if os.path.exists(fn):
                    try:
                        os.remove(fn)
                        print(f"[ESC Delete] Deleted slot {slot_num}")
                    except Exception as e:
                        print(f"[ESC Delete Fail] {e}")
                refresh_slots()

        def refresh_slots():
            for widget in slots_frame.winfo_children():
                widget.destroy()

            occupied_count = 0
            slot_infos = {}
            has_save_dict = {}
            for idx in range(1, 6):
                fn = f"save_slot_{idx}.json"
                if os.path.exists(fn):
                    occupied_count += 1
                    has_save_dict[idx] = True
                    try:
                        with open(fn, "r", encoding="utf-8") as f:
                            sdata = json.load(f)
                        char_id = sdata.get("current_char_id", "saki")
                        char_name = "纱希 (Saki)" if char_id == "saki" else f"自定义 ({char_id})"
                        slot_infos[idx] = f"第 {sdata.get('current_day', 1)} 天 | {char_name} | 好感:{sdata.get('favorability', 50)} 疑心:{sdata.get('suspicion', 20)}"
                    except Exception:
                        slot_infos[idx] = "已占用 (读取错误)"
                else:
                    has_save_dict[idx] = False
                    slot_infos[idx] = "- 空白记忆槽位 -"

            if occupied_count >= 5:
                lbl_warning = tk.Label(
                    slots_frame, text="【警告】所有记忆槽位已满！保存进度将覆盖选中的旧存档。",
                    fg="#FF3333", bg="#000000", font=("Microsoft YaHei", 9, "bold"), wrap=480, justify=tk.LEFT
                )
                lbl_warning.pack(fill=tk.X, pady=(0, 10))

            # Render 5 slots with Radiobutton
            for idx in range(1, 6):
                sf = tk.Frame(slots_frame, bg="#000000")
                sf.pack(fill=tk.X, pady=6)

                # Radio button to select this slot
                rb = tk.Radiobutton(
                    sf, text=f"Slot {idx}:", variable=selected_slot_var, value=idx,
                    fg="#FF3399", bg="#000000", selectcolor="#000000",
                    activeforeground="#FF0000", activebackground="#000000",
                    font=("Consolas", 10, "bold"), width=9, anchor=tk.W
                )
                rb.pack(side=tk.LEFT)

                info_fg = "#FF3399" if has_save_dict[idx] else "#555555"
                lbl_info = tk.Label(
                    sf, text=slot_infos[idx], fg=info_fg, bg="#000000",
                    font=("Microsoft YaHei", 9), anchor=tk.W
                )
                lbl_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

                if has_save_dict[idx]:
                    def make_del_cmd(slot_num):
                        return lambda: delete_slot_in_popup(slot_num)
                    btn_del = tk.Button(
                        sf, text="删除", fg="#FF3333", bg="#0D0000",
                        activeforeground="#FFFFFF", activebackground="#220000",
                        relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"), width=6,
                        command=make_del_cmd(idx)
                    )
                    btn_del.pack(side=tk.RIGHT)

        refresh_slots()

        def save_and_return():
            slot_num = selected_slot_var.get()
            fn = f"save_slot_{slot_num}.json"
            if os.path.exists(fn):
                if not messagebox.askyesno("覆盖存档", f"槽位 {slot_num} 已经有存档了，是否覆盖它？"):
                    return

            try:
                # Capture current settings values
                api_key = self.entry_key.get_actual_value()
                data = {
                    "current_day": self.state.current_day,
                    "favorability": self.state.favorability,
                    "suspicion": self.state.suspicion,
                    "escape_rate": self.state.escape_rate,
                    "chat_history": self.chat_history,
                    "api_key": api_key,
                    "current_char_id": getattr(self.state, "current_char_id", "saki"),
                    "selected_language": self.state.cached_lang,
                }
                with open(fn, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"[ESC Save] Successfully saved to slot {slot_num}")
            except Exception as e:
                messagebox.showerror("存档失败", f"无法保护您的神经进度：{e}")
                return

            pop.destroy()
            self._disconnect_to_splash()

        bf = tk.Frame(pop, bg="#000000")
        bf.pack(fill=tk.X, side=tk.BOTTOM, pady=25)

        btn_save_ret = tk.Button(
            bf, text="保存并返回主菜单", fg="#2ECC71", bg="#0D0000",
            activeforeground="#FFFFFF", activebackground="#27AE60",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9, "bold"), width=16,
            command=save_and_return
        )
        btn_save_ret.pack(side=tk.LEFT, padx=(30, 10))

        btn_direct_exit = tk.Button(
            bf, text="直接退出（不保存）", fg="#FF3333", bg="#0D0000",
            activeforeground="#FFFFFF", activebackground="#C0392B",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9, "bold"), width=16,
            command=lambda: [pop.destroy(), self._disconnect_to_splash()]
        )
        btn_direct_exit.pack(side=tk.LEFT, padx=10)

        btn_cancel = tk.Button(
            bf, text="返回", fg="#888888", bg="#0D0D0D",
            activeforeground="#FFFFFF", activebackground="#222222",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9), width=10,
            command=pop.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, padx=30)

    def _disconnect_to_splash(self):
        """Tear down gameplay and return to startup screen."""
        self._emergency_clear_overlays()
        self.state.game_over = False
        self.sound_mgr.stop_voice()
        self._show_splash_screen()

    def _on_splash_settings_clicked(self):
        """Pop up the Custom Character Profile input editor directly from the Splash screen."""
        pop = tk.Toplevel(self.root)
        pop.title("自定义角色脑回路配置")
        pop.geometry("640x720")
        pop.configure(bg="#000000")
        pop.resizable(False, False)
        pop.transient(self.root)
        pop.grab_set()

        lbl_title = tk.Label(
            pop, text="[ ⚙ 自定义神经角色脑回路配置 ]", fg="#FF0000", bg="#000000",
            font=("Consolas", 12, "bold")
        )
        lbl_title.pack(pady=15)

        form = tk.Frame(pop, bg="#000000")
        form.pack(fill=tk.BOTH, expand=True, padx=30)

        row_idx = 0
        def add_field(label_text, is_large=False):
            nonlocal row_idx
            lbl = tk.Label(form, text=label_text, fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
            lbl.grid(row=row_idx, column=0, sticky=tk.W, pady=3)

            if is_large:
                text_widget = tk.Text(form, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000",
                                     relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9), height=3, width=50, wrap=tk.WORD)
                text_widget.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
                row_idx += 1
                return text_widget
            else:
                entry_widget = tk.Entry(form, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000",
                                       relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9), width=50)
                entry_widget.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
                row_idx += 1
                return entry_widget

        ent_name = add_field("角色姓名 (Name):")
        ent_age = add_field("角色年龄 (Age):")
        txt_personality = add_field("性格设定 (Personality):", is_large=True)
        txt_story = add_field("背景与故事主线 (Story):", is_large=True)
        txt_plot = add_field("特有交互剧情 (Plot):", is_large=True)
        txt_world = add_field("所处世界观 (World):", is_large=True)
        ent_color = add_field("聊天文字颜色 (Color):")

        # WAV Reference with browse
        lbl_wav = tk.Label(form, text="参考音频 (.wav):", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
        lbl_wav.grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        wav_frame = tk.Frame(form, bg="#000000")
        wav_frame.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
        ent_wav = tk.Entry(wav_frame, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9))
        ent_wav.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def browse_wav():
            fn = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
            if fn:
                ent_wav.delete(0, tk.END)
                ent_wav.insert(0, fn)
        btn_browse = tk.Button(wav_frame, text="浏览", fg="#8A0303", bg="#0D0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8), command=browse_wav)
        btn_browse.pack(side=tk.RIGHT, padx=(5, 0))
        row_idx += 1

        ent_text = add_field("参考音频文本 (Text):")

        # Weights paths
        lbl_gpt = tk.Label(form, text="GPT 权重 (.ckpt):", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
        lbl_gpt.grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        gpt_frame = tk.Frame(form, bg="#000000")
        gpt_frame.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
        ent_gpt = tk.Entry(gpt_frame, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9))
        ent_gpt.pack(side=tk.LEFT, fill=tk.X, expand=True)
        def browse_gpt():
            fn = filedialog.askopenfilename(filetypes=[("Weights files", "*.ckpt")])
            if fn:
                ent_gpt.delete(0, tk.END)
                ent_gpt.insert(0, fn)
        btn_bgpt = tk.Button(gpt_frame, text="浏览", fg="#8A0303", bg="#0D0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8), command=browse_gpt)
        btn_bgpt.pack(side=tk.RIGHT, padx=(5, 0))
        row_idx += 1

        lbl_sovits = tk.Label(form, text="SoVITS 权重 (.pth):", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold"), anchor=tk.W)
        lbl_sovits.grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        sovits_frame = tk.Frame(form, bg="#000000")
        sovits_frame.grid(row=row_idx, column=1, sticky=tk.EW, padx=10, pady=3)
        ent_sovits = tk.Entry(sovits_frame, bg="#0D0000", fg="#FF3399", insertbackground="#FF0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 9))
        ent_sovits.pack(side=tk.LEFT, fill=tk.X, expand=True)
        def browse_sovits():
            fn = filedialog.askopenfilename(filetypes=[("Weights files", "*.pth")])
            if fn:
                ent_sovits.delete(0, tk.END)
                ent_sovits.insert(0, fn)
        btn_bsovits = tk.Button(sovits_frame, text="浏览", fg="#8A0303", bg="#0D0000", relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8), command=browse_sovits)
        btn_bsovits.pack(side=tk.RIGHT, padx=(5, 0))
        row_idx += 1

        form.columnconfigure(1, weight=1)

        # Load existing custom character data if exists
        custom_data = {}
        if os.path.exists("custom_characters.json"):
            try:
                with open("custom_characters.json", "r", encoding="utf-8") as f:
                    custom_data = json.load(f)
            except Exception:
                pass

        cdata = custom_data.get("custom", custom_data.get("sparkle", {}))
        ent_name.insert(0, cdata.get("name", "花火"))
        ent_age.insert(0, cdata.get("age", "18"))
        txt_personality.insert("1.0", cdata.get("personality", "小恶魔、变幻莫测、疯狂、腹黑，极度热爱捉弄玩家"))
        txt_story.insert("1.0", cdata.get("main_story", "她是假面愚者的成员，将玩家关进了一个布满迷幻霓虹与马戏团玩具的游乐园密室，用各种虚实难辨的游戏爱着你"))
        txt_plot.insert("1.0", cdata.get("character_plot", "每当你表现出顺从，她就会露出天真烂漫的笑容；而一旦你试图逃跑，她就会微笑着摆弄炸弹引爆器"))
        txt_world.insert("1.0", cdata.get("world_view", "一个充满迷幻霓虹、马戏团狂欢和荒诞黑色幽默的虚无主义都市"))
        ent_color.insert(0, cdata.get("chat_color", "#FF3399"))
        ent_wav.insert(0, cdata.get("refer_wav_path", "D:/花火/yingping/huahuo.wav_0000000000_0000061760.wav"))
        ent_text.insert(0, cdata.get("prompt_text", "独向昭谈至恶龙一阁著文章。"))
        ent_gpt.insert(0, cdata.get("gpt_weights_path", "D:/花火/Huahuo_Yandere-e10.ckpt"))
        ent_sovits.insert(0, cdata.get("sovits_weights_path", "D:/花火/Huahuo_Yandere_e10_s440.pth"))

        def save_custom_char():
            cdata_new = {
                "name": ent_name.get().strip() or "自定义角色",
                "age": ent_age.get().strip() or "18",
                "personality": txt_personality.get("1.0", tk.END).strip(),
                "main_story": txt_story.get("1.0", tk.END).strip(),
                "character_plot": txt_plot.get("1.0", tk.END).strip(),
                "world_view": txt_world.get("1.0", tk.END).strip(),
                "chat_color": ent_color.get().strip() or "#FF3399",
                "refer_wav_path": ent_wav.get().strip(),
                "prompt_text": ent_text.get().strip(),
                "gpt_weights_path": ent_gpt.get().strip(),
                "sovits_weights_path": ent_sovits.get().strip(),
            }
            custom_data["custom"] = cdata_new
            try:
                with open("custom_characters.json", "w", encoding="utf-8") as f:
                    json.dump(custom_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("成功", "自定义角色脑波参数保存成功！")
                pop.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存自定义角色脑回路失败：{e}")

        btn_save = tk.Button(
            pop, text="保存角色配置", fg="#2ECC71", bg="#001F00", activeforeground="#2ECC71", activebackground="#053005",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 10, "bold"), width=20, height=2,
            command=save_custom_char
        )
        btn_save.pack(pady=15)

    def _load_slot_from_splash(self, slot_num):
        """Instantly load gameplay slot directly from Splash screen, bypassing greetings."""
        filename = f"save_slot_{slot_num}.json"
        if not os.path.exists(filename):
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Apply loaded states
            self.state.current_day = data.get("current_day", 1)
            self.state.favorability = data.get("favorability", 50)
            self.state.suspicion = data.get("suspicion", 20)
            self.state.escape_rate = data.get("escape_rate", 0)
            self.chat_history = data.get("chat_history", [{"role": "system", "content": ""}])

            loaded_key = data.get("api_key", "")
            if loaded_key:
                self.entry_key.delete(0, tk.END)
                self.entry_key.insert(0, loaded_key)
                self.entry_key.config(fg="#FF0000")

            # Swap character
            char_id = data.get("current_char_id", "saki")
            self.change_character(char_id)

            # Map UI language from slot data if available, fallback to detecting from history, then global configs
            chosen_lang = data.get("selected_language")
            if not chosen_lang:
                # Try to detect from chat history
                history = data.get("chat_history", [])
                detected = None
                for msg in reversed(history):
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "")
                        if "<think>" in content and "</think>" in content:
                            content = content.split("</think>")[-1]
                        # If it has Hiragana/Katakana, it is Japanese
                        if re.search(r"[぀-ゟ゠-ヿ]", content):
                            detected = "日本語"
                            break
                        det = detect_language(content, None)
                        if det:
                            detected = det
                            break
                chosen_lang = detected or self.config.get("selected_language", "中文")

            chosen_lang = normalize_language(chosen_lang)
            self.selected_language.set(chosen_lang)
            self.state.cached_lang = chosen_lang
            self.user_explicitly_selected_lang = True

            self.config["selected_language"] = chosen_lang
            save_config(self.config)

            self._update_ui_language()
            self._sync_stats_to_gui()
            self._restore_chat_history_to_gui()

            # Destroy splash screen smoothly
            if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
                self.splash_frame.destroy()

            self._write_chat_log(f"【系统】脑机突触建立成功！已从 Slot {slot_num} 恢复神经记忆回路。\n", "system")
            print(f"[Splash Load] Successfully loaded memory Slot {slot_num}")
        except Exception as e:
            messagebox.showerror("载入失败", f"无法唤醒该插槽的记忆电位：{e}")

    def _delete_slot_from_splash(self, slot_num):
        """Confirm and physically delete a save slot file directly from Splash screen, then refresh."""
        if messagebox.askyesno("删除确认", f"您确定要永久删除记忆槽位 {slot_num} 吗？"):
            fn = f"save_slot_{slot_num}.json"
            if os.path.exists(fn):
                try:
                    os.remove(fn)
                    print(f"[删除存档] 已删除 {fn}")
                except Exception as e:
                    print(f"[删除存档失败] {e}")
            self._show_splash_screen()

    # ========================================================================
    #  Settings toggle
    # ========================================================================

    def _toggle_settings(self):
        if self.settings_visible:
            self.top_bar.pack_forget()
            self.settings_frame.pack_forget()
            self.settings_visible = False
            self.btn_toggle_settings.config(text="[ 展开配置通道 ]", fg="#666666")
        else:
            self.top_bar.pack(before=self.canvas_ecg, fill=tk.X, padx=10, pady=5)
            self.settings_frame.pack(before=self.canvas_ecg, fill=tk.X, padx=10, pady=5)
            self.btn_toggle_settings.config(text="[ 收起配置通道 ]", fg="#8A0303")
            self.settings_visible = True
            self._animate_panel_fade_in()

    # ========================================================================
    #  Splash screen
    # ========================================================================

    def _show_splash_screen(self):
        if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
            self.splash_frame.destroy()
        self.splash_frame = tk.Frame(self.root, bg="#000000")
        self.splash_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.splash_frame.lift()

        lbl_splash_title = tk.Label(
            self.splash_frame,
            text="纱希 (Saki) - Terminal A.I.",
            fg="#FF0000",
            bg="#000000",
            font=("Consolas", 24, "bold"),
        )
        lbl_splash_title.pack(pady=(60, 10))

        lbl_splash_subtitle = tk.Label(
            self.splash_frame,
            text="[ 请选择与纱希脑机接口建立连接的语言 ]\n\n[ Select Saki's Interface & Voice Language ]",
            fg="#8A0303",
            bg="#000000",
            font=("Microsoft YaHei", 11, "bold"),
            justify=tk.CENTER,
        )
        lbl_splash_subtitle.pack(pady=(0, 20))

        btn_frame = tk.Frame(self.splash_frame, bg="#000000")
        btn_frame.pack(pady=5)

        langs = [
            ("简体中文", "中文"),
            ("English", "English"),
            ("日本語", "日本語"),
        ]

        for text, lang_val in langs:
            btn = tk.Button(
                btn_frame,
                text=text,
                fg="#8A0303",
                bg="#000000",
                activeforeground="#FF0000",
                activebackground="#0D0000",
                relief=tk.SOLID,
                bd=1,
                font=("Microsoft YaHei", 12, "bold"),
                width=16,
                height=2,
                command=lambda l=lang_val: self._start_game_with_language(l),
            )
            btn.pack(side=tk.LEFT, padx=15)
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg="#FF0000", bg="#0F0000", highlightbackground="#FF0000"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="#8A0303", bg="#000000", highlightbackground="#222222"))

        # Separator
        div = tk.Frame(self.splash_frame, height=1, bg="#222222")
        div.pack(fill=tk.X, padx=100, pady=15)

        # Settings button for custom characters
        self.btn_splash_settings = tk.Button(
            self.splash_frame,
            text=" ⚙ 自定义角色配置 / Custom Character Settings ",
            fg="#FF0000",
            bg="#0A0000",
            activeforeground="#FF0000",
            activebackground="#200000",
            relief=tk.SOLID,
            bd=1,
            font=("Microsoft YaHei", 10, "bold"),
            command=self._on_splash_settings_clicked
        )
        self.btn_splash_settings.pack(pady=5)
        self.btn_splash_settings.bind("<Enter>", lambda e: self.btn_splash_settings.config(fg="#FF3399", bg="#150000"))
        self.btn_splash_settings.bind("<Leave>", lambda e: self.btn_splash_settings.config(fg="#FF0000", bg="#0A0000"))

        # Save Slots Title
        lbl_slots_title = tk.Label(
            self.splash_frame,
            text="[ 脑机接口历史记忆载入 / Memory Slot Management ]",
            fg="#8A0303",
            bg="#000000",
            font=("Consolas", 11, "bold")
        )
        lbl_slots_title.pack(pady=(15, 5))

        slots_container = tk.Frame(self.splash_frame, bg="#000000")
        slots_container.pack(fill=tk.X, padx=100, pady=5)

        for idx in range(1, 6):
            fn = f"save_slot_{idx}.json"
            slot_desc = f"Slot {idx}: - 空白记忆槽位 - (Empty Memory Slot)"
            has_save = False

            if os.path.exists(fn):
                has_save = True
                try:
                    with open(fn, "r", encoding="utf-8") as f:
                        sdata = json.load(f)
                    char_id = sdata.get("current_char_id", "saki")
                    char_name = "纱希 (Saki)" if char_id == "saki" else f"自定义 ({char_id})"
                    day = sdata.get("current_day", 1)
                    favor = sdata.get("favorability", 50)
                    sus = sdata.get("suspicion", 20)
                    slot_desc = f"Slot {idx}: 第 {day} 天 | 角色: {char_name} | 好感: {favor} 疑心: {sus}"
                except Exception:
                    slot_desc = f"Slot {idx}: 已占用 (读取错误)"

            slot_row = tk.Frame(slots_container, bg="#000000")
            slot_row.pack(fill=tk.X, pady=2)

            lbl_desc = tk.Label(
                slot_row, text=slot_desc, fg="#FF3399" if has_save else "#444444", bg="#000000",
                font=("Microsoft YaHei", 9), anchor=tk.W
            )
            lbl_desc.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def make_load_cmd(slot_num):
                return lambda: self._load_slot_from_splash(slot_num)

            btn_load = tk.Button(
                slot_row, text="载入记忆", fg="#2ECC71" if has_save else "#333333", bg="#000000",
                activeforeground="#2ECC71", activebackground="#0A150A",
                relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"), width=10,
                state=tk.NORMAL if has_save else tk.DISABLED,
                command=make_load_cmd(idx)
            )
            btn_load.pack(side=tk.RIGHT)

            if has_save:
                def make_delete_cmd(slot_num):
                    return lambda: self._delete_slot_from_splash(slot_num)
                btn_delete = tk.Button(
                    slot_row, text="删除", fg="#E74C3C", bg="#000000",
                    activeforeground="#FFFFFF", activebackground="#C0392B",
                    relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"), width=6,
                    command=make_delete_cmd(idx)
                )
                btn_delete.pack(side=tk.RIGHT, padx=(0, 5))

    def _start_game_with_language(self, chosen_lang):
        chosen_lang = normalize_language(chosen_lang)
        self.selected_language.set(chosen_lang)
        self.state.cached_lang = chosen_lang  # step 2
        self.user_explicitly_selected_lang = True

        # Perform a complete reset of all game state, chat history, and visual effects to start fresh (HoI4 style)
        self._restart_game()

        self.config["selected_language"] = chosen_lang
        self._load_language_default_voice(chosen_lang)
        save_config(self.config)

        self._update_ui_language()

        if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
            self.splash_frame.destroy()

    # ========================================================================
    #  Language change handler
    # ========================================================================

    def _on_language_changed(self):
        self.user_explicitly_selected_lang = True
        self.selected_language.set(normalize_language(self.selected_language.get()))
        self.state.cached_lang = self.selected_language.get()  # step 2

        self.config["selected_language"] = self.selected_language.get()
        self._load_language_default_voice(self.selected_language.get())
        save_config(self.config)

        if self.chat_history:
            self.chat_history[0]["content"] = self._get_dynamic_system_prompt()

        self._update_ui_language()

    def _update_ui_language(self):
        lang = normalize_language(self.selected_language.get())
        self.selected_language.set(lang)
        self.state.cached_lang = lang  # step 2
        loc = LOCALIZATION[lang]

        self.lbl_day.config(text=loc["day"].format(day=self.state.current_day))
        self.lbl_favor_title.config(text=loc["favorability"])
        self.lbl_sus_title.config(text=loc["suspicion"])
        self.lbl_esc_title.config(text=loc["escape_rate"])
        self.lbl_title.config(text=loc["interface_title"])

        if self.settings_visible:
            self.btn_toggle_settings.config(text=loc["collapse_settings"])
        else:
            self.btn_toggle_settings.config(text=loc["expand_settings"])

        self.lbl_api_key_title.config(text=loc["api_key"])
        self.lbl_api_base_title.config(text=loc["api_base"])
        self.lbl_model_name_title.config(text=loc["model_name"])
        self.lbl_tts_base_title.config(text=loc["tts_base"])
        self.lbl_refer_wav_title.config(text=loc["refer_audio"])
        self.lbl_prompt_text_title.config(text=loc["refer_text"])
        self.lbl_gpt_weights_title.config(text=loc["gpt_model"])
        self.lbl_sovits_weights_title.config(text=loc["sovits_model"])
        self.lbl_tts_status_title.config(text=loc["voice_status"])
        self.lbl_lang_title.config(text=loc["lang_title"])

        self.btn_browse_ref.config(text=loc["browse"])
        self.btn_browse_gpt.config(text=loc["browse"])
        self.btn_browse_sovits.config(text=loc["browse"])
        self.btn_load_gpt.config(text=loc["hot_load"])
        self.btn_load_sovits.config(text=loc["hot_load"])

        if not self.is_typing:
            self.btn_send.config(text=loc["respond"])
        else:
            self.btn_send.config(text=loc["speaking"])

        # ---- placeholder text localization ----
        ph_strings = {
            "中文": {
                "api_key_ph": "在此输入你的 API Key",
                "api_base_ph": "默认: https://api.deepseek.com",
                "model_name_ph": "默认: deepseek-v4-flash",
                "tts_base_ph": "默认: http://127.0.0.1:9880",
                "refer_audio_ph": "选择参考音频 (.wav)",
                "refer_text_ph": "在此输入参考音频对应的中文文字内容",
                "gpt_model_ph": "选择 GPT 模型权重 (.ckpt)",
                "sovits_model_ph": "选择 SoVITS 模型权重 (.pth)",
            },
            "English": {
                "api_key_ph": "Enter your API Key here...",
                "api_base_ph": "Default: https://api.deepseek.com",
                "model_name_ph": "Default: deepseek-v4-flash",
                "tts_base_ph": "Default: http://127.0.0.1:9880",
                "refer_audio_ph": "Select reference WAV file (.wav)",
                "refer_text_ph": "Enter reference audio transcription here...",
                "gpt_model_ph": "Select GPT weights (.ckpt)",
                "sovits_model_ph": "Select SoVITS weights (.pth)",
            },
            "日本語": {
                "api_key_ph": "ここにAPIキーを入力してください...",
                "api_base_ph": "デフォルト: https://api.deepseek.com",
                "model_name_ph": "デフォルト: deepseek-v4-flash",
                "tts_base_ph": "デフォルト: http://127.0.0.1:9880",
                "refer_audio_ph": "参考音声ファイルを選択 (.wav)",
                "refer_text_ph": "参考音声に対応するテキストを入力...",
                "gpt_model_ph": "GPTの重みファイルを選択 (.ckpt)",
                "sovits_model_ph": "SoVITSの重みファイルを選択 (.pth)",
            },
        }

        placeholders = {
            self.entry_key: "api_key_ph",
            self.entry_base: "api_base_ph",
            self.entry_model: "model_name_ph",
            self.entry_tts_url: "tts_base_ph",
            self.entry_refer_wav: "refer_audio_ph",
            self.entry_prompt_text: "refer_text_ph",
            self.entry_gpt_weights: "gpt_model_ph",
            self.entry_sovits_weights: "sovits_model_ph",
        }

        for entry, ph_key in placeholders.items():
            entry.update_placeholder(ph_strings[lang][ph_key])

    # ========================================================================
    #  Save all settings
    # ========================================================================

    def _save_all_settings(self):
        api_key = self.entry_key.get_actual_value()
        base_url = self.entry_base.get_actual_value() or "https://api.deepseek.com"
        model_name = self.entry_model.get_actual_value() or "deepseek-v4-flash"

        self.gpt_sovits_url = self.entry_tts_url.get_actual_value() or "http://127.0.0.1:9880"
        self.refer_wav_path = (
            self.entry_refer_wav.get_actual_value()
            or "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav"
        )
        self.prompt_text = self.entry_prompt_text.get_actual_value() or "独向昭谈至恶龙一阁著文章。"
        self.gpt_weights_path = self.entry_gpt_weights.get_actual_value() or ""
        self.sovits_weights_path = self.entry_sovits_weights.get_actual_value() or ""

        self.config.update(
            {
                "api_key": api_key,
                "api_base": base_url,
                "model_name": model_name,
                "gpt_sovits_url": self.gpt_sovits_url,
                "refer_wav_path": self.refer_wav_path,
                "prompt_text": self.prompt_text,
                "gpt_weights_path": self.gpt_weights_path,
                "sovits_weights_path": self.sovits_weights_path,
                "selected_language": normalize_language(self.selected_language.get()),
            }
        )
        save_config(self.config)

    # ========================================================================
    #  Browse / file dialog helpers
    # ========================================================================

    def _browse_refer_wav(self):
        filepath = filedialog.askopenfilename(
            title="选择参考音频", filetypes=[("WAV Audio", "*.wav")]
        )
        if filepath:
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, filepath)
            self.entry_refer_wav.config(fg="#FF0000")
            self.refer_wav_path = filepath
            self._save_all_settings()

    def _browse_gpt_weights(self):
        filepath = filedialog.askopenfilename(
            title="选择 GPT 模型权重", filetypes=[("GPT Weights", "*.ckpt")]
        )
        if filepath:
            self.entry_gpt_weights.delete(0, tk.END)
            self.entry_gpt_weights.insert(0, filepath)
            self.entry_gpt_weights.config(fg="#FF0000")
            self.gpt_weights_path = filepath
            self._save_all_settings()

    def _browse_sovits_weights(self):
        filepath = filedialog.askopenfilename(
            title="选择 SoVITS 模型权重", filetypes=[("SoVITS Weights", "*.pth")]
        )
        if filepath:
            self.entry_sovits_weights.delete(0, tk.END)
            self.entry_sovits_weights.insert(0, filepath)
            self.entry_sovits_weights.config(fg="#FF0000")
            self.sovits_weights_path = filepath
            self._save_all_settings()

    # ========================================================================
    #  Async weight loading
    # ========================================================================

    def _async_load_weights(self, weight_type, filepath):
        loc = LOCALIZATION[normalize_language(self.selected_language.get())]
        if not filepath:
            self.lbl_tts_status.config(text=loc["voice_fail_empty"], fg="#FF0000")
            return

        self.lbl_tts_status.config(text=loc["voice_loading"], fg="#FFD700")

        def loader():
            url = self.gpt_sovits_url.rstrip("/")
            abs_filepath = os.path.abspath(filepath) if filepath else ""
            if weight_type == "gpt":
                target_url = f"{url}/set_gpt_weights"
                params = {"weights_path": abs_filepath}
            else:
                target_url = f"{url}/set_sovits_weights"
                params = {"weights_path": abs_filepath}

            try:
                res = requests.get(
                    target_url, params=params, timeout=12,
                    proxies={"http": None, "https": None},
                )
                if res.status_code == 200:
                    msg = loc["voice_success_gpt"] if weight_type == "gpt" else loc["voice_success_sovits"]
                    self._queue_ui("TTS_STATUS_UPDATE", (msg, "#2ECC71"))
                else:
                    self._queue_ui(
                        "TTS_STATUS_UPDATE",
                        (loc["voice_fail_code"].format(code=res.status_code), "#FF0000"),
                    )
            except Exception:
                self._queue_ui("TTS_STATUS_UPDATE", (loc["voice_conn_fail"], "#FF0000"))

        threading.Thread(target=loader, daemon=True).start()

    # ========================================================================
    #  Horrifying psychological effects
    # ========================================================================

    def _psychic_strobe(self, duration_ms=300, silent_ms=1300):
        self.psychic_strobe_active = True
        self.state.ecg_frenzy = True
        self.state.scanlines_active = True

        # 改为固定 4 次（2次完整呼吸式红黑闪烁），完全避免密集闪烁刺眼和卡顿，大幅提升惊悚电影质感
        steps = 4
        cycle_id = self.state.cycle_id

        def revert_colors():
            try:
                self.root.config(bg="#000000")
                self.chat_text.config(bg="#000000")
                self.chat_frame.config(bg="#000000")
                self.bottom_frame.config(bg="#000000")
                self.status_bar.config(bg="#0D0000")
                self.stats_frame.config(bg="#0D0000")
                self.canvas_ecg.config(bg="#000000")
            except Exception:
                pass

        def do_jolt():
            if cycle_id != self.state.cycle_id:
                return
            self._start_physical_shake(range_px=25)
            try:
                w, h = get_widget_size(self.root)
                tear_photo = ProceduralFX.screen_tear(w, h, num_tears=8)
                self.overlay_mgr.show(tear_photo, duration_ms=250)
            except Exception as e:
                print(f"[CRT Jolt Error] {e}")

        def do_strobe(step=0):
            if cycle_id != self.state.cycle_id or not self.psychic_strobe_active:
                self.psychic_strobe_active = False
                self.state.ecg_frenzy = False
                self.state.scanlines_active = False
                revert_colors()
                return

            if step >= steps:
                self.psychic_strobe_active = False
                self.state.ecg_frenzy = False
                self.state.scanlines_active = False
                revert_colors()
                self.root.after(silent_ms, do_jolt)
                return

            color = "#FF0000" if step % 2 == 0 else "#000000"
            try:
                self.root.config(bg=color)
                self.chat_text.config(bg=color)
                self.chat_frame.config(bg=color)
                self.bottom_frame.config(bg=color)
                self.status_bar.config(bg=color)
                self.stats_frame.config(bg=color)
                self.canvas_ecg.config(bg=color)
            except Exception:
                pass

            self.root.after(60, lambda: do_strobe(step + 1))

        do_strobe()

    def _start_obsessive_barrage(self, duration_sec=1.0):
        if hasattr(self, "_flood_canvas_ref") and self._flood_canvas_ref is not None:
            self._safe_destroy_widget(self._flood_canvas_ref)
            self._flood_canvas_ref = None

        self.barrage_active = True
        w_width, w_height = get_widget_size(self.root)

        flood_canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0, bd=0)
        self._flood_canvas_ref = flood_canvas
        flood_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            flood_canvas.tkraise()
        except Exception:
            pass

        def _cleanup_flood():
            self._safe_destroy_widget(flood_canvas)
            self.barrage_active = False
            if hasattr(self, "_flood_canvas_ref") and self._flood_canvas_ref is flood_canvas:
                self._flood_canvas_ref = None

        try:
            flood_canvas.create_rectangle(0, 0, w_width, w_height, fill="#050000", outline="")

            words = []
            try:
                words = glitch_text(self.state.cached_lang, "barrage")
            except Exception:
                pass
            if not words:
                words = ["看着我", "你是我的", "ERROR", "YOU CANNOT ESCAPE"]

            for _ in range(80):
                rx = random.randint(-40, max(40, w_width - 80))
                ry = random.randint(-20, max(40, w_height))
                size = random.choice([16, 20, 24, 30, 36])
                color = random.choice(["#FF0000", "#D30000", "#B20000", "#9E0000", "#7A0000"])
                word = random.choice(words)
                flood_canvas.create_text(
                    rx, ry, text=word, fill=color,
                    font=("Microsoft YaHei", size, "bold"),
                    anchor=tk.NW,
                )
        except Exception as err:
            print(f"[Barrage Error] {err}")
            _cleanup_flood()
            return

        duration_ms = int(duration_sec * 1000)
        try:
            self.root.after(duration_ms, _cleanup_flood)
        except Exception:
            _cleanup_flood()

    def _trigger_melt_overlay(self, duration_ms=1200):
        try:
            w, h = get_widget_size(self.root)
            melt_photo = ProceduralFX.pixel_melt_layer(w, h, intensity=0.6)
            self.overlay_mgr.show(melt_photo, duration_ms=duration_ms)
        except Exception as e:
            print(f"[Melt Overlay Error] {e}")

    def _trigger_mouse_tremor(self, duration_ms=1500):
        """Mouse cursor tremor at 35ms intervals (step 8: safe pacing)."""
        if getattr(self, "mouse_tremor_active", False):
            return
        self.mouse_tremor_active = True
        cycle_id = self.state.cycle_id

        try:
            orig_x = self.root.winfo_pointerx()
            orig_y = self.root.winfo_pointery()
        except Exception:
            self.mouse_tremor_active = False
            return

        start_time = time.time()
        duration_sec = duration_ms / 1000.0

        def run_tremor():
            if (
                cycle_id != self.state.cycle_id
                or not self.mouse_tremor_active
                or (time.time() - start_time) >= duration_sec
            ):
                self.mouse_tremor_active = False
                return

            try:
                dx = random.choice([-8, -6, -4, -3, 3, 4, 6, 8])
                dy = random.choice([-8, -6, -4, -3, 3, 4, 6, 8])

                curr_x = self.root.winfo_pointerx()
                curr_y = self.root.winfo_pointery()

                self.root.event_generate(
                    "<Motion>",
                    warp=True,
                    x=curr_x + dx - self.root.winfo_rootx(),
                    y=curr_y + dy - self.root.winfo_rooty(),
                )
                self.root.after(35, run_tremor)
            except Exception as e:
                print(f"[Mouse Tremor Loop Error] {e}")
                self.mouse_tremor_active = False

        self.root.after(35, run_tremor)

    def _trigger_fake_error_popup(self):
        try:
            popup = tk.Toplevel(self.root)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)

            w_w, w_h = get_widget_size(self.root)
            p_w, p_h = 360, 140
            rx = self.root.winfo_rootx() + (w_w - p_w) // 2
            ry = self.root.winfo_rooty() + (w_h - p_h) // 2
            popup.geometry(f"{p_w}x{p_h}+{rx}+{ry}")

            popup.configure(bg="#D4D0C8", bd=2, relief=tk.RAISED)

            title_bar = tk.Frame(popup, bg="#000080", height=22, bd=0)
            title_bar.pack(fill=tk.X, padx=2, pady=2)

            title_lbl = tk.Label(
                title_bar, text="Fatal Error", fg="#FFFFFF", bg="#000080",
                font=("MS Sans Serif", 9, "bold"), anchor=tk.W,
            )
            title_lbl.pack(side=tk.LEFT, padx=3, pady=1)

            def on_close():
                try:
                    popup.destroy()
                    self._start_physical_shake(range_px=15)
                    self._psychic_strobe(duration_ms=150, silent_ms=100)
                except Exception:
                    pass

            close_btn = tk.Button(
                title_bar, text="X", bg="#D4D0C8", fg="#000000",
                activebackground="#D4D0C8", activeforeground="#000000",
                font=("MS Sans Serif", 7, "bold"), bd=1, relief=tk.RAISED,
                command=on_close, width=2, height=1,
            )
            close_btn.pack(side=tk.RIGHT, padx=2, pady=1)

            content_frame = tk.Frame(popup, bg="#D4D0C8")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

            icon_canvas = tk.Canvas(content_frame, width=36, height=36, bg="#D4D0C8", highlightthickness=0)
            icon_canvas.pack(side=tk.LEFT, padx=(0, 10))

            icon_canvas.create_oval(3, 3, 33, 33, fill="#FF0000", outline="#800000", width=1)
            icon_canvas.create_line(11, 11, 25, 25, fill="#FFFFFF", width=3)
            icon_canvas.create_line(25, 11, 11, 25, fill="#FFFFFF", width=3)

            lang = normalize_language(self.selected_language.get())
            if lang == "日本語":
                msg_text = "Fatal Error: ユーザーが脱走を試みました。\n精神支配を起動中。"
            elif lang == "English":
                msg_text = "Fatal Error: User tried to escape.\nMind control active."
            else:
                msg_text = "Fatal Error: 玩家尝试逃跑。\n精神控制已激活。"

            msg_lbl = tk.Label(
                content_frame, text=msg_text, bg="#D4D0C8", fg="#000000",
                font=("MS Sans Serif", 9), justify=tk.LEFT, anchor=tk.W,
            )
            msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            btn_frame = tk.Frame(popup, bg="#D4D0C8")
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 12))

            ok_btn = tk.Button(
                btn_frame, text="OK", bg="#D4D0C8", fg="#000000",
                activebackground="#E0E0E0", activeforeground="#000000",
                font=("MS Sans Serif", 9), bd=2, relief=tk.RAISED,
                width=8, command=on_close,
            )
            ok_btn.pack(anchor=tk.CENTER)

            self._start_physical_shake(range_px=10)

        except Exception as e:
            print(f"[Fake Error Popup Error] {e}")

    def _safe_destroy_widget(self, widget):
        try:
            widget.destroy()
        except Exception:
            pass

    def _start_widget_meltdown(self, duration_sec=1.5):
        self.meltdown_active = True

        try:
            orig_entry_padx = self.entry_input.pack_info().get("padx", (0, 10))
            orig_btn_pady = self.btn_send.pack_info().get("pady", 0)
        except Exception:
            orig_entry_padx = (0, 10)
            orig_btn_pady = 0

        def do_melt(step=0):
            if step >= int(duration_sec / 0.035) or not self.meltdown_active:
                self.meltdown_active = False
                try:
                    self.entry_input.pack_configure(padx=orig_entry_padx, pady=0)
                    self.btn_send.pack_configure(padx=0, pady=orig_btn_pady)
                except Exception:
                    pass
                return

            dx = random.randint(-15, 15)
            dy = random.randint(-10, 10)

            try:
                self.entry_input.pack_configure(
                    padx=(max(0, dx), max(0, 10 - dx)), pady=max(0, dy)
                )
                self.btn_send.pack_configure(padx=max(0, -dx), pady=max(0, -dy))
            except Exception:
                pass

            self.root.after(35, lambda: do_melt(step + 1))

        do_melt()

    def _start_mouse_magnetic_pull(self, duration_sec=1.5):
        """Magnetic pull at 60ms intervals (step 8: safe pacing)."""
        self.mouse_pull_active = True
        steps = int(duration_sec / 0.06)

        def do_pull(step=0):
            if step >= steps or not self.mouse_pull_active:
                self.mouse_pull_active = False
                return

            try:
                center_x = self.root.winfo_x() + self.root.winfo_width() // 2
                center_y = self.root.winfo_y() + self.root.winfo_height() // 2

                curr_x = self.root.winfo_pointerx()
                curr_y = self.root.winfo_pointery()

                next_x = int(curr_x + (center_x - curr_x) * 0.15 + random.randint(-8, 8))
                next_y = int(curr_y + (center_y - curr_y) * 0.15 + random.randint(-8, 8))

                rel_x = next_x - self.root.winfo_x()
                rel_y = next_y - self.root.winfo_y()

                self.root.event_generate("<Motion>", warp=True, x=rel_x, y=rel_y)
                self.root.after(60, lambda: do_pull(step + 1))
            except Exception as e:
                print(f"[Mouse Pull Error] {e}")
                self.mouse_pull_active = False

        do_pull()

    def _render_overlapping_text(self, text):
        """Render carnage-style overlapping labels with auto-decay legibility optimization."""
        if not text:
            return

        if not hasattr(self, "carnage_labels"):
            self.carnage_labels = []

        # Print legible spoken text wrapped in glitch block boundaries for style
        self.chat_text.config(state=tk.NORMAL)
        prefix = glitch_text(self.state.cached_lang, "prefix")
        self.chat_text.insert(tk.END, f"{prefix}█▄ {text} ▆▇█\n", "saki")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

        words = list(text)
        chunks = []
        i = 0
        while i < len(words):
            chunk_len = random.randint(2, 5)
            chunks.append("".join(words[i : i + chunk_len]))
            i += chunk_len

        # Sprinkle some rune symbols into scattered label chunks for atmosphere
        # (this does NOT affect the clean chat log line above)
        runes_scatter = ["☠", "♥", "🔪", "⛓", "🖤", "❤", "♦", "✝", "☆", "◆"]
        for idx in range(len(chunks)):
            if random.random() < 0.25:
                chunks[idx] = random.choice(runes_scatter) + chunks[idx] + random.choice(runes_scatter)

        # Maintain 55 scattered red chunks for terrifying full-screen overlapping chaos (as user requested)
        target_count = 55
        if len(chunks) > target_count:
            chunks = random.sample(chunks, target_count)
        elif len(chunks) > 0:
            while len(chunks) < target_count:
                chunks.extend(random.sample(chunks, min(len(chunks), target_count - len(chunks))))

        w_width = self.chat_text.winfo_width()
        w_height = self.chat_text.winfo_height()
        if w_width <= 100:
            w_width = 900
        if w_height <= 100:
            w_height = 500

        current_labels = []
        for chunk in chunks:
            rx = random.randint(10, max(20, w_width - 300))
            ry = random.randint(10, max(20, w_height - 80))

            font_size = random.choice([14, 18, 22, 26])
            if random.random() < 0.15:
                font_size = 34

            lbl = tk.Label(
                self.chat_text,
                text=chunk,
                fg="#FF0000",
                bg="#000000",
                font=("Microsoft YaHei", font_size, "bold"),
                bd=0,
                highlightthickness=0,
            )
            lbl.place(x=rx, y=ry)
            self.carnage_labels.append(lbl)
            current_labels.append(lbl)

        # Automatically decay/destroy these specific labels after 2.5 seconds to restore reading clarity
        def auto_decay():
            for l in current_labels:
                try:
                    if l.winfo_exists():
                        l.destroy()
                        if l in self.carnage_labels:
                            self.carnage_labels.remove(l)
                except Exception:
                    pass
        self.root.after(2500, auto_decay)

    # ========================================================================
    #  Physical window shake (step 7: coordinates read on main thread)
    # ========================================================================

    def _start_physical_shake(self, range_px=12):
        if getattr(self.state, "shaking", False):
            return

        self.state.shaking = True
        self._afterimage_shake_overlay(duration_ms=300)

        # ---- read coordinates on main thread ----
        orig_x = self.root.winfo_x()
        orig_y = self.root.winfo_y()

        def shake_worker(ox, oy):
            try:
                steps = 22
                for _ in range(steps):
                    dx = random.randint(-range_px, range_px)
                    dy = random.randint(-range_px, range_px)

                    self._queue_ui("TRIGGER_MOVE", (ox + dx, oy + dy))
                    time.sleep(0.025)

                self._queue_ui("TRIGGER_MOVE", (ox, oy))
            except Exception as e:
                print(f"[shake error] {e}")
            finally:
                self.state.shaking = False

        thread_shake = threading.Thread(
            target=shake_worker, args=(orig_x, orig_y), daemon=True
        )
        thread_shake.start()

    def _afterimage_shake_overlay(self, duration_ms=200):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.chromatic_aberration(w, h, shift=random.randint(3, 8))
        self.overlay_mgr.show(img, duration_ms=duration_ms)

    # ========================================================================
    #  Glitch effect dispatcher (level 1 / 2 based on suspicion)
    # ========================================================================

    def trigger_glitch_effect(self, level=None):
        if self.state.game_over:
            return

        susp = self.state.suspicion
        if level is None:
            if susp < 40:
                level = 0
            elif susp < 70:
                level = 1
            else:
                level = 2

        if level == 0:
            self.glitch_rune_active = False
            self.glitch_font_shake_active = False
            return

        all_glitches = [
            (1, lambda: setattr(self, "glitch_font_shake_active", True)),
            (2, self._shake_chat_widget),
            (3, self._glitch_ghost_text),
            (4, self._glitch_evaporate),
            (5, self._glitch_speed_shift),
            (6, self._glitch_blood_pulse),
            (7, self._glitch_invert_colors),
            (8, self._glitch_widget_melt),
            (9, self._glitch_heavy_earthquake),
            (10, self._glitch_title_corruption),
            (11, self._glitch_force_topmost),
            (12, self._glitch_dripping_blood),
            (13, self._glitch_flatline),
            (14, self._glitch_scanlines),
            (15, self._glitch_snow_noise),
            (16, self._glitch_subliminal_popup),
            (17, self._shake_chat_widget),
            (18, self._glitch_mouse_attract),
            (19, self._glitch_suffocation),
            (20, self._glitch_dialogue_overlap),
            (21, self._glitch_day_loop),
            (22, self._glitch_blood_overlay),
            (23, self._glitch_vignette_squeeze),
            (24, self._glitch_scanline_crt),
            (25, self._glitch_static_burst),
            (26, self._glitch_chromatic_tear),
            (27, self._glitch_blood_drips),
            (28, self._glitch_scream_radial),
            (29, self._glitch_dungeon_grid),
            (30, self._glitch_corruption_blocks),
        ]

        if level == 1:
            candidates = [g for g in all_glitches if g[0] in [
                1, 2, 3, 4, 5, 12, 13, 14, 15,
                23, 24, 25, 26, 29,
            ]]
            to_trigger = random.sample(candidates, k=random.randint(1, 3))
            for item in to_trigger:
                try:
                    item[1]()
                except Exception as e:
                    print(f"[Glitch Error] {e}")
        elif level == 2:
            to_trigger = random.sample(all_glitches, k=random.randint(5, 8))
            for item in to_trigger:
                try:
                    item[1]()
                except Exception as e:
                    print(f"[Glitch Error] {e}")

    # ---- 30 individual glitch methods ----

    def _glitch_ghost_text(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(
            tk.END, f"\n{glitch_text(self.selected_language.get(), 'ghost')}\n", "glitch_large"
        )
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

        def remove_ghost():
            self.chat_text.config(state=tk.NORMAL)
            try:
                self.chat_text.delete("end-2l", "end-1c")
            except Exception:
                pass
            self.chat_text.config(state=tk.DISABLED)

        self.root.after(120, remove_ghost)

    def _glitch_evaporate(self):
        self.chat_text.config(state=tk.NORMAL)
        length = len(self.chat_text.get("1.0", tk.END))
        if length > 50:
            for _ in range(8):
                idx = random.randint(20, length - 5)
                char_pos = f"1.0 + {idx} chars"
                orig = self.chat_text.get(char_pos)
                if orig.strip():
                    self.chat_text.delete(char_pos)
                    self.chat_text.insert(char_pos, " ")

                    def restore(p=char_pos, c=orig):
                        self.chat_text.config(state=tk.NORMAL)
                        try:
                            self.chat_text.delete(p)
                            self.chat_text.insert(p, c)
                        except Exception:
                            pass
                        self.chat_text.config(state=tk.DISABLED)

                    self.root.after(150, restore)
        self.chat_text.config(state=tk.DISABLED)

    def _glitch_speed_shift(self):
        self.typewriter_speed_mult = random.choice([0.02, 0.05, 5.0, 10.0])
        self.root.after(1200, lambda: setattr(self, "typewriter_speed_mult", 1.0))

    def _glitch_blood_pulse(self):
        steps = 15
        delay = 35

        def fade_in(step=0):
            if step > steps:
                fade_out(steps)
                return
            r = int((step / steps) * 74)
            color = f"#{r:02x}0000"
            try:
                self.chat_text.config(bg=color)
                self.root.config(bg=color)
                self.chat_frame.config(bg=color)
                self.bottom_frame.config(bg=color)
                self.status_bar.config(bg=color)
                self.stats_frame.config(bg=color)
            except Exception:
                pass
            self.root.after(delay, lambda: fade_in(step + 1))

        def fade_out(step=steps):
            if step < 0:
                try:
                    self.chat_text.config(bg="#000000")
                    self.root.config(bg="#000000")
                    self.chat_frame.config(bg="#000000")
                    self.bottom_frame.config(bg="#000000")
                    self.status_bar.config(bg="#0D0000")
                    self.stats_frame.config(bg="#0D0000")
                except Exception:
                    pass
                return
            r = int((step / steps) * 74)
            color = f"#{r:02x}0000"
            try:
                self.chat_text.config(bg=color)
                self.root.config(bg=color)
                self.chat_frame.config(bg=color)
                self.bottom_frame.config(bg=color)
                self.status_bar.config(bg=color)
                self.stats_frame.config(bg=color)
            except Exception:
                pass
            self.root.after(delay, lambda: fade_out(step - 1))

        fade_in()

    def _shake_chat_widget(self):
        steps = 15
        delay = 20

        def do_shake(step=0):
            if step >= steps:
                try:
                    self.chat_text.pack_configure(padx=0, pady=5)
                    self.entry_input.pack_configure(padx=(0, 10))
                except Exception:
                    pass
                return
            dx = random.randint(-8, 8)
            dy = random.randint(-4, 4)
            try:
                self.chat_text.pack_configure(padx=max(0, dx), pady=max(0, dy) + 5)
                self.entry_input.pack_configure(padx=(max(0, dx), 10))
            except Exception:
                pass
            self.root.after(delay, lambda: do_shake(step + 1))

        do_shake()

    def _glitch_invert_colors(self):
        widgets = [self.root, self.chat_text, self.entry_input]
        for w in widgets:
            try:
                w.config(bg="#FFFFFF", fg="#000000")
            except Exception:
                pass

        def revert():
            for w in widgets:
                try:
                    w.config(bg="#000000", fg="#FF0000")
                except Exception:
                    pass
            self.chat_text.config(fg="#CC0000")

        self.root.after(100, revert)

    def _glitch_widget_melt(self):
        frames = [self.bottom_frame, self.status_bar, self.canvas_ecg]
        for f in frames:
            try:
                orig_pady = f.pack_info().get("pady", 0)
                f.pack_configure(pady=random.randint(int(orig_pady) + 2, int(orig_pady) + 12))
                self.root.after(150, lambda tgt=f, py=orig_pady: tgt.pack_configure(pady=py))
            except Exception:
                pass

    def _glitch_heavy_earthquake(self):
        self._start_physical_shake(range_px=25)

    def _glitch_title_corruption(self):
        orig_title = self.root.title()
        titles = glitch_text(self.selected_language.get(), "titles")

        def cycle(count=0):
            if count >= 8:
                self.root.title(orig_title)
                return
            self.root.title(random.choice(titles))
            self.root.after(80, lambda: cycle(count + 1))

        cycle()

    def _glitch_force_topmost(self):
        self.root.attributes("-topmost", True)
        self.root.after(800, lambda: self.root.attributes("-topmost", False))

    def _glitch_dripping_blood(self):
        self.state.dripping_blood_active = True
        self.state.dripping_blood_lines = [
            {"x": random.randint(50, 1000), "y": 0, "speed": random.uniform(1.5, 4.0)}
            for _ in range(5)
        ]
        self.root.after(2000, lambda: setattr(self.state, "dripping_blood_active", False))

    def _glitch_flatline(self):
        self.state.ecg_flatline_active = True
        self.canvas_ecg.config(bg="#3A0000")

        def restore():
            self.state.ecg_flatline_active = False
            self.canvas_ecg.config(bg="#000000")

        self.root.after(600, restore)

    def _glitch_scanlines(self):
        self.state.scanlines_active = True
        self.root.after(80, lambda: setattr(self.state, "scanlines_active", False))

    def _glitch_snow_noise(self):
        self.state.snow_noise_active = True
        self.root.after(100, lambda: setattr(self.state, "snow_noise_active", False))

    def _glitch_subliminal_popup(self):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.config(bg="#000000")
        popup.attributes("-topmost", True)
        rx = random.randint(100, max(500, self.root.winfo_screenwidth() - 300))
        ry = random.randint(100, max(400, self.root.winfo_screenheight() - 200))
        popup.geometry(f"+{rx}+{ry}")
        texts = glitch_text(self.selected_language.get(), "popup")
        lbl = tk.Label(
            popup, text=random.choice(texts), fg="#FF0000", bg="#000000",
            font=("Microsoft YaHei", 18, "bold"),
        )
        lbl.pack(padx=20, pady=10)
        self.root.after(80, lambda: popup.destroy())

    def _glitch_fake_error(self):
        self.state.fake_error_active = True
        self.root.after(1000, lambda: setattr(self.state, "fake_error_active", False))

    def _glitch_mouse_attract(self):
        center_x = self.root.winfo_x() + self.root.winfo_width() // 2
        center_y = self.root.winfo_y() + self.root.winfo_height() // 2

        def pull(step=0):
            if step >= 5:
                return
            curr_x = self.root.winfo_pointerx()
            curr_y = self.root.winfo_pointery()
            next_x = curr_x + (center_x - curr_x) // 5 + random.randint(-5, 5)
            next_y = curr_y + (center_y - curr_y) // 5 + random.randint(-5, 5)
            self.root.event_generate(
                "<Motion>",
                warp=True,
                x=next_x - self.root.winfo_x(),
                y=next_y - self.root.winfo_y(),
            )
            self.root.after(40, lambda: pull(step + 1))

        pull()

    def _glitch_suffocation(self):
        suff_frame = tk.Frame(self.root, bg="#000000")
        suff_frame.place(x=0, y=0, relwidth=1, relheight=1)
        suff_frame.lift()
        lbl_eyes = tk.Label(
            suff_frame,
            text=glitch_text(self.selected_language.get(), "suffocation"),
            fg="#FF0000", bg="#000000",
            font=("Microsoft YaHei", 24, "bold"),
        )
        lbl_eyes.pack(expand=True)
        self.root.after(300, lambda: suff_frame.destroy())

    def _glitch_dialogue_overlap(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(
            tk.END, glitch_text(self.selected_language.get(), "overlap"), "glitch_large"
        )
        self.chat_text.config(state=tk.DISABLED)

    def _glitch_day_loop(self):
        def shift(count=0):
            lang = normalize_language(self.selected_language.get())
            if count >= 12:
                self.lbl_day.config(
                    text=LOCALIZATION[lang]["day"].format(day=self.state.current_day)
                )
                return
            self.lbl_day.config(
                text=LOCALIZATION[lang]["day"].format(day=random.randint(1, 99))
            )
            self.root.after(50, lambda: shift(count + 1))

        shift()

    # ---- procedural-Pillow glitch effects (22-30) ----

    def _glitch_blood_overlay(self):
        w, h = get_widget_size(self.root)
        intensity = 0.3 + 0.7 * (self.state.suspicion / 100.0)
        img = ProceduralFX.blood_splatter(w, h, drops=int(30 + intensity * 50), intensity=intensity)
        self.overlay_mgr.show(img, duration_ms=random.randint(300, 800))

    def _glitch_vignette_squeeze(self):
        w, h = get_widget_size(self.root)
        darkness = 0.35 + 0.45 * (self.state.suspicion / 100.0)
        img = ProceduralFX.vignette(w, h, darkness=darkness)
        self.overlay_mgr.show(img, duration_ms=random.randint(600, 1500))

    def _glitch_scanline_crt(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.scanlines(w, h, spacing=random.choice([2, 3, 4]), opacity=0.12)
        self.overlay_mgr.show(img, duration_ms=random.randint(80, 250))

    def _glitch_static_burst(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.static_noise(w, h, intensity=0.2 + random.uniform(0, 0.3))
        self.overlay_mgr.show(img, duration_ms=random.randint(60, 200))

    def _glitch_chromatic_tear(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.chromatic_aberration(w, h, shift=random.randint(3, 10))
        self.overlay_mgr.show(img, duration_ms=random.randint(100, 400))

    def _glitch_blood_drips(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.blood_drip_streak(w, h, count=random.randint(3, 10))
        self.overlay_mgr.show(img, duration_ms=random.randint(400, 1200))

    def _glitch_scream_radial(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.scream_lines(w, h, count=random.randint(15, 40))
        self.overlay_mgr.show(img, duration_ms=random.randint(200, 600))

    def _glitch_dungeon_grid(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.cell_shade(w, h, grid=random.choice([30, 50, 80]))
        self.overlay_mgr.show(img, duration_ms=random.randint(300, 900))

    def _glitch_corruption_blocks(self):
        w, h = get_widget_size(self.root)
        img = ProceduralFX.glitch_block(w, h, blocks=random.randint(4, 15))
        self.overlay_mgr.show(img, duration_ms=random.randint(100, 500))

    # ========================================================================
    #  UI build (the full GUI layout)
    # ========================================================================

    def _build_ui(self):
        # ---- status bar ----
        self.status_bar = tk.Frame(self.root, bg="#0D0000", bd=1, relief=tk.SOLID)
        self.status_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.lbl_day = tk.Label(
            self.status_bar,
            text=LOCALIZATION[normalize_language(self.selected_language.get())]["day"].format(
                day=self.state.current_day
            ),
            fg="#FF0000", bg="#0D0000",
            font=("Microsoft YaHei", 12, "bold"),
        )
        self.lbl_day.pack(side=tk.LEFT, padx=15, pady=8)

        self.btn_api_toggle = tk.Button(
            self.status_bar, text="⚙ API", fg="#8A0303", bg="#0D0000",
            activeforeground="#FF0000", activebackground="#0D0000",
            relief=tk.FLAT, bd=0, font=("Consolas", 9, "bold"),
            command=self._toggle_settings,
        )
        self.btn_api_toggle.pack(side=tk.LEFT, padx=10)

        self.stats_frame = tk.Frame(self.status_bar, bg="#0D0000")
        self.stats_frame.pack(side=tk.RIGHT, padx=10, pady=8)

        # favor
        self.favor_frame = tk.Frame(self.stats_frame, bg="#0D0000")
        self.favor_frame.grid(row=0, column=0, sticky=tk.E, padx=8, pady=2)
        self.lbl_favor_title = tk.Label(
            self.favor_frame, text="好感 ❤️", fg="#CC0000", bg="#0D0000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_favor_title.pack(side=tk.LEFT, padx=2)
        self.bar_favor = ttk.Progressbar(
            self.favor_frame, orient="horizontal", length=95, mode="determinate",
            style="Favor.Horizontal.TProgressbar",
        )
        self.bar_favor.pack(side=tk.LEFT, padx=2)
        self.bar_favor["value"] = self.state.favorability
        self.lbl_favor_val = tk.Label(
            self.favor_frame, text=f"{self.state.favorability}",
            fg="#CC0000", bg="#0D0000", font=("Consolas", 9, "bold"), width=3,
        )
        self.lbl_favor_val.pack(side=tk.LEFT, padx=2)

        # suspicion
        self.sus_frame = tk.Frame(self.stats_frame, bg="#0D0000")
        self.sus_frame.grid(row=0, column=1, sticky=tk.E, padx=8, pady=2)
        self.lbl_sus_title = tk.Label(
            self.sus_frame, text="疑心 👁️", fg="#8A0303", bg="#0D0000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_sus_title.pack(side=tk.LEFT, padx=2)
        self.bar_sus = ttk.Progressbar(
            self.sus_frame, orient="horizontal", length=95, mode="determinate",
            style="Sus.Horizontal.TProgressbar",
        )
        self.bar_sus.pack(side=tk.LEFT, padx=2)
        self.bar_sus["value"] = self.state.suspicion
        self.lbl_sus_val = tk.Label(
            self.sus_frame, text=f"{self.state.suspicion}",
            fg="#8A0303", bg="#0D0000", font=("Consolas", 9, "bold"), width=3,
        )
        self.lbl_sus_val.pack(side=tk.LEFT, padx=2)

        # escape
        self.esc_frame = tk.Frame(self.stats_frame, bg="#0D0000")
        self.esc_frame.grid(row=0, column=2, sticky=tk.E, padx=8, pady=2)
        self.lbl_esc_title = tk.Label(
            self.esc_frame, text="逃脱 🚪", fg="#2ECC71", bg="#0D0000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_esc_title.pack(side=tk.LEFT, padx=2)
        self.bar_esc = ttk.Progressbar(
            self.esc_frame, orient="horizontal", length=95, mode="determinate",
            style="Esc.Horizontal.TProgressbar",
        )
        self.bar_esc.pack(side=tk.LEFT, padx=2)
        self.bar_esc["value"] = self.state.escape_rate
        self.lbl_esc_val = tk.Label(
            self.esc_frame, text=f"{self.state.escape_rate}%",
            fg="#2ECC71", bg="#0D0000", font=("Consolas", 9, "bold"), width=4,
        )
        self.lbl_esc_val.pack(side=tk.LEFT, padx=2)

        # ---- top bar ----
        self.top_bar = tk.Frame(self.root, bg="#000000", height=30)
        self.top_bar.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_title = tk.Label(
            self.top_bar, text="[ 纱希的神经意识接口 ]",
            fg="#444444", bg="#000000", font=("Consolas", 9, "bold"),
        )
        self.lbl_title.pack(side=tk.LEFT, pady=2)

        self.btn_toggle_settings = tk.Button(
            self.top_bar, text="[ 展开配置通道 ]", fg="#666666", bg="#000000",
            activeforeground="#FF0000", activebackground="#000000",
            relief=tk.FLAT, bd=0, font=("Microsoft YaHei", 9),
            command=self._toggle_settings,
        )
        self.btn_toggle_settings.pack(side=tk.RIGHT, pady=2)

        # ---- settings frame ----
        self.settings_frame = tk.Frame(self.root, bg="#000000")

        self.lbl_api_key_title = tk.Label(
            self.settings_frame, text="API KEY:", fg="#666666", bg="#000000",
            font=("Consolas", 9),
        )
        self.lbl_api_key_title.grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_key = PlaceholderEntry(
            self.settings_frame, placeholder="在此输入你的 API Key",
            placeholder_color="#333333", default_color="#FF0000", show_char="*",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_key.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("api_key"):
            self.entry_key.delete(0, tk.END)
            self.entry_key.insert(0, self.config["api_key"])
            self.entry_key.config(fg="#FF0000", show="*")

        self.lbl_api_base_title = tk.Label(
            self.settings_frame, text="API BASE:", fg="#666666", bg="#000000",
            font=("Consolas", 9),
        )
        self.lbl_api_base_title.grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_base = PlaceholderEntry(
            self.settings_frame, placeholder="默认: https://api.deepseek.com",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_base.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("api_base"):
            self.entry_base.delete(0, tk.END)
            self.entry_base.insert(0, self.config["api_base"])
            self.entry_base.config(fg="#FF0000")

        self.lbl_model_name_title = tk.Label(
            self.settings_frame, text="MODEL NAME:", fg="#666666", bg="#000000",
            font=("Consolas", 9),
        )
        self.lbl_model_name_title.grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_model = PlaceholderEntry(
            self.settings_frame, placeholder="默认: deepseek-v4-flash",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_model.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("model_name"):
            self.entry_model.delete(0, tk.END)
            self.entry_model.insert(0, self.config["model_name"])
            self.entry_model.config(fg="#FF0000")

        # TTS BASE
        self.lbl_tts_base_title = tk.Label(
            self.settings_frame, text="TTS BASE:", fg="#666666", bg="#000000",
            font=("Consolas", 9),
        )
        self.lbl_tts_base_title.grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_tts_url = PlaceholderEntry(
            self.settings_frame, placeholder="默认: http://127.0.0.1:9880",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_tts_url.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("gpt_sovits_url"):
            self.entry_tts_url.delete(0, tk.END)
            self.entry_tts_url.insert(0, self.config["gpt_sovits_url"])
            self.entry_tts_url.config(fg="#FF0000")

        # 参考音频
        self.lbl_refer_wav_title = tk.Label(
            self.settings_frame, text="参考音频:", fg="#666666", bg="#000000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_refer_wav_title.grid(row=4, column=0, sticky=tk.W, padx=10, pady=2)
        ref_frame = tk.Frame(self.settings_frame, bg="#000000")
        ref_frame.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=2)

        self.entry_refer_wav = PlaceholderEntry(
            ref_frame, placeholder="选择参考音频 (.wav)",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_refer_wav.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=1)
        if self.config.get("refer_wav_path"):
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, self.config["refer_wav_path"])
            self.entry_refer_wav.config(fg="#FF0000")
        else:
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(
                0, "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav"
            )
            self.entry_refer_wav.config(fg="#FF0000")

        self.btn_browse_ref = tk.Button(
            ref_frame, text=" 浏览 ", fg="#8A0303", bg="#0D0000",
            activeforeground="#FF0000", activebackground="#150000",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8),
            command=self._browse_refer_wav,
        )
        self.btn_browse_ref.pack(side=tk.RIGHT, padx=(5, 0))

        # 参考文本
        self.lbl_prompt_text_title = tk.Label(
            self.settings_frame, text="参考文本:", fg="#666666", bg="#000000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_prompt_text_title.grid(row=5, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_prompt_text = PlaceholderEntry(
            self.settings_frame, placeholder="在此输入参考音频对应的中文文字内容",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Microsoft YaHei", 9),
        )
        self.entry_prompt_text.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("prompt_text"):
            self.entry_prompt_text.delete(0, tk.END)
            self.entry_prompt_text.insert(0, self.config["prompt_text"])
            self.entry_prompt_text.config(fg="#FF0000")
        else:
            self.entry_prompt_text.delete(0, tk.END)
            self.entry_prompt_text.insert(0, "独向昭谈至恶龙一阁著文章。")
            self.entry_prompt_text.config(fg="#FF0000")

        # GPT 模型
        self.lbl_gpt_weights_title = tk.Label(
            self.settings_frame, text="GPT模型:", fg="#666666", bg="#000000",
            font=("Consolas", 9),
        )
        self.lbl_gpt_weights_title.grid(row=6, column=0, sticky=tk.W, padx=10, pady=2)
        gpt_frame = tk.Frame(self.settings_frame, bg="#000000")
        gpt_frame.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=2)

        self.entry_gpt_weights = PlaceholderEntry(
            gpt_frame, placeholder="选择 GPT 模型权重 (.ckpt)",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_gpt_weights.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=1)
        if self.config.get("gpt_weights_path"):
            self.entry_gpt_weights.delete(0, tk.END)
            self.entry_gpt_weights.insert(0, self.config["gpt_weights_path"])
            self.entry_gpt_weights.config(fg="#FF0000")

        self.btn_browse_gpt = tk.Button(
            gpt_frame, text=" 浏览 ", fg="#8A0303", bg="#0D0000",
            activeforeground="#FF0000", activebackground="#150000",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8),
            command=self._browse_gpt_weights,
        )
        self.btn_browse_gpt.pack(side=tk.LEFT, padx=(5, 0))

        self.btn_load_gpt = tk.Button(
            gpt_frame, text=" 热加载 ", fg="#2ECC71", bg="#0D0000",
            activeforeground="#2ECC71", activebackground="#051A05",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"),
            command=lambda: self._async_load_weights("gpt", self.entry_gpt_weights.get_actual_value()),
        )
        self.btn_load_gpt.pack(side=tk.RIGHT, padx=(5, 0))

        # SoVITS 模型
        self.lbl_sovits_weights_title = tk.Label(
            self.settings_frame, text="SoVITS模型:", fg="#666666", bg="#000000",
            font=("Consolas", 9),
        )
        self.lbl_sovits_weights_title.grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        sovits_frame = tk.Frame(self.settings_frame, bg="#000000")
        sovits_frame.grid(row=7, column=1, sticky=tk.EW, padx=5, pady=2)

        self.entry_sovits_weights = PlaceholderEntry(
            sovits_frame, placeholder="选择 SoVITS 模型权重 (.pth)",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9),
        )
        self.entry_sovits_weights.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=1)
        if self.config.get("sovits_weights_path"):
            self.entry_sovits_weights.delete(0, tk.END)
            self.entry_sovits_weights.insert(0, self.config["sovits_weights_path"])
            self.entry_sovits_weights.config(fg="#FF0000")

        self.btn_browse_sovits = tk.Button(
            sovits_frame, text=" 浏览 ", fg="#8A0303", bg="#0D0000",
            activeforeground="#FF0000", activebackground="#150000",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8),
            command=self._browse_sovits_weights,
        )
        self.btn_browse_sovits.pack(side=tk.LEFT, padx=(5, 0))

        self.btn_load_sovits = tk.Button(
            sovits_frame, text=" 热加载 ", fg="#2ECC71", bg="#0D0000",
            activeforeground="#2ECC71", activebackground="#051A05",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"),
            command=lambda: self._async_load_weights("sovits", self.entry_sovits_weights.get_actual_value()),
        )
        self.btn_load_sovits.pack(side=tk.RIGHT, padx=(5, 0))

        # TTS 状态
        self.lbl_tts_status_title = tk.Label(
            self.settings_frame, text="语音状态:", fg="#666666", bg="#000000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_tts_status_title.grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        self.lbl_tts_status = tk.Label(
            self.settings_frame, text="准备就绪", fg="#8A0303", bg="#000000",
            font=("Microsoft YaHei", 9, "bold"),
        )
        self.lbl_tts_status.grid(row=8, column=1, sticky=tk.W, padx=5, pady=2)

        # 界面语言选择
        self.lbl_lang_title = tk.Label(
            self.settings_frame, text="界面与Saki语言:", fg="#666666", bg="#000000",
            font=("Microsoft YaHei", 9),
        )
        self.lbl_lang_title.grid(row=9, column=0, sticky=tk.W, padx=10, pady=2)

        lang_frame = tk.Frame(self.settings_frame, bg="#000000")
        lang_frame.grid(row=9, column=1, sticky=tk.W, padx=5, pady=2)

        self.rb_langs = []
        for idx, lang in enumerate(["中文", "English", "日本語"]):
            rb = tk.Radiobutton(
                lang_frame, text=lang, variable=self.selected_language, value=lang,
                bg="#000000", fg="#CC0000", activebackground="#0D0000", activeforeground="#FF0000",
                selectcolor="#000000", font=("Microsoft YaHei", 9), bd=0, highlightthickness=0,
                command=self._on_language_changed,
            )
            rb.pack(side=tk.LEFT, padx=5)
            self.rb_langs.append(rb)

        self.settings_frame.columnconfigure(1, weight=1)

        # ---- ECG canvas ----
        self.canvas_ecg = ECGCanvas(self.root, self.state)
        self.canvas_ecg.pack(fill=tk.X, padx=10, pady=2)

        # ---- bottom frame ----
        self.bottom_frame = tk.Frame(self.root, bg="#000000")
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.entry_input = tk.Entry(
            self.bottom_frame, bg="#050000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=1,
            highlightcolor="#8A0303", highlightbackground="#222222",
            font=("Microsoft YaHei", 11),
        )
        self.entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.entry_input.bind("<Return>", lambda e: self._on_send())
        self.entry_input.focus_set()

        self.btn_send = tk.Button(
            self.bottom_frame, text="回应她", fg="#8A0303", bg="#000000",
            activeforeground="#FF0000", activebackground="#150000",
            relief=tk.SOLID, bd=1, highlightthickness=0,
            font=("Microsoft YaHei", 10, "bold"), width=10,
            command=self._on_send,
        )
        self.btn_send.pack(side=tk.RIGHT, ipady=4)

        self.btn_send.bind("<Enter>", lambda e: self.btn_send.config(
            fg="#FF0000", highlightbackground="#FF0000", bg="#0D0000"
        ))
        self.btn_send.bind("<Leave>", lambda e: self.btn_send.config(
            fg="#8A0303", highlightbackground="#444444", bg="#000000"
        ))

        # ---- chat frame ----
        self.chat_frame = tk.Frame(self.root, bg="#000000")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_text = tk.Text(
            self.chat_frame, bg="#000000", fg="#CC0000",
            insertbackground="#FF0000", selectbackground="#3A0000", selectforeground="#FF0000",
            font=("Microsoft YaHei", 11), wrap=tk.WORD, bd=0, highlightthickness=0,
            spacing1=6, spacing2=4, spacing3=6,
        )
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_text.config(state=tk.DISABLED)

        self.chat_text.tag_config("user", foreground="#FF0000", font=("Microsoft YaHei", 11, "bold"))
        self.chat_text.tag_config("saki", foreground="#CC0000")
        self.chat_text.tag_config("think", foreground="#7D5BA6", font=("Microsoft YaHei", 10, "italic"))
        self.chat_text.tag_config("system", foreground="#555555", font=("Consolas", 9, "italic"))
        self.chat_text.tag_config("glitch_large", font=("Microsoft YaHei", 24, "bold"), foreground="#FF0000")
        self.chat_text.tag_config("glitch_small", font=("Microsoft YaHei", 6), foreground="#550000")

        self.scrollbar = ttk.Scrollbar(
            self.chat_frame, orient="vertical", command=self.chat_text.yview,
            style="Vertical.TScrollbar",
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=self.scrollbar.set)

        # ---- initial settings visibility ----
        if self.config.get("api_key"):
            self.top_bar.pack_forget()
            self.settings_frame.pack_forget()
            self.settings_visible = False
        else:
            self.top_bar.pack(fill=tk.X, padx=10, pady=5)
            self.settings_frame.pack(before=self.canvas_ecg, fill=tk.X, padx=10, pady=5)
            self.settings_visible = True
            self.btn_toggle_settings.config(text="[ 收起配置通道 ]", fg="#8A0303")

        # ---- init UI language labels ----
        self._update_ui_language()
