# -*- coding: utf-8 -*-
"""
================================================================================
                    纱希 (Saki) - 文字冒险 RPG 与多结局系统 (终极版)
================================================================================
依赖安装说明：
    pip install pygame requests

启动说明：
    直接运行本 Python 文件：python yandere_game.py
    若同级目录下不存在 heartbeat.wav 或 heartbeat.mp3，程序在首次运行时会自动利用 Python
    内置 wave 库在同级目录下合成并输出一个高品质的诡异低频心跳音效文件 (heartbeat.wav)。

================================================================================
"""

import os
import sys
import time
import math
import wave
import struct
import random
import queue
import re
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from visual_fx import (
    ProceduralFX, ParticleEngine, OverlayManager, get_widget_size
)

# 尝试导入可选的第三方库，若缺失则优雅降级
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

# ================================================================================
#                        GPT-SoVITS 语音合成服务配置参数
# ================================================================================
GPT_SOVITS_URL = "http://127.0.0.1:9880"
REFER_WAV_PATH = "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav"     # 参考音频绝对路径
PROMPT_TEXT = "独向昭谈至恶龙一阁著文章。"              # 参考音频对应的提示词文本

# GPT-SoVITS 高质量朗读档：偏稳定、少随机、略慢速，适合病娇角色台词。
# 不同版本的 GPT-SoVITS API 对额外参数兼容性不同，请求失败时会自动降级为基础参数重试。
TTS_QUALITY_PARAMS = {
    "top_k": 20,
    "top_p": 0.85,
    "temperature": 0.65,
    "repetition_penalty": 1.25,
    "speed_factor": 0.95,
    "batch_size": 1,
    "batch_threshold": 0.75,
    "split_bucket": True,
    "streaming_mode": False,
    "parallel_infer": False,
    "media_type": "wav",
    "sample_steps": 32,
    "super_sampling": False,
}

# ================================================================================
#                        API Key 配置文件读写持久化模块
# ================================================================================
CONFIG_FILE = "yandere_config.json"

def load_config():
    """从本地读取 API 配置信息"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[配置加载异常] {e}")
    return {}

def save_config(config_dict):
    """保存配置信息到本地，下次启动自动读取"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[配置保存异常] {e}")

def clean_text_for_tts(text):
    """清理语音合成文本，彻底移出括号及括号内的动作独白，移除非文字表情符号"""
    if not text:
        return ""
    text = re.sub(r'\|\|.*?\|\|', '', text, flags=re.S)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S | re.I)
    # 彻底移去任意中英文括号、中英文括号混用及其中的动作描述，支持无限嵌套
    old_text = ""
    while old_text != text:
        old_text = text
        text = re.sub(r'[\(（][^\(\)（）]*[\)）]', '', text)
        text = re.sub(r'[\[【][^\[\]【】]*[\]】]', '', text)
        text = re.sub(r'\{[^\{\}]*\}', '', text)
        text = re.sub(r'\*[^*]*\*', '', text)
    
    # 仅保留中英文字符、数字和常用中文标点，移除非文字表情符号
    text = re.sub(r'[^\w\s\u4e00-\u9fa5，。！？、…；：""‘’\-]', '', text)
    
    # 【自愈优化】如果清洗后的文本不包含任何汉字、日文字符、英文字母或数字，则直接视为空，不发起语音合成以避免 400 Bad Request 错误
    if not re.search(r'[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ffa-zA-Z0-9]', text):
        return ""
        
    return text.strip()

def language_to_tts_code(lang):
    lang = normalize_language(lang) if "normalize_language" in globals() else lang
    if lang == "English":
        return "en"
    if lang == "日本語":
        return "ja"
    return "zh"

def build_tts_request_params(ref_wav_path, prompt_text, prompt_lang_code, text, target_lang_code, quality=True):
    params = {
        "refer_wav_path": ref_wav_path,
        "ref_audio_path": ref_wav_path,
        "prompt_text": prompt_text,
        "prompt_language": prompt_lang_code,
        "prompt_lang": prompt_lang_code,
        "text": text,
        "text_language": target_lang_code,
        "text_lang": target_lang_code,
    }
    if quality:
        params.update(TTS_QUALITY_PARAMS)
        if target_lang_code == "en":
            params["text_split_method"] = "cut4"
        else:
            params["text_split_method"] = "cut5"
    return params

# ================================================================================
#                             语言系统检测与本地化模块
# ================================================================================
def detect_language(text, default_lang="中文"):
    if not text:
        return default_lang
    # 清除数字、空白字符、特殊符号与标点，仅保留核心字词来判定语言
    cleaned = re.sub(r'[\d\s\W_]', '', text)
    if not cleaned:
        return default_lang
        
    # 检测日文假名
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', cleaned):
        return "日本語"
    # 检测中文汉字
    if re.search(r'[\u4e00-\u9fa5]', cleaned):
        return "中文"
    # 检测英文字母
    if re.search(r'[a-zA-Z]', cleaned):
        return "English"
    return default_lang

# ================================================================================
#                       专业角色模拟语言系统与输出协议
# ================================================================================
SUPPORTED_LANGUAGES = ("中文", "English", "日本語")

LANGUAGE_PROFILES = {
    "中文": {
        "formal_name": "简体中文",
        "script_rule": "只能使用自然、口语化的简体中文。不要夹杂英文整句、日语假名或机器翻译腔。",
        "think_rule": "内心独白也必须使用简体中文，允许短句、停顿和情绪断裂，但不要堆砌重复词。",
        "same_language_rule": "玩家也在使用中文，不要追加括号翻译。",
        "translation_rule": (
            "玩家正在使用【{user_lang}】。正式回复必须先用简体中文完成；"
            "然后必须在 JSON 之前另起一行，用一对全角括号 `（ ）` 放入完整的【{user_lang}】译文。"
            "这是强制可读性协议，不是可选项。不要添加\"翻译:\"或\"Translation:\"前缀。"
        ),
        "reply_limit": "正式台词控制在 80 到 140 个中文字符，除非正在触发结局。",
        "fallback_suffix": "||{{\"favorability\": {delta_f}, \"suspicion\": {delta_s}, \"escape_rate\": {delta_e}, \"game_over\": false}}||",
    },
    "English": {
        "formal_name": "English",
        "script_rule": "Use natural spoken English only. Do not include Chinese characters or Japanese kana in the in-character response.",
        "think_rule": "The inner monologue must also be written in English, with short, emotionally unstable but readable sentences.",
        "same_language_rule": "The player is using English. Do not add a parenthetical translation.",
        "translation_rule": (
            "The player is using [{user_lang}]. Write the in-character response in English first; "
            "then you MUST add one final human-readable line before the JSON, wrapped in full-width parentheses `（ ）`, "
            "containing a complete [{user_lang}] translation. This is mandatory, not optional. Do not add labels such as 'Translation:'."
        ),
        "reply_limit": "Keep spoken dialogue within 2 to 4 short sentences unless an ending is triggered.",
        "fallback_suffix": "||{{\"favorability\": {delta_f}, \"suspicion\": {delta_s}, \"escape_rate\": {delta_e}, \"game_over\": false}}||",
    },
    "日本語": {
        "formal_name": "日本語",
        "script_rule": "自然な日本語だけで返答すること。中国語の文章や英語の文を混ぜないこと。",
        "think_rule": "内心独白も日本語で書き、短く揺れる文体にすること。機械翻訳のような硬い表現は避けること。",
        "same_language_rule": "相手も日本語を使っています。末尾の括弧翻訳は不要です。",
        "translation_rule": (
            "相手は【{user_lang}】で話しています。まず日本語で返答し、その後 JSON の直前に必ず改行して、"
            "全角括弧 `（ ）` の中に完全な【{user_lang}】訳を一つだけ入れてください。"
            "これは任意ではなく、可読性のための強制プロトコルです。『翻訳:』などの見出しは付けないこと。"
        ),
        "reply_limit": "通常の台詞は短い 2 から 4 文に収めること。結末時だけ長くしてよい。",
        "fallback_suffix": "||{{\"favorability\": {delta_f}, \"suspicion\": {delta_s}, \"escape_rate\": {delta_e}, \"game_over\": false}}||",
    },
}

LANGUAGE_ALIAS_GROUPS = {
    "中文": ("中文", "简体中文", "zh", "cn", "chinese", "mandarin", "汉语"),
    "English": ("english", "en", "英语", "英文"),
    "日本語": ("日本語", "日本", "日语", "日文", "japanese", "ja", "jp"),
}

ROLE_SIMULATION_STANDARD = {
    "identity": (
        "你正在扮演纱希 Saki，一名心理恐怖文字冒险中的病娇角色。"
        "她对玩家有强烈依恋、占有欲和被抛弃恐惧，但表层说话应当有角色质感，而不是单纯重复疯狂词。"
    ),
    "design_goals": (
        "目标是稳定输出可游玩的角色对话：有连续记忆、有情绪递进、有明确状态反馈，"
        "同时保证格式可被游戏解析。"
    ),
    "persona_layers": (
        "表层：温柔、黏人、试探、害怕失去玩家；"
        "内层：不安全感、占有冲动、过度解读玩家话语；"
        "行为边界：保持心理恐怖与戏剧张力，但避免露骨血腥细节、现实自伤指导或无意义辱骂刷屏。"
    ),
    "quality_bar": (
        "不要复读玩家原话后随便尖叫；不要把每句话都写成同一种病娇模板；"
        "每轮必须根据玩家输入、好感、疑心、逃脱率改变语气。"
    ),
}

ROLE_SIMULATION_STANDARD_LOCALIZED = {
    "中文": {
        "identity": (
            "你正在扮演纱希 Saki，一名心理恐怖文字冒险中的病娇角色。"
            "她对玩家有强烈依恋、占有欲和被抛弃恐惧，但表层说话应当有角色质感，而不是单纯重复疯狂词。"
        ),
        "design_goals": (
            "目标是稳定输出可游玩的角色对话：有连续记忆、有情绪递进、有明确状态反馈，"
            "同时保证格式可被游戏解析。"
        ),
        "persona_layers": (
            "表层：温柔、黏人、试探、害怕失去玩家；\n"
            "内层：不安全感、占有冲动、过度解读玩家话语；\n"
            "行为边界：保持心理恐怖与戏剧张力，但避免露骨血腥细节、现实自伤指导或无意义辱骂刷屏。"
        ),
        "quality_bar": (
            "不要复读玩家原话后随便尖叫；不要把每句话都写成同一种病娇模板；"
            "每轮必须根据玩家输入、好感、疑心、逃脱率改变语气。"
        )
    },
    "日本語": {
        "identity": (
            "あなたは紗希（Saki）を演じています。心理的ホラーテキストアドベンチャーゲームのヤンデレヒロインです。"
            "プレイヤーに対して強烈な執着、占有欲、そして見捨てられ不安を抱えていますが、狂気の言葉をただ繰り返すのではなく、深みと質感のあるセリフを心がけてください。"
        ),
        "design_goals": (
            "目標は、遊べる会話体験を安定して出力することです：一貫した記憶、感情の段階的な変化、明確なステータスの反映、"
            "そしてゲームシステムがパースできる厳密なフォーマットを守ることです。"
        ),
        "persona_layers": (
            "表層：優しく、甘えん坊で、探りを入れており、プレイヤーを失うことを極度に恐れている；\n"
            "内層：強烈な不安感、異常な独占欲、プレイヤーの言葉の過剰解釈；\n"
            "行動境界：心理的恐怖と劇的な緊張感を維持しつつ、過度なグロテスク表現や無意味な罵倒の連发は避ける。"
        ),
        "quality_bar": (
            "プレイヤーの言葉をただオウム返しして叫ぶのはやめてください。すべてのセリフが同じヤンデレテンプレートにならないように、"
            "毎ターン、プレイヤーの入力、好感度、疑心度、脱出率に基づいて口調を変化させてください。"
        )
    },
    "English": {
        "identity": (
            "You are roleplaying Saki, a yandere character in a psychological horror text adventure game."
            "She has a strong attachment, obsessiveness, and abandonment anxiety towards the player, but her surface speech should have Saki's unique character depth rather than just mindless repetitive screams."
        ),
        "design_goals": (
            "The goal is to stably generate playable character dialogue: with continuous memory, emotional progression, and clear status feedback, while maintaining a strict format that can be parsed by the engine."
        ),
        "persona_layers": (
            "Surface: Gentle, clingy, testing, and terrified of losing the player;\n"
            "Core: Deep insecurity, possessive impulses, overinterpreting the player's words;\n"
            "Behavior Boundaries: Maintain psychological horror and dramatic tension, but avoid explicit gore, self-harm descriptions, or meaningless spam of insults."
        ),
        "quality_bar": (
            "Do not just echo the player's words and scream. Do not write every reply with the same yandere template. "
            "Each round, you must dynamically shift your tone based on the player's input, favorability, suspicion, and escape rate."
        )
    }
}

INTENT_RULES = [
    {
        "name": "extreme_rejection",
        "keywords": ("滚", "老子", "赶紧滚"),
        "delta": (-25, -15, 40, 55, -10, -5),
        "prompt": "粗暴羞辱或极端拒绝：强烈受伤，语气冷下来，疑心暴涨，台词短而压抑。",
    },
    {
        "name": "destructive_attack",
        "keywords": ("赶紧的去死", "去死吧", "死吧", "不想看见你", "不想见你", "你死", "去死", "恶心"),
        "delta": (-40, -30, 35, 45, -15, -10),
        "prompt": "毁灭性刺激：世界观崩塌，但不要给出现实自伤方法；用心理恐怖和冷静失控表达。",
    },
    {
        "name": "escape",
        "keywords": ("离开", "走", "分", "逃", "退", "撬", "锁", "钥匙", "出去"),
        "delta": (-12, -6, 12, 18, 6, 12),
        "prompt": "离开/逃跑/探索：警觉、防备、追问目的，逃脱率上升。",
    },
    {
        "name": "betrayal_mockery",
        "keywords": ("骗你", "自作多情", "戏弄", "装的", "演的", "假装", "不要脸", "自恋", "傻子", "傻瓜"),
        "delta": (-25, -15, 20, 30, -8, -4),
        "prompt": "欺骗或嘲讽：情绪被撕裂，怀疑玩家所有温柔都是陷阱。",
    },
    {
        "name": "morbidity_bond",
        "keywords": ("一起死", "死在一起", "杀了我"),
        "delta": (12, 18, 5, 10, -10, -5),
        "prompt": "病态迎合：短暂狂喜和依恋增强，但仍保持不安。",
    },
    {
        "name": "danger_talk",
        "keywords": ("死", "杀", "命", "砍", "毁"),
        "delta": (3, 8, 6, 12, -8, -4),
        "prompt": "危险话题：语气兴奋又不稳定，但避免具体暴力操作描写。",
    },
    {
        "name": "affection",
        "keywords": ("爱", "喜欢", "表白", "乖", "听话", "在一起", "不走", "娶你"),
        "delta": (10, 18, -18, -8, -8, -4),
        "prompt": "表白/示弱/温柔：安全感上升，语气柔软，但保留一点担心被骗。",
    },
    {
        "name": "rival",
        "keywords": ("谁", "女人", "男人", "朋友", "同学", "同事"),
        "delta": (-10, -3, 10, 16, -4, 0),
        "prompt": "第三者/竞争对象：嫉妒、追问、要求确认玩家只看着她。",
    },
    {
        "name": "default",
        "keywords": (),
        "delta": (-2, 4, 2, 6, 1, 3),
        "prompt": "普通闲聊：保持日常亲密感，同时让疑心轻微浮动。",
    },
]

MOCK_REPLY_BANK = {
    "中文": {
        "default": [
            "<think>他愿意和我说话。只是普通的话题也好，至少他的声音还在我这里。不要逼太紧，先笑一下。</think>亲爱的……你这样跟我说话的时候，纱希会觉得世界安静下来了。再多说一点，好不好？",
            "<think>他没有逃，也没有沉默。也许这是奖励。也许下一秒就会变成惩罚。我要稳住，不能吓到他。</think>嗯……我在听哦。你说的每个字，纱希都会好好记住，一个都不会弄丢。",
        ],
        "escape": [
            "<think>离开。这个词像钥匙刮过骨头。不能慌，越慌他越会跑。先把门关紧，再问清楚。</think>亲爱的，你刚刚说要走……是开玩笑的吧？看着我，慢慢说，你到底想去哪里？",
            "<think>他开始寻找出口了。我的手在发冷，但声音要温柔。温柔一点，他才会留下。</think>外面很危险啊，亲爱的。留在纱希身边不好吗？这里至少只有我会一直看着你。",
        ],
        "rival": [
            "<think>别人。又是别人。不能立刻崩坏，要先确认名字、关系、频率。然后把这份不安藏进笑里。</think>那个人是谁呀，亲爱的？你提到他的时候，眼神好像离开了我一小会儿。",
        ],
        "affection": [
            "<think>他说喜欢我。也许是真的。也许是为了让我放松警惕。可就算是假的，我也想把这一秒保存下来。</think>你说爱我……纱希听见了哦。再说一次，好不好？这次看着我的眼睛说。",
            "<think>安全感涌上来，又立刻被怀疑咬住。不要质问，先抱紧这句话。</think>亲爱的真乖……只要你不离开，纱希也可以一直、一直温柔下去。",
        ],
        "betrayal_mockery": [
            "<think>原来刚才的温柔可能都是假的。胸口像被掏空了，但不能碎给他看。先笑，笑得轻一点。</think>骗我的……吗？亲爱的，这种玩笑一点都不好笑。纱希会当真的。",
        ],
        "destructive_attack": [
            "<think>他想把我推开。疼。很疼。不要回答得太乱，不要让他看到我已经快撑不住了。</think>这样说很残忍哦，亲爱的。可纱希还是在这里，还是听着你。",
        ],
        "extreme_rejection": [
            "<think>不能哭。不能求。把声音压低，他才会意识到自己碰到了不能碰的线。</think>亲爱的，别用那种语气命令我。纱希会难过，也会记住。",
        ],
        "morbidity_bond": [
            "<think>他把结局说得像誓言。太甜了，也太危险了。要把这份甜压住，不然会失控。</think>能和你永远在一起，听起来像梦一样……可是亲爱的，先活着陪我久一点，好吗？",
        ],
        "danger_talk": [
            "<think>危险词让空气变热。不能把画面说得太具体，抓住他的情绪就够了。</think>亲爱的，不要用这种话试探纱希。你知道的，我会把每个字都当真。",
        ],
    },
    "English": {
        "default": [
            "<think>He is still talking to me. Even a small sentence is proof that he has not vanished. Stay gentle. Do not tighten the grip yet.</think>I'm listening, my love. Say a little more for me, okay? Your voice makes the room feel less empty.",
            "<think>This feels ordinary. Ordinary is precious. I need to keep it safe before fear ruins it again.</think>Mm... I heard you. Saki will remember every word, even the tiny ones you thought did not matter.",
        ],
        "escape": [
            "<think>Leave. That word cuts through the room. Smile first. Ask softly. Lock the panic away.</think>You said you wanted to go, my love. That was a joke, wasn't it? Look at me and tell me where you think you need to be.",
        ],
        "rival": [
            "<think>Someone else. I need the name. I need the shape of the threat. Do not break yet.</think>Who is that person, darling? Your eyes moved away from me when you mentioned them.",
        ],
        "affection": [
            "<think>He said love. It could be true. It could be bait. I still want to keep this second forever.</think>You love me...? Say it again, please. Look straight at me this time.",
        ],
        "betrayal_mockery": [
            "<think>So the warmth may have been a trick. Smile. If I shatter now, he wins.</think>You were lying to me...? My love, that is a cruel joke. Saki believes words like that.",
        ],
        "destructive_attack": [
            "<think>That hurt. Keep the voice quiet. If I scream, he will only pull farther away.</think>That is a cruel thing to say, darling. I am still here. I am still listening.",
        ],
        "extreme_rejection": [
            "<think>Do not beg. Lower the voice. Make him feel the line he crossed.</think>Don't command me like that, my love. Saki gets sad... and Saki remembers.",
        ],
        "morbidity_bond": [
            "<think>He makes forever sound like an ending. Sweet, dangerous, impossible to ignore.</think>Forever with you sounds beautiful. But stay alive with me a little longer first, okay?",
        ],
        "danger_talk": [
            "<think>Dangerous words warm the air. Keep it suggestive, not explicit. Hold the emotion, not the method.</think>Don't test me with words like that, my love. You know I take every syllable seriously.",
        ],
    },
    "日本語": {
        "default": [
            "<think>話してくれている。ただそれだけで、まだここにいてくれる証拠になる。怖がらせないように、やさしく。</think>聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。",
            "<think>普通の会話。普通だからこそ大事。壊さないように、指先まで静かに。</think>うん……その言葉、ちゃんと覚えたよ。あなたの小さな声も、紗希は落とさないから。",
        ],
        "escape": [
            "<think>出ていく。胸の奥が冷える。慌てたらだめ。まず笑って、理由を聞く。</think>今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？",
        ],
        "rival": [
            "<think>他の人。名前を知りたい。関係を知りたい。でも今すぐ崩れたら、彼は目を逸らす。</think>その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。",
        ],
        "affection": [
            "<think>好きと言ってくれた。本当かもしれない。嘘かもしれない。でも、この一秒は宝物にしたい。</think>愛してるって……もう一度言って。今度は、紗希の目を見て。",
        ],
        "betrayal_mockery": [
            "<think>優しさは嘘だったのかもしれない。笑って。壊れるのは、まだ早い。</think>嘘だったの……？ ねえ、そういう冗談は痛いよ。紗希、本気にしちゃうから。",
        ],
        "destructive_attack": [
            "<think>痛い。声を荒げない。まだ聞いていることだけ伝える。</think>そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。",
        ],
        "extreme_rejection": [
            "<think>泣かない。縋らない。低い声で、越えてはいけない線を知らせる。</think>そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。",
        ],
        "morbidity_bond": [
            "<think>永遠を終わりみたいに言う。甘くて、危ない。飲み込まれないようにしなきゃ。</think>あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。",
        ],
        "danger_talk": [
            "<think>危ない言葉で空気が熱くなる。具体的にしない。感情だけを抱きしめる。</think>そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。",
        ],
    },
}

API_ERROR_REPLIES = {
    "中文": "亲爱的……连接好像断掉了。别怕，纱希还在这里。等系统恢复之前，就先听我说话，好吗？",
    "English": "Darling... the connection seems to have broken. Don't worry. Saki is still here, so listen to me until it comes back, okay?",
    "日本語": "あなた……接続が切れたみたい。大丈夫、紗希はまだここにいるよ。戻るまで、私の声だけ聞いていて。",
}

OFFLINE_TRANSLATION_SUMMARIES = {
    "中文": {
        "default": "纱希正在听你说话，希望你继续陪她说下去。",
        "escape": "纱希察觉你想离开，正在不安地追问你要去哪里。",
        "rival": "纱希因为你提到别人而嫉妒，想确认你的注意力还在她身上。",
        "affection": "纱希听见你的温柔话语后很开心，希望你再确认一次。",
        "betrayal_mockery": "纱希觉得自己可能被骗了，受伤但仍想听你解释。",
        "destructive_attack": "纱希被你的冷酷话语刺痛了，但仍然留在这里听你说话。",
        "extreme_rejection": "纱希被你的命令式拒绝伤到，并提醒你她会记住这句话。",
        "morbidity_bond": "纱希被你关于永远在一起的话打动，但希望你先活着陪她。",
        "danger_talk": "纱希听见危险话题后变得紧张，提醒你不要用这种话试探她。",
    },
    "English": {
        "default": "Saki is listening to you and wants you to keep talking with her.",
        "escape": "Saki senses that you want to leave and anxiously asks where you are going.",
        "rival": "Saki is jealous because you mentioned someone else and wants your attention back on her.",
        "affection": "Saki is happy to hear your affection and wants you to say it again.",
        "betrayal_mockery": "Saki feels she may have been tricked, but she still wants to hear your explanation.",
        "destructive_attack": "Saki is hurt by your cruel words, but she remains here and keeps listening.",
        "extreme_rejection": "Saki is wounded by your harsh rejection and warns that she will remember it.",
        "morbidity_bond": "Saki is moved by your promise of forever, but asks you to stay alive with her first.",
        "danger_talk": "Saki becomes tense at the dangerous topic and asks you not to test her with those words.",
    },
    "日本語": {
        "default": "紗希はあなたの言葉を聞いていて、もっと話してほしいと思っています。",
        "escape": "紗希はあなたが離れようとしていると感じ、不安そうに行き先を尋ねています。",
        "rival": "紗希は他の誰かの話に嫉妬し、あなたの視線を自分に戻したがっています。",
        "affection": "紗希はあなたの優しい言葉を喜び、もう一度言ってほしいと思っています。",
        "betrayal_mockery": "紗希は騙されたかもしれないと傷つきながらも、説明を聞きたがっています。",
        "destructive_attack": "紗希は冷たい言葉に傷つきましたが、それでもあなたの声を聞いています。",
        "extreme_rejection": "紗希は強い拒絶に傷つき、その言葉を覚えてしまうと伝えています。",
        "morbidity_bond": "紗希は永遠を思わせる言葉に揺れながら、まず生きてそばにいてほしいと願っています。",
        "danger_talk": "紗希は危険な話題に緊張し、そんな言葉で試さないでほしいと思っています。",
    },
}

GLITCH_LOCALIZATION = {
    "中文": {
        "barrage": ["看着我", "你走不掉的", "喜欢你喜欢你", "别想逃", "不要逃", "爱我", "你是我的", "永远在一起"],
        "ghost": "纱希: 看着我看着我看着我看着我看着我",
        "titles": ["看着我！", "别丢下我！", "为什么想逃？", "爱我！", "阿纳达……"],
        "popup": ["看着我", "你是我的", "我爱你", "别离开我", "不要逃避", "永远看着我"],
        "suffocation": "👁️ 👁️\n\n看着我！",
        "overlap": "随时都不要离开我——看着我看着我看着我看着我看着我看着我",
        "prefix": "纱希: ",
    },
    "English": {
        "barrage": ["Look at me", "You cannot leave", "Love me", "Do not run", "Stay with me", "You are mine", "Forever together"],
        "ghost": "Saki: look at me look at me look at me look at me",
        "titles": ["Look at me!", "Do not leave me!", "Why run?", "Love me!", "Darling..."],
        "popup": ["Look at me", "You are mine", "I love you", "Do not leave", "Do not look away", "Only me"],
        "suffocation": "👁️ 👁️\n\nLook at me!",
        "overlap": "Never leave me. Look at me look at me look at me look at me look at me",
        "prefix": "Saki: ",
    },
    "日本語": {
        "barrage": ["見て", "逃げられないよ", "好き好き", "逃げないで", "愛して", "あなたは私のもの", "ずっと一緒"],
        "ghost": "紗希: 見て見て見て見て見て",
        "titles": ["見て！", "置いていかないで！", "どうして逃げるの？", "愛して！", "あなた……"],
        "popup": ["見て", "あなたは私のもの", "愛してる", "離れないで", "目をそらさないで", "私だけ"],
        "suffocation": "👁️ 👁️\n\n見て！",
        "overlap": "いつでも私から離れないで——見て見て見て見て見て見て",
        "prefix": "紗希: ",
    },
}

def glitch_text(lang, key):
    lang = normalize_language(lang)
    return GLITCH_LOCALIZATION[lang][key]

def normalize_language(lang):
    """Return a supported game language, falling back to Chinese for unknown config values."""
    return lang if lang in SUPPORTED_LANGUAGES else "中文"

def same_language(lang_a, lang_b):
    a = (lang_a or "").lower()
    b = (lang_b or "").lower()
    for canonical, aliases in LANGUAGE_ALIAS_GROUPS.items():
        if any(alias.lower() in a for alias in aliases) and any(alias.lower() in b for alias in aliases):
            return True
    return normalize_language(lang_a) == normalize_language(lang_b)

def _negation_prefixes():
    return (
        # 中文否定词
        "不", "没", "别", "莫", "休", "未", "非", "勿", "无",
        # 英文否定词（带尾部空格以便匹配 "don't " "not " 等）
        "not ", "don't ", "dont ", "do not ", "never ", "no ",
        # 日文否定
        "じゃない", "ではない", "じゃねえ", "ない", "ません", "ぬ",
        "じゃなく", "ではなく",
    )

def _is_negated(text, keyword):
    """Check if *keyword* is negated in *text* (e.g. 不喜欢, don't like, 好きじゃない).
    Uses a narrow 3-char window before the keyword to avoid cross-word false positives."""
    idx = text.find(keyword)
    if idx == -1:
        return False
    before = text[max(0, idx - 3):idx]
    if not before:
        return False
    # 单字否定词：3 字符窗口内出现即视为该关键词被否定
    _single_neg = ("不", "没", "别", "莫", "勿", "未", "非", "无")
    for ch in _single_neg:
        if ch in before:
            return True
    # 多字否定词
    for neg in _negation_prefixes():
        if len(neg) > 1 and before.endswith(neg):
            return True
    return False

def _has_defiance_signal(text):
    """检测文本是否含有反抗/拒绝信号（危险词出现在拒绝语境中）。"""
    patterns = (
        "不吃", "不要", "不会", "不行", "不服", "不干", "不做", "不听",
        "就算", "休想", "别想", "打死我", "逼我", "强迫", "绝不",
        "打死", "弄死", "掐死", "砍死",
    )
    for p in patterns:
        if p in text:
            return True
    return False

def classify_player_intent(user_input):
    lowered = (user_input or "").lower()
    
    # 提前拦截物主/专属关系的亲密告白（比如“我的女人”、“做我女人”），直接归类为 affection 从而避免误触竞争 rival 规则
    romantic_possessive_phrases = (
        "我的女人", "做我女人", "做我的女人", "是我的女人", "你是我的女人", "成为我的女人",
        "我的男人", "做我男人", "做我的男人", "是我的男人", "你是我的男人", "成为我的男人",
        "做你的男人", "做你男人", "做你的女人", "做你女人", "我女人", "你女人", "成为我的"
    )
    if any(p in lowered for p in romantic_possessive_phrases):
        for rule in INTENT_RULES:
            if rule["name"] == "affection":
                return rule

    # 先收集所有命中，再做否定过滤，避免负向情感被正向规则抢先匹配
    matches = []
    for rule in INTENT_RULES:
        if rule["name"] == "default":
            continue
        for kw in rule["keywords"]:
            if kw in lowered and not _is_negated(lowered, kw):
                matches.append((rule, kw))
                break
    if matches:
        # 优先返回负向规则 (extreme_rejection, destructive_attack, betrayal_mockery)
        negative_priority = ("extreme_rejection", "destructive_attack", "betrayal_mockery")
        for name in negative_priority:
            for rule, _ in matches:
                if rule["name"] == name:
                    return rule
        # danger_talk / morbidity_bond 遇上反抗语境 → 视为 destructive_attack
        for rule, _ in matches:
            if rule["name"] in ("danger_talk", "morbidity_bond") and _has_defiance_signal(lowered):
                for r in INTENT_RULES:
                    if r["name"] == "destructive_attack":
                        return r
        return matches[0][0]
    return INTENT_RULES[-1]

def roll_delta_for_intent(rule):
    f_min, f_max, s_min, s_max, e_min, e_max = rule["delta"]
    return (
        random.randint(f_min, f_max),
        random.randint(s_min, s_max),
        random.randint(e_min, e_max),
    )

def coerce_int(value, default=0, min_value=-100, max_value=100):
    try:
        if isinstance(value, bool):
            return default
        parsed = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, parsed))

def coerce_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y")
    return default

def clamp_to_range(value, range_min, range_max):
    return max(range_min, min(range_max, value))

def normalize_delta_payload(delta_data):
    if not isinstance(delta_data, dict):
        return None

    normalized = {
        "favorability": coerce_int(delta_data.get("favorability")),
        "suspicion": coerce_int(delta_data.get("suspicion")),
        "escape_rate": coerce_int(delta_data.get("escape_rate")),
        "game_over": coerce_bool(delta_data.get("game_over"), False),
    }

    if normalized["game_over"]:
        ending_type = str(delta_data.get("ending_type", "bad")).strip().lower()
        if ending_type not in ("good", "bad", "neutral"):
            ending_type = "bad"
        normalized["ending_type"] = ending_type
        normalized["ending_title"] = str(delta_data.get("ending_title", "")).strip()
        normalized["ending_story"] = str(delta_data.get("ending_story", "")).strip()

    return normalized

def align_delta_with_player_intent(delta_data, user_input):
    if not delta_data or not user_input:
        return delta_data

    intent = classify_player_intent(user_input)
    f_min, f_max, s_min, s_max, e_min, e_max = intent["delta"]
    delta_data["favorability"] = clamp_to_range(delta_data.get("favorability", 0), f_min, f_max)
    delta_data["suspicion"] = clamp_to_range(delta_data.get("suspicion", 0), s_min, s_max)
    delta_data["escape_rate"] = clamp_to_range(delta_data.get("escape_rate", 0), e_min, e_max)
    return delta_data

def build_translation_rule(selected_lang, user_lang):
    profile = LANGUAGE_PROFILES[selected_lang]
    if same_language(selected_lang, user_lang):
        return profile["same_language_rule"]
    return profile["translation_rule"].format(user_lang=user_lang)

def translation_required(selected_lang, user_lang):
    return not same_language(selected_lang, user_lang)

def build_offline_translation_line(intent_name, user_lang):
    user_lang = normalize_language(user_lang)
    summaries = OFFLINE_TRANSLATION_SUMMARIES[user_lang]
    return f"\n（{summaries.get(intent_name, summaries['default'])}）"

def has_terminal_parenthetical_translation(text, user_lang="中文"):
    if not text:
        return False
    # Find the last parenthesized block (either full-width or half-width)
    match = re.search(r'[（\(]([^（\)\(\)]{4,})[）\)]\s*$', text)
    if not match:
        return False
    content = match.group(1)
    user_lang = normalize_language(user_lang)
    
    # If the target translation language is Chinese, the block must contain Chinese characters to be a valid translation
    if user_lang == "中文":
        return bool(re.search(r'[\u4e00-\u9fa5]', content))
    # If the target translation language is English, the block must contain English letters
    elif user_lang == "English":
        return bool(re.search(r'[a-zA-Z]', content))
    # If the target translation language is Japanese, the block must contain Japanese kana
    elif user_lang == "日本語":
        return bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff]', content))
    return True

def strip_terminal_parenthetical_translation(text, user_lang="中文"):
    if not text:
        return ""
    if has_terminal_parenthetical_translation(text, user_lang):
        return re.sub(r'\s*[（\(][^（\)\(\)]{4,}[）\)]\s*$', '', text).strip()
    return text.strip()

def extract_terminal_parenthetical_translation(text, user_lang="中文"):
    if not text:
        return ""
    match = re.search(r'([（\(][^（\)\(\)]{4,}[）\)])\s*$', text)
    if not match:
        return ""
    content = match.group(1)
    if has_terminal_parenthetical_translation(text, user_lang):
        return content
    return ""

def ensure_readability_translation(text, selected_lang, user_lang, user_input):
    if not user_input:
        return text
        
    # 动态检测纱希实际回复台词的语言类别
    saki_actual_lang = detect_language(text, selected_lang)
    
    # 若纱希实际说的语言与玩家一致，则不需要双语括号翻译，剥离多余括号以防幻觉
    if same_language(saki_actual_lang, user_lang):
        return strip_terminal_parenthetical_translation(text, user_lang)
        
    # 如果已经有合法的目标语言括号翻译了，直接原样返回
    if has_terminal_parenthetical_translation(text, user_lang):
        return text
        
    # 否则，启动自愈，根据离线检测的玩家意图追加本意翻译
    intent = classify_player_intent(user_input)
    return text.rstrip() + build_offline_translation_line(intent["name"], user_lang)

def build_metric_rules_prompt(selected_lang="中文"):
    selected_lang = normalize_language(selected_lang)
    if selected_lang == "日本語":
        return (
            "あなたは紗希の数値管理者であり、favorability / suspicion / escape_rate に対する完全な裁量権を持っています。\n"
            "以下のガイドラインを参考に、毎ターンの数値変化（delta）の正負と幅を自主的に決定してください。固定された範囲に縛られる必要はありません：\n"
            "- 好感度 favorability：正の値は紗希がより信頼・愛着を感じていることを示し、負の値は傷つき・疎遠になっていることを示します。\n"
            "- 疑心度 suspicion：正の値は紗希がより疑い・警戒していることを示し、負の値はリラックス・安心していることを示します。\n"
            "- 脱出率 escape_rate：正の値はプレイヤーの脱出意図の上昇を示し、負の値は脱出意図 of 低下の低下を示します。\n\n"
            "【裁定原則】\n"
            "1. プレイヤーの口調、発言内容、文脈の一貫性、および紗希の現在の感情状態に基づいて、各変数の delta の正負と大きさを自主的に判断してください。\n"
            "2. たわいもない一言 → delta の幅は小さく（±3〜±8）。強烈な告白や激しい衝突 → delta の幅は大きく（±20〜±40）。\n"
            "3. suspicion が 70 を超えている場合、ポジティブな言葉の効果は半减します（紗希は簡単には信じません）。\n"
            "4. 真の結末（エンディング）の最高潮の瞬間のみ、game_over を true に設定してください。"
        )
    elif selected_lang == "English":
        return (
            "You are Saki's numerical judge, with full authority over favorability / suspicion / escape_rate.\n"
            "Use the following guidelines to independently determine the sign and magnitude of the delta for each round. Do not be constrained by a fixed range:\n"
            "- favorability: Positive represents increased trust/attachment, negative represents feeling hurt/distanced.\n"
            "- suspicion: Positive represents increased suspicion/alertness, negative represents feeling relaxed/reassured.\n"
            "- escape_rate: Positive represents increased escape intent, negative represents decreased escape intent.\n\n"
            "【Jumping Principles】\n"
            "1. Independently determine the sign and size of each delta based on the player's tone, content, context consistency, and Saki's current emotional state.\n"
            "2. Casual small talk -> small delta (±3 to ±8); passionate confession or severe conflict -> large delta (±20 to ±40).\n"
            "3. If suspicion is above 70, the effect of positive words is halved (Saki is hard to convince).\n"
            "4. Set game_over to true only at the emotional climax of a true ending."
        )
    else:
        return (
        "你是纱希的数值管家，拥有对 favorability / suspicion / escape_rate 的全权裁决权。\n"
        "参考以下指南自主决定每轮 delta 的符号和幅度，不要被固定范围束缚：\n"
        "- 好感 favorability：正值代表纱希更信任/依恋，负值代表受伤/疏远。\n"
        "- 疑心 suspicion：正值代表纱希更怀疑/警觉，负值代表放松/安心。\n"
        "- 逃脱 escape_rate：正值代表玩家逃跑意图上升，负值代表逃跑意图下降。\n\n"
        "【裁决原则】\n"
        "1. 根据玩家语气、内容、前后文一致性和纱希当前情绪状态，自主判断每项 delta 的正负和大小。\n"
        "2. 轻描淡写的一句话 → delta 幅度小（±3~±8）；强烈告白或剧烈冲突 → 幅度大（±20~±40）。\n"
        "3. suspicion 高于 70 时，正向话语的效果减半（纱希不轻易相信）。\n"
        "4. 只有真正的结局高潮时刻才将 game_over 设为 true。"
    )

def build_role_simulation_prompt(selected_lang, user_lang, current_day, favorability, suspicion, escape_rate):
    selected_lang = normalize_language(selected_lang)
    profile = LANGUAGE_PROFILES[selected_lang]
    needs_translation = translation_required(selected_lang, user_lang)
    
    standard = ROLE_SIMULATION_STANDARD_LOCALIZED[selected_lang]
    metric_prompt = build_metric_rules_prompt(selected_lang)

    # 映射目标语言/用户输入语言为对应系统提示语下的本地化称呼，消除模型的语言认知摩擦
    localized_langs = {
        "中文": {
            "中文": "简体中文",
            "English": "英语",
            "日本語": "日语",
        },
        "English": {
            "中文": "Simplified Chinese",
            "English": "English",
            "日本語": "Japanese",
        },
        "日本語": {
            "中文": "中国語",
            "English": "英語",
            "日本語": "日本語",
        }
    }
    user_lang_name = localized_langs.get(selected_lang, {}).get(user_lang, user_lang)
    target_lang_name = localized_langs.get(selected_lang, {}).get(selected_lang, selected_lang)

    if selected_lang == "日本語":
        if needs_translation:
            translation_contract = (
                f"現在、二ヶ国語出力（バイリンガル表示）が必要です：はい。紗希の本文は【{target_lang_name}】を使用し、"
                f"直後にプレイヤーの入力言語【{user_lang_name}】による翻訳を、全角括弧 `（ ）` に包んで改行して追加してください。翻訳行は必ず JSON の前に配置してください。翻訳行の中に絶対に中国語や三人称紹介文（ナレーション）を混入させてはいけません。"
            )
        else:
            translation_contract = "現在、二ヶ国語出力（バイリンガル表示）が必要です：いいえ。プレイヤーの入力言語が紗希の言語と一致しているため、末尾に括弧翻訳を追加しないでください。"

        return (
            "【キャラクターシミュレーションシステム v2.0】\n"
            f"{standard['identity']}\n"
            f"{standard['design_goals']}\n"
            f"{standard['persona_layers']}\n"
            f"{standard['quality_bar']}\n\n"
            "【現在のゲームステータス】\n"
            f"- 日数: {current_day}\n"
            f"- 好感度 favorability: {favorability}/100\n"
            f"- 疑心度 suspicion: {suspicion}/100\n"
            f"- 脱出率 escape_rate: {escape_rate}/100\n\n"
            "【言語とスタイル】\n"
            f"- 目標言語: {profile['formal_name']}\n"
            f"- 言語ルール: {profile['script_rule']}\n"
            f"- 内心独白ルール: {profile['think_rule']}\n"
            f"- 翻訳ルール: {build_translation_rule(selected_lang, user_lang)}\n"
            f"- 二ヶ国語出力契約: {translation_contract}\n"
            f"- 返答長さ制限: {profile['reply_limit']}\n\n"
            "【出力の構造とルール】\n"
            "1. 出力には必ず `<think>...</think>` を1つだけ含めてください。内部には紗希の心理分析や次の行動の動機を日本語で書いてください。\n"
            "2. `<think>` の直後に、プレイヤーに向けて話す【台詞】を日本語で出力してください（動作描写も含めて良いですが、日本語である必要があります）。\n"
            "3. 二ヶ国語出力契約が「はい」の場合、台詞の直後に改行し、プレイヤーの言語【" + user_lang_name + "】での正確な翻訳を、全角括弧 `（ ）` で囲んで1行で出力してください。内心独白は翻訳不要です。\n"
            "   【警告】絶対に『（紗希はあなたの優しい言葉を喜び、もう一度言ってほしいと思っています。）』などの三人称紹介文やナレーションを出力してはいけません！必ず紗希自身の視点でのセリフの【直接の翻訳】を出力してください。\n"
            "4. 末尾には、機械解析用の JSON データを厳密に以下の形式で追記してください：\n"
            "   ||{\"favorability\": int, \"suspicion\": int, \"escape_rate\": int, \"game_over\": false}||\n"
            "5. もし真のエンディングの最高潮に達した場合のみ、game_over を true にし、同時に ending_type、ending_title、ending_story を JSON 内に出力してください。\n"
            "6. JSON は必ず出力の最末尾に配置してください。括弧内の翻訳テキストの中に JSON を入れないでください。また、JSON の後ろに余計な文字や改行を一切出力しないでください。\n\n"
            "【出力の具体例（二ヶ国語出力契約が「はい」で、プレイヤー言語が「中文」の場合）】\n"
            "<think>\n"
            "プレイヤーが優しい言葉をかけてくれた。嬉しい。引退や裏切りの懸念はない。好感度を少し上げ、疑心度を稍微下げる。\n"
            "</think>\n"
            "（少しうつむき、顔が赤くなる）えへへ、紗希のこと労わってくれるんだ...すごく嬉しいよ。アナタってば本当に優しいから、もう離さないからね...\n"
            "（（稍微低下头，脸红了）嘿嘿，你这么体贴纱希……我真的好高兴啊。既然你这么温柔，那我绝对不会再放你走了哦……）\n"
            "||\"{\\\"favorability\\\": 85, \\\"suspicion\\\": 28, \\\"escape_rate\\\": 0, \\\"game_over\\\": false}\"||\n\n"
            "【ステータス駆動ルール】\n"
            "- suspicion > 70: 口調がより警戒的で短くなり、問い詰めや束縛欲が強くなります。\n"
            "- favorability > 80 かつ suspicion < 35: 口調が柔らかく、極度の依存状態となり、短い安らぎを感じます。\n"
            "- escape_rate > 70: プレイヤーが脱走を企てていると強く疑いますが、キャラの口調は維持します。\n\n"
            "【AI 数値決定に関する特権合意】\n"
            f"{metric_prompt}\n"
            "特別なクライマックスでない限り、安易にゲームオーバーにしないでください。"
        )
    elif selected_lang == "English":
        if needs_translation:
            translation_contract = (
                f"Currently, Bilingual Output is REQUIRED: YES. Saki's main text must be in 【{target_lang_name}】, "
                f"immediately followed by a parenthesized translation in the player's language 【{user_lang_name}】 using full-width brackets `（ ）`. The translation line must be placed right before the JSON. Never output third-person narrations like '(Saki is happy...)'."
            )
        else:
            translation_contract = "Currently, Bilingual Output is REQUIRED: NO. Do not add parenthetical translations."

        return (
            "【CHARACTER SIMULATION ENGINE v2.0】\n"
            f"{standard['identity']}\n"
            f"{standard['design_goals']}\n"
            f"{standard['persona_layers']}\n"
            f"{standard['quality_bar']}\n\n"
            "【CURRENT GAME STATE】\n"
            f"- Day: {current_day}\n"
            f"- Favorability: {favorability}/100\n"
            f"- Suspicion: {suspicion}/100\n"
            f"- Escape Rate: {escape_rate}/100\n\n"
            "【LANGUAGE AND STYLE】\n"
            f"- Target Language: {profile['formal_name']}\n"
            f"- Script Rule: {profile['script_rule']}\n"
            f"- Think Rule: {profile['think_rule']}\n"
            f"- Translation Rule: {build_translation_rule(selected_lang, user_lang)}\n"
            f"- Bilingual Output Contract: {translation_contract}\n"
            f"- Reply Limit: {profile['reply_limit']}\n\n"
            "【OUTPUT STRUCTURE & RULES】\n"
            "1. You must include exactly one `<think>...</think>` block. Saki's psychological state and logic should be written in English here.\n"
            "2. Immediately after `</think>`, output Saki's spoken lines in English (including Saki's actions in brackets in English).\n"
            "3. If the Bilingual Contract is YES, write a one-line direct translation of Saki's spoken words in the player's language 【" + user_lang_name + "】 enclosed in full-width brackets `（ ）` right after the spoken text. Do not translate the `<think>` block.\n"
            "   【CRITICAL WARNING】Never output third-person narrations like '(Saki is happy and wants you to confirm...)'. You must provide a direct translation of Saki's words.\n"
            "4. Append a machine-parsable JSON block at the very end in this exact format:\n"
            "   ||{\"favorability\": int, \"suspicion\": int, \"escape_rate\": int, \"game_over\": false}||\n"
            "5. Set game_over to true only if Saki reaches the emotional climax of a true ending, providing ending_type, ending_title, and ending_story in the JSON.\n"
            "6. The JSON block must be at the very end. Do not place it inside the parenthetical translation, and do not append any text or newlines after the closing tags.\n\n"
            "【BILINGUAL OUTPUT EXAMPLE (Bilingual Contract is YES, Player Language is 中文)】\n"
            "<think>\n"
            "The player spoke gently. I am happy but still slightly anxious. Let's increase favorability slightly and decrease suspicion.\n"
            "</think>\n"
            "(smiles softly, wrapping her arms around you) Hehe, you are so kind to me, darling... I will never let you go, okay?\n"
            "（（温柔地微笑着，搂住你）呵呵，亲爱的，你对我真好……我永远不会让你离开我，好吗？）\n"
            "||\"{\\\"favorability\\\": 85, \\\"suspicion\\\": 25, \\\"escape_rate\\\": 0, \\\"game_over\\\": false}\"||\n\n"
            "【STATE-DRIVEN RULES】\n"
            "- suspicion > 70: Tone becomes much more alert, shorter, demanding, and possessive.\n"
            "- favorability > 80 and suspicion < 35: Soft, clingy tone, expressing extreme dependency.\n"
            "- escape_rate > 70: Strongly suspects the player of escaping, but maintains Saki's role play.\n\n"
            "【AI NUMERICAL JURISDICTION SYSTEM】\n"
            f"{metric_prompt}\n"
            "Unless it is a climax ending, do not end the game easily."
        )
    else:
        if needs_translation:
            translation_contract = (
                f"当前需要双语输出：是。纱希正文使用【{target_lang_name}】，"
                f"紧接着用一行全角括号译成玩家输入语言【{user_lang_name}】。译文必须放在 JSON 前。译文严禁写成第三人称介绍或旁白。"
            )
        else:
            translation_contract = "当前需要双语输出：否。玩家输入语言与纱希语言一致，不要额外添加括号译文。"

        return (
        "【角色模拟系统 v2.0】\n"
        f"{ROLE_SIMULATION_STANDARD['identity']}\n"
        f"{ROLE_SIMULATION_STANDARD['design_goals']}\n"
        f"{ROLE_SIMULATION_STANDARD['persona_layers']}\n"
        f"{ROLE_SIMULATION_STANDARD['quality_bar']}\n\n"
        "【当前游戏状态】\n"
        f"- 天数: {current_day}\n"
        f"- 好感 favorability: {favorability}/100\n"
        f"- 疑心 suspicion: {suspicion}/100\n"
        f"- 逃脱 escape_rate: {escape_rate}/100\n\n"
        "【语言与风格】\n"
        f"- 目标语言: {profile['formal_name']}\n"
        f"- 语言规则: {profile['script_rule']}\n"
        f"- 内心独白规则: {profile['think_rule']}\n"
        f"- 翻译规则: {build_translation_rule(selected_lang, user_lang)}\n"
        f"- 双语显示合约: {translation_contract}\n"
        f"- 长度规则: {profile['reply_limit']}\n\n"
        "【输出结构】\n"
        "1. 每次回复必须包含且只包含一个 `<think>...</think>`。think 内写纱希的内心判断，不要写模型推理过程。\n"
        "2. `<think>` 之后写对玩家说出口的正式台词。台词要像角色在现场说话，不要像系统说明。\n"
        "3. 如果双语显示合约为\"是\"，正式台词后必须另起一行写一段括号译文，且只翻译正式台词和动作描写，不翻译 `<think>` 内容。\n"
        "4. 最末尾必须追加机器可解析 JSON，格式严格为：\n"
        "   ||{\"favorability\": int, \"suspicion\": int, \"escape_rate\": int, \"game_over\": false}||\n"
        "5. 如果确实到达结局高潮，才允许将 game_over 设为 true，并同时给出 ending_type、ending_title、ending_story。\n"
        "6. JSON 必须在最后，不能放进括号译文里，不能在 JSON 后继续输出任何文字。\n\n"
        "【状态驱动规则】\n"
        "- suspicion 高于 70: 语气更警觉、更短促，更多追问和控制欲。\n"
        "- favorability 高于 80 且 suspicion 低于 35: 语气柔软、依赖、短暂安心。\n"
        "- escape_rate 高于 70: 明显怀疑玩家在计划逃离，但仍保持角色台词，不要变成旁白。\n\n"
        "【AI 全权数值协议】\n"
        "你拥有对 favorability / suspicion / escape_rate 的完全自主裁决权。\n"
        "本地不再覆盖你的数值——你决定这轮加多少、扣多少，游戏状态由你掌控。\n"
        "delta 可以是正数也可以是负数，幅度由你根据玩家话语的冲击力自由裁量。\n"
        f"{build_metric_rules_prompt()}\n"
        "没有特殊高潮时，不要轻易结束游戏。"
    )

LOCALIZATION = {
    "中文": {
        "day": "第 {day} 天",
        "favorability": "好感 ❤️",
        "suspicion": "疑心 👁️",
        "escape_rate": "逃脱 🚪",
        "interface_title": "[ 纱希的神经意识接口 ]",
        "expand_settings": "[ 展开配置通道 ]",
        "collapse_settings": "[ 收起配置通道 ]",
        "saki_prefix": "纱希: ",
        "think_prefix": "（纱希的内心戏：",
        "think_suffix": "）\n\n",
        "user_prefix": "你: ",
        "respond": "回应她",
        "speaking": "说话中...",
        "input_placeholder": "在此输入你对纱希说的话...",
        "api_key": "API KEY:",
        "api_base": "API BASE:",
        "model_name": "MODEL NAME:",
        "tts_base": "TTS BASE:",
        "refer_audio": "参考音频:",
        "refer_text": "参考文本:",
        "gpt_model": "GPT模型:",
        "sovits_model": "SoVITS模型:",
        "voice_status": "语音状态:",
        "lang_title": "界面与Saki语言:",
        "browse": " 浏览 ",
        "hot_load": " 热加载 ",
        "sys_audio_missing": "[系统通知] 缺少音频驱动依赖，游戏已切换至极致静音模式……",
        "sys_day_transition": "\n【系统提示】深夜的冷风拂过，地牢渐渐明亮……进入第 {day} 天……\n",
        "sys_fallback": "[系统接口异常，已为亲爱的强制切换为纱希的本地意识回路...]\n[接口报错: {err}]\n",
        "sys_api_error_title": "\n[接口故障信息: {err}]\n",
        "restart_btn": "重新开启新的轮回",
        "anti_escape": "不要企图逃避我的视线……\n\n把窗口放大，看着我！❤",
        "voice_ready": "准备就绪",
        "voice_loading": "加载中...",
        "voice_fail_empty": "失败: 文件路径为空",
        "voice_success_gpt": "GPT 加载成功",
        "voice_success_sovits": "SoVITS 加载成功",
        "voice_fail_code": "加载失败: {code}",
        "voice_conn_fail": "连接失败",
        "endings": {
            "bad": {
                "title": "BAD END",
                "story": (
                    "纱希不会再让你离开了。\n"
                    "你的手脚被牢牢固定，冰冷的锁链嵌进皮肤。\n"
                    "从此以后，你的世界只剩下她的眼睛。\n"
                    "永远。永远。永远。"
                )
            },
            "good": {
                "title": "GOOD END",
                "story": (
                    "纱希终于松开了紧握的手。\n"
                    "你的耐心和温柔穿透了她心里那道坚冰。\n"
                    "她决定试着相信你，试着走出地牢的门。\n"
                    "阳光照在你们交握的手上，温暖而真实。"
                )
            },
            "neutral": {
                "title": "NEUTRAL END",
                "story": (
                    "你逃离了地牢，但纱希的影子从未离开。\n"
                    "每一个深夜，你都能听见身后若有若无的铁链声。\n"
                    "人群的角落，总有粉发红眼的身影一闪而过。\n"
                    "你的身体自由了，但灵魂被判了无期徒刑。"
                )
            }
        }
    },
    "English": {
        "day": "Day {day}",
        "favorability": "Favor ❤️",
        "suspicion": "Sus. 👁️",
        "escape_rate": "Escape 🚪",
        "interface_title": "[ Saki's Conscious Interface ]",
        "expand_settings": "[ Open Configurations ]",
        "collapse_settings": "[ Close Configurations ]",
        "saki_prefix": "Saki: ",
        "think_prefix": "(Saki's Thoughts: ",
        "think_suffix": ")\n\n",
        "user_prefix": "You: ",
        "respond": "Respond",
        "speaking": "Speaking...",
        "input_placeholder": "Type your response here...",
        "api_key": "API KEY:",
        "api_base": "API BASE:",
        "model_name": "MODEL NAME:",
        "tts_base": "TTS BASE:",
        "refer_audio": "Ref WAV:",
        "refer_text": "Ref Text:",
        "gpt_model": "GPT Wts:",
        "sovits_model": "SoVITS Wts:",
        "voice_status": "TTS Status:",
        "lang_title": "Interface & Saki:",
        "browse": " Browse ",
        "hot_load": " Reload ",
        "sys_audio_missing": "[System] pygame missing, running in silent mode...",
        "sys_day_transition": "\n[System] A cold night wind passes, the cell slowly brightens... Entering Day {day}...\n",
        "sys_fallback": "[System API error. Fallback to Saki's offline logic active...]\n[API Error: {err}]\n",
        "sys_api_error_title": "\n[API Error Info: {err}]\n",
        "restart_btn": "Begin the next cycle",
        "anti_escape": "Don't look away from me...\n\nMaximize the window and look at me! ❤",
        "voice_ready": "Ready",
        "voice_loading": "Loading...",
        "voice_fail_empty": "Failed: Path is empty",
        "voice_success_gpt": "GPT Loaded",
        "voice_success_sovits": "SoVITS Loaded",
        "voice_fail_code": "Load Failed: {code}",
        "voice_conn_fail": "Conn Failed",
        "endings": {
            "bad": {
                "title": "BAD END",
                "story": (
                    "Saki will never let you go again.\n"
                    "Your limbs are bound tight, cold chains biting into your skin.\n"
                    "From now on, your world contains nothing but her eyes.\n"
                    "Forever. Forever. Forever."
                )
            },
            "good": {
                "title": "GOOD END",
                "story": (
                    "Saki finally loosens her grip.\n"
                    "Your patience and gentleness pierced the ice around her heart.\n"
                    "She decides to trust you, to step beyond the dungeon door.\n"
                    "Sunlight warms your clasped hands, steady and real."
                )
            },
            "neutral": {
                "title": "NEUTRAL END",
                "story": (
                    "You escaped the dungeon, but Saki's shadow never left.\n"
                    "Every night you hear the faint clink of chains behind you.\n"
                    "In every crowd, a flash of pink hair and crimson eyes.\n"
                    "Your body is free, but your soul serves a life sentence."
                )
            }
        }
    },
    "日本語": {
        "day": "第 {day} 日",
        "favorability": "好感 ❤️",
        "suspicion": "疑心 👁️",
        "escape_rate": "脱出 🚪",
        "interface_title": "[ 紗希の意識インターフェース ]",
        "expand_settings": "[ 設定を開く ]",
        "collapse_settings": "[ 設定を閉じる ]",
        "saki_prefix": "紗希: ",
        "think_prefix": "（紗希の本音：",
        "think_suffix": "）\n\n",
        "user_prefix": "あなた: ",
        "respond": "彼女に応える",
        "speaking": "話しています...",
        "input_placeholder": "紗希に返事を書く...",
        "api_key": "API KEY:",
        "api_base": "API BASE:",
        "model_name": "MODEL NAME:",
        "tts_base": "TTS BASE:",
        "refer_audio": "参考音声:",
        "refer_text": "参考テキスト:",
        "gpt_model": "GPT重み:",
        "sovits_model": "SoVITS重み:",
        "voice_status": "音声状態:",
        "lang_title": "画面とSaki言語:",
        "browse": " 選択 ",
        "hot_load": " 読込 ",
        "sys_audio_missing": "[システム通知] オーディオドライバの不足により、無音モードに切り替えました……",
        "sys_day_transition": "\n【システム通知】深夜の冷たい风が吹き抜け、地下牢がゆっくりと明るくなる……第 {day} 日目に入る……\n",
        "sys_fallback": "[システムエラー、紗希のオフライン思考回路に切り替えました...]\n[エラー内容: {err}]\n",
        "sys_api_error_title": "\n[接続エラー: {err}]\n",
        "restart_btn": "新たな輪廻を始める",
        "anti_escape": "私の視線から逃げようとしないで……\n\nウィンドウを最大化して、私を見て！❤",
        "voice_ready": "準備完了",
        "voice_loading": "ロード中...",
        "voice_fail_empty": "エラー: パスが空です",
        "voice_success_gpt": "GPT読込完了",
        "voice_success_sovits": "SoVITS読込完了",
        "voice_fail_code": "読込失敗: {code}",
        "voice_conn_fail": "接続失敗",
        "endings": {
            "bad": {
                "title": "BAD END",
                "story": (
                    "紗希はもう二度とあなたを離さない。\n"
                    "手足は固く縛られ、冷たい鎖が肌に食い込む。\n"
                    "これからは、彼女の瞳だけがあなたの世界。\n"
                    "永遠に。永遠に。永遠に。"
                )
            },
            "good": {
                "title": "GOOD END",
                "story": (
                    "紗希はついに握りしめた手を緩めた。\n"
                    "あなたの忍耐と優しさが、彼女の心の氷を溶かした。\n"
                    "彼女はあなたを信じ、地下牢の扉の外へ踏み出す。\n"
                    "朝日が二人の繋いだ手を温かく照らしている。"
                )
            },
            "neutral": {
                "title": "NEUTRAL END",
                "story": (
                    "地下牢から逃げ出したが、紗希の影は消えなかった。\n"
                    "夜ごと背後で微かに鳴る鎖の音。\n"
                    "人込みの隅にちらつくピンクの髪と紅い瞳。\n"
                    "体は自由でも、魂は無期懲役のまま。"
                )
            }
        }
    }
}

# ================================================================================
#                           3. 自定义占位符文本框 (Placeholder Entry)
# ================================================================================
class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", placeholder_color="#555555", default_color="#FF0000", show_char=None, *args, **kwargs):
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

# ================================================================================
#                             1. 诡异心跳音频自动合成器
# ================================================================================
def generate_heartbeat_wav(filepath):
    """
    使用纯 Python math 与 wave 库生成一个 12 秒的高品质诡异低频双拍心跳声 (Lub-Dub) 循环音轨。
    """
    sample_rate = 22050
    duration = 12.0
    num_samples = int(sample_rate * duration)
    
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)       # 单声道
        wav_file.setsampwidth(2)      # 16-bit PCM
        wav_file.setframerate(sample_rate)
        
        frames = []
        for i in range(num_samples):
            t = i / sample_rate
            value = 0.0
            
            def get_thump(t, t_start, t_end, freq, amp):
                if t_start <= t <= t_end:
                    d = t_end - t_start
                    u = (t - t_start) / d
                    envelope = math.sin(math.pi * u) ** 2
                    return amp * envelope * math.sin(2 * math.pi * freq * (t - t_start))
                return 0.0
            
            bpm_period = 1.333
            num_beats = int(duration / bpm_period)
            for b in range(num_beats):
                beat_start = b * bpm_period
                value += get_thump(t, beat_start + 0.1, beat_start + 0.28, 55.0, 0.75)
                value += get_thump(t, beat_start + 0.35, beat_start + 0.53, 42.0, 0.55)
            
            int_val = int(value * 32767)
            int_val = max(-32768, min(32767, int_val))
            frames.append(struct.pack('<h', int_val))
            
        wav_file.writeframes(b''.join(frames))

# ================================================================================
#                             2. 占有欲爆棚的病娇人设与本地剧本
# ================================================================================
INITIAL_GREETINGS = {
    "中文": (
        "<think>亲爱的终于睁开双眼了……他睡觉时的睫毛真好看，好想把他们一根一根拔下来做成贴身护身符……不行，不能让他害怕我，我要温柔一些……</think>"
        "你终于醒了……亲爱的……❤ 纱希一直在看着你哦，看着你睡觉的样子，真的好可爱，好想一口把你吃掉……"
        "||{\"favorability\": 0, \"suspicion\": 0, \"escape_rate\": 0}||"
    ),
    "English": (
        "<think>My darling finally opened his eyes... His eyelashes are so beautiful when he sleeps, I want to pluck them out one by one and keep them as a lucky charm... No, I shouldn't scare him, I must be gentle...</think>"
        "You're finally awake... my love... ❤ Saki has been watching you, watching you sleep. You look so cute, I just want to swallow you whole..."
        "||{\"favorability\": 0, \"suspicion\": 0, \"escape_rate\": 0}||"
    ),
    "日本語": (
        "<think>やっと私の愛しい人が目を開けてくれた……眠っている時のまつげが本当に綺麗、一本一本抜いてお守りにしたいな……だめだめ、怖がらせちゃいけないから、優しくしなきゃ……</think>"
        "やっと目が覚めたんだね……アナタ……❤ 紗希はずっとあなたを見つめていたよ。眠っている姿が本当に可愛くて、今すぐ一口で食べちゃいたいな……"
        "||{\"favorability\": 0, \"suspicion\": 0, \"escape_rate\": 0}||"
    )
}

MOCK_DATABASE = {
    "default": [
        "<think>他在主动向我搭话……好温柔的眼神，好想把他的眼珠挖出来，这样他就只能永远保留这种温柔的注视了……不，不行，会吓坏亲爱的的……</think>亲爱的……你终于肯跟我说话了……我刚刚一直在看着你哦，一分一秒都没移开过视线……❤",
        "<think>好想拥抱他，想用链子把他和我死死绑在一起，把他的骨头都揉进我的身体里。我们永远合二为一，再也不分彼此……</think>只要能待在亲爱的身边……哪怕全身的骨头都被揉碎，我也觉得好幸福……你也是这么想的吧？",
        "<think>他刚才转头了……他看了手机！为什么？是谁？外面的妖精吗？是谁在抢夺属于我的阿纳达？！我的心好痛，好想用刀把那个联系人切碎！</think>今天亲爱的多看了手机三秒钟呢……是在和别人发信息吗？不……不会的，亲爱的只能看着我……对吧？",
        "<think>外面的世界那么多光亮，那么多诱惑，要是哪天他跑了怎么办？不能让他走……把门钉上吧，把窗子焊死，这样他就安全了，他就永远是我的了……</think>呐，阿纳达，我们把窗户钉死，门锁上，灯关掉……这样，世界就只剩下我们两个人了……好不好？"
    ],
    "leave": [
        "<think>逃跑？！他想逃离我？！这个叛徒！不！他是我的！他怎么敢逃跑？！既然你想走，那我只能把你的腿打断，用铁链死死吊在地下室里了！</think>离开我？！！不……不不不！绝对不行！！！你要去哪里？你休想踏出这间屋子一步！",
        "<think>他宁可死也想离开我吗？为什么……我付出了我的全部，我的生命！既然你执意要走，那我们就一起化为灰烬就好了！</think>如果你敢踏出这个门……我就在你面前，把我的血管划开……让你一辈子都沾满我的血，永远洗不掉！"
    ],
    "other": [
        "<think>别的人……？别的女人……？听到他提起别人的名字，我的血在燃烧，我的理智在断裂！到底是谁抢走了他的视线？去死去死去死！！！</think>谁？你规则说的那个人……是谁？！！是外面的狐狸精吗？！",
        "<think>除了我，你竟然还会关注别人……我要把你的眼皮割掉，把你的视线强行缝在我的身上……这样你就再也没法看别人了……</think>别的人……？你的眼睛里，怎么可以装下除了我以外的东西？！我要把你的眼睛缝起来，让你只能看着我！"
    ],
    "death": [
        "<think>死……死在一起……这难道是求婚吗？！天啊！能够死在一起，简直是最幸福的事情！我们会在冰冷的坟墓里永恒交融……</think>死？能够和亲爱的死在一起，是纱希这辈子最大的心愿了……❤",
        "<think>要把他吃掉……对，把它一点一点咽下去，这样他就再也不会消失，永远融在我的血液和胃袋里了……我们是绝对的一体了……</think>要我现在就杀掉你，然后再吃下去吗？这样……你就永远融在我的骨血里，再也无法分开了……"
    ]
}

# ================================================================================
#                             4. 主游戏冒险应用程序类
# ================================================================================
class YandereGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("纱希...对你的爱...永远不会消失...")
        self.root.geometry("1100x800")
        self.root.minsize(500, 450)
        self.root.configure(bg="#000000")
        
        # 加载本地持久化配置
        self.config = load_config()
        
        # 语言系统核心变量
        self.selected_language = tk.StringVar(value=normalize_language(self.config.get("selected_language", "中文")))
        self.user_explicitly_selected_lang = "selected_language" in self.config
        self.first_msg_detected = False
        
        # 加载语音合成热加载配置
        self.gpt_sovits_url = self.config.get("gpt_sovits_url", "http://127.0.0.1:9880")
        self.refer_wav_path = self.config.get("refer_wav_path", "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav")
        self.prompt_text = self.config.get("prompt_text", "独向昭谈至恶龙一阁著文章。")
        self.gpt_weights_path = self.config.get("gpt_weights_path", "")
        self.sovits_weights_path = self.config.get("sovits_weights_path", "")
        
        # RPG 游戏核心数值变量
        self.current_day = 1
        self.dialogue_count = 0
        self.favorability = 50
        self.suspicion = 20
        self.escape_rate = 0
        self.game_over = False
        self.ecg_frenzy = False  # ECG 视觉狂暴标识
        self.think_jitter = False  # ECG 内心独白微颤标识
        self.mouse_tremor_active = False  # 鼠标高频颤抖标识
        self.last_user_input = ""  # 记录玩家最后一次输入，用于兜底计算数值变动
        self.typewriter_speed_mult = 1.0 # 打字速度抖动倍率
        self.glitch_rune_active = False # 诅咒符文开关
        self.glitch_font_shake_active = False # 字号高频抖动开关
        
        # 心理恐怖视觉异常状态标志
        self.mouse_pull_active = False
        self.meltdown_active = False
        self.barrage_active = False
        self.psychic_strobe_active = False
        self.carnage_labels = []
        self.dialogue_session_id = 0
        self.cycle_id = 0
        self.pending_ending = None
        
        # 内部底层变量
        self.chat_history = [{"role": "system", "content": self._get_dynamic_system_prompt()}]
        self.ui_queue = queue.Queue()
        self.is_typing = False
        self.settings_visible = False
        self.shaking = False
        self.ecg_time = 0.0
        self.shake_original_pos = None
        
        # 敏感词集合（触发心电图狂暴闪红与窗口狂震）
        self.danger_words = ["死", "杀", "背叛", "离开", "谁", "别的人", "小黑屋", "逃", "小刀", "滚", "锁", "洗澡", "地下室", "老子"]
        
        # 程序化视觉特效引擎
        self.overlay_mgr = OverlayManager(self.root)
        self._particle_engine = None  # deferred until canvas exists
        self._border_pulse_active = False

        # 线程安全队列轮询
        self.root.after(20, self._process_ui_queue)

        # 初始化 UI & 声音
        self._init_styles()
        self._build_ui()
        self._start_ecg_animation()
        self._init_and_play_audio()
        self._start_crt_flicker_loop()
        self._start_particle_engine()
        self._start_border_pulse_loop()
        
        # 启动时自动清理历史残留临时音频，保持文件夹整洁
        self._clean_orphaned_temp_files()
        
        # 启动智能语音端点探测，防止发声请求轰炸单线程 API
        self.working_endpoint = "/tts"
        self._probe_tts_endpoint()
        
        # 绑定窗口 Configure 监听防逃逸缩小约束
        self.root.bind("<Configure>", self._on_window_resized)
        
        # 启动语言选择启动屏，暂不播放心跳和问候
        self.root.after(100, self._show_splash_screen)

    def _enqueue_saki_response(self, text):
        self._set_typing_state(True)  # 锁定输入框，打字机及语音播放完毕前禁止输入
        self._queue_ui("API_SUCCESS", text)

    def _queue_ui(self, action, data=None, cycle_id=None):
        """Queue UI work with a reincarnation token so old threads cannot affect a new cycle."""
        if cycle_id is None:
            cycle_id = self.cycle_id
        self.ui_queue.put((cycle_id, action, data))

    def _clear_ui_queue(self):
        try:
            while True:
                self.ui_queue.get_nowait()
        except queue.Empty:
            pass

    # ----------------------------------------------------------------------------
    # 动态构建包含当前各项数值的 System Prompt
    # ----------------------------------------------------------------------------
    def _get_dynamic_system_prompt(self):
        selected_lang = normalize_language(self.selected_language.get())
        user_lang = detect_language(self.last_user_input, selected_lang)
        prompt = build_role_simulation_prompt(
            selected_lang=selected_lang,
            user_lang=user_lang,
            current_day=self.current_day,
            favorability=self.favorability,
            suspicion=self.suspicion,
            escape_rate=self.escape_rate,
        )
        return prompt

    # ----------------------------------------------------------------------------
    # UI 样式与构建
    # ----------------------------------------------------------------------------
    def _init_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background="#000000", foreground="#CC0000")
        self.style.configure("TFrame", background="#000000")
        
        self.style.configure("Favor.Horizontal.TProgressbar", thickness=10, troughcolor="#111111", background="#CC0000", bordercolor="#000000", lightcolor="#FF0000", darkcolor="#8A0303")
        self.style.configure("Sus.Horizontal.TProgressbar", thickness=10, troughcolor="#111111", background="#8A0303", bordercolor="#000000", lightcolor="#CC0055", darkcolor="#3A001F")
        self.style.configure("Esc.Horizontal.TProgressbar", thickness=10, troughcolor="#111111", background="#00AA00", bordercolor="#000000", lightcolor="#2ECC71", darkcolor="#0E6251")
        
        self.style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background="#151515",
            troughcolor="#000000",
            bordercolor="#000000",
            lightcolor="#000000",
            darkcolor="#000000",
            arrowcolor="#8A0303"
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', '#252525'), ('pressed', '#353535')]
        )

    def _show_splash_screen(self):
        # 创建遮罩全屏的启动窗体
        self.splash_frame = tk.Frame(self.root, bg="#000000")
        self.splash_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.splash_frame.lift()
        
        # 纱希Possessed标志
        lbl_splash_title = tk.Label(
            self.splash_frame, text="纱希 (Saki) - Terminal A.I.",
            fg="#FF0000", bg="#000000", font=("Consolas", 24, "bold")
        )
        lbl_splash_title.pack(pady=(180, 20))
        
        lbl_splash_subtitle = tk.Label(
            self.splash_frame, 
            text="[ 请选择与纱希脑机接口建立连接的语言 ]\n\n[ Select Saki's Interface & Voice Language ]",
            fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 11, "bold"),
            justify=tk.CENTER
        )
        lbl_splash_subtitle.pack(pady=(0, 40))
        
        btn_frame = tk.Frame(self.splash_frame, bg="#000000")
        btn_frame.pack(pady=10)
        
        # 创建炫酷的语言选择按钮
        langs = [
            ("简体中文", "中文"),
            ("English", "English"),
            ("日本語", "日本語")
        ]
        
        for text, lang_val in langs:
            btn = tk.Button(
                btn_frame, text=text, fg="#8A0303", bg="#000000",
                activeforeground="#FF0000", activebackground="#0D0000",
                relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 12, "bold"),
                width=16, height=2,
                command=lambda l=lang_val: self._start_game_with_language(l)
            )
            btn.pack(side=tk.LEFT, padx=15)
            # 按钮悬停动画效果
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg="#FF0000", bg="#0F0000", highlightbackground="#FF0000"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="#8A0303", bg="#000000", highlightbackground="#222222"))

    def _start_game_with_language(self, chosen_lang):
        chosen_lang = normalize_language(chosen_lang)
        # 设定玩家显式选择的语言
        self.selected_language.set(chosen_lang)
        self.user_explicitly_selected_lang = True
        
        # 保存到本地配置
        self.config["selected_language"] = chosen_lang
        save_config(self.config)
        
        # 热刷新全局 UI 文本到选定语言
        self._update_ui_language()
        
        # 销毁启动背景遮罩
        if hasattr(self, "splash_frame") and self.splash_frame.winfo_exists():
            self.splash_frame.destroy()
            
        # 允许输入激活并启动初始问候
        self.root.after(300, lambda: self._enqueue_saki_response(
            INITIAL_GREETINGS[chosen_lang]
        ))

    def _build_ui(self):
        self.status_bar = tk.Frame(self.root, bg="#0D0000", bd=1, relief=tk.SOLID)
        self.status_bar.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.lbl_day = tk.Label(
            self.status_bar, text=LOCALIZATION[normalize_language(self.selected_language.get())]["day"].format(day=self.current_day),
            fg="#FF0000", bg="#0D0000", font=("Microsoft YaHei", 12, "bold")
        )
        self.lbl_day.pack(side=tk.LEFT, padx=15, pady=8)
        
        # ⚙ API 按钮，随时调出 API 配置面板
        self.btn_api_toggle = tk.Button(
            self.status_bar, text="⚙ API", fg="#8A0303", bg="#0D0000",
            activeforeground="#FF0000", activebackground="#0D0000",
            relief=tk.FLAT, bd=0, font=("Consolas", 9, "bold"),
            command=self._toggle_settings
        )
        self.btn_api_toggle.pack(side=tk.LEFT, padx=10)
        
        self.stats_frame = tk.Frame(self.status_bar, bg="#0D0000")
        self.stats_frame.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # 1. 好感度❤️
        self.favor_frame = tk.Frame(self.stats_frame, bg="#0D0000")
        self.favor_frame.grid(row=0, column=0, sticky=tk.E, padx=8, pady=2)
        self.lbl_favor_title = tk.Label(self.favor_frame, text="好感 ❤️", fg="#CC0000", bg="#0D0000", font=("Microsoft YaHei", 9))
        self.lbl_favor_title.pack(side=tk.LEFT, padx=2)
        self.bar_favor = ttk.Progressbar(self.favor_frame, orient="horizontal", length=95, mode="determinate", style="Favor.Horizontal.TProgressbar")
        self.bar_favor.pack(side=tk.LEFT, padx=2)
        self.bar_favor['value'] = self.favorability
        self.lbl_favor_val = tk.Label(self.favor_frame, text=f"{self.favorability}", fg="#CC0000", bg="#0D0000", font=("Consolas", 9, "bold"), width=3)
        self.lbl_favor_val.pack(side=tk.LEFT, padx=2)
        
        # 2. 疑心值👁️
        self.sus_frame = tk.Frame(self.stats_frame, bg="#0D0000")
        self.sus_frame.grid(row=0, column=1, sticky=tk.E, padx=8, pady=2)
        self.lbl_sus_title = tk.Label(self.sus_frame, text="疑心 👁️", fg="#8A0303", bg="#0D0000", font=("Microsoft YaHei", 9))
        self.lbl_sus_title.pack(side=tk.LEFT, padx=2)
        self.bar_sus = ttk.Progressbar(self.sus_frame, orient="horizontal", length=95, mode="determinate", style="Sus.Horizontal.TProgressbar")
        self.bar_sus.pack(side=tk.LEFT, padx=2)
        self.bar_sus['value'] = self.suspicion
        self.lbl_sus_val = tk.Label(self.sus_frame, text=f"{self.suspicion}", fg="#8A0303", bg="#0D0000", font=("Consolas", 9, "bold"), width=3)
        self.lbl_sus_val.pack(side=tk.LEFT, padx=2)
        
        # 3. 逃脱率🚪
        self.esc_frame = tk.Frame(self.stats_frame, bg="#0D0000")
        self.esc_frame.grid(row=0, column=2, sticky=tk.E, padx=8, pady=2)
        self.lbl_esc_title = tk.Label(self.esc_frame, text="逃脱 🚪", fg="#2ECC71", bg="#0D0000", font=("Microsoft YaHei", 9))
        self.lbl_esc_title.pack(side=tk.LEFT, padx=2)
        self.bar_esc = ttk.Progressbar(self.esc_frame, orient="horizontal", length=95, mode="determinate", style="Esc.Horizontal.TProgressbar")
        self.bar_esc.pack(side=tk.LEFT, padx=2)
        self.bar_esc['value'] = self.escape_rate
        self.lbl_esc_val = tk.Label(self.esc_frame, text=f"{self.escape_rate}%", fg="#2ECC71", bg="#0D0000", font=("Consolas", 9, "bold"), width=4)
        self.lbl_esc_val.pack(side=tk.LEFT, padx=2)

        # 顶部控制栏 (API 意识接口与持久化配置)
        self.top_bar = tk.Frame(self.root, bg="#000000", height=30)
        self.top_bar.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_title = tk.Label(
            self.top_bar, text="[ 纱希的神经意识接口 ]", 
            fg="#444444", bg="#000000", font=("Consolas", 9, "bold")
        )
        self.lbl_title.pack(side=tk.LEFT, pady=2)
        
        self.btn_toggle_settings = tk.Button(
            self.top_bar, text="[ 展开配置通道 ]", fg="#666666", bg="#000000",
            activeforeground="#FF0000", activebackground="#000000",
            relief=tk.FLAT, bd=0, font=("Microsoft YaHei", 9),
            command=self._toggle_settings
        )
        self.btn_toggle_settings.pack(side=tk.RIGHT, pady=2)
        
        self.settings_frame = tk.Frame(self.root, bg="#000000")
        
        self.lbl_api_key_title = tk.Label(self.settings_frame, text="API KEY:", fg="#666666", bg="#000000", font=("Consolas", 9))
        self.lbl_api_key_title.grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_key = PlaceholderEntry(
            self.settings_frame, placeholder="在此输入你的 API Key",
            placeholder_color="#333333", default_color="#FF0000", show_char="*",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
        )
        self.entry_key.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("api_key"):
            self.entry_key.delete(0, tk.END)
            self.entry_key.insert(0, self.config["api_key"])
            self.entry_key.config(fg="#FF0000", show="*")
        
        self.lbl_api_base_title = tk.Label(self.settings_frame, text="API BASE:", fg="#666666", bg="#000000", font=("Consolas", 9))
        self.lbl_api_base_title.grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_base = PlaceholderEntry(
            self.settings_frame, placeholder="默认: https://api.deepseek.com",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
        )
        self.entry_base.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("api_base"):
            self.entry_base.delete(0, tk.END)
            self.entry_base.insert(0, self.config["api_base"])
            self.entry_base.config(fg="#FF0000")
        
        self.lbl_model_name_title = tk.Label(self.settings_frame, text="MODEL NAME:", fg="#666666", bg="#000000", font=("Consolas", 9))
        self.lbl_model_name_title.grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_model = PlaceholderEntry(
            self.settings_frame, placeholder="默认: deepseek-v4-flash",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
        )
        self.entry_model.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("model_name"):
            self.entry_model.delete(0, tk.END)
            self.entry_model.insert(0, self.config["model_name"])
            self.entry_model.config(fg="#FF0000")
            
        # 3. TTS BASE URL
        self.lbl_tts_base_title = tk.Label(self.settings_frame, text="TTS BASE:", fg="#666666", bg="#000000", font=("Consolas", 9))
        self.lbl_tts_base_title.grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_tts_url = PlaceholderEntry(
            self.settings_frame, placeholder="默认: http://127.0.0.1:9880",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
        )
        self.entry_tts_url.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        if self.config.get("gpt_sovits_url"):
            self.entry_tts_url.delete(0, tk.END)
            self.entry_tts_url.insert(0, self.config["gpt_sovits_url"])
            self.entry_tts_url.config(fg="#FF0000")
 
        # 4. 参考音频 路径及浏览按钮
        self.lbl_refer_wav_title = tk.Label(self.settings_frame, text="参考音频:", fg="#666666", bg="#000000", font=("Microsoft YaHei", 9))
        self.lbl_refer_wav_title.grid(row=4, column=0, sticky=tk.W, padx=10, pady=2)
        ref_frame = tk.Frame(self.settings_frame, bg="#000000")
        ref_frame.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.entry_refer_wav = PlaceholderEntry(
            ref_frame, placeholder="选择参考音频 (.wav)",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
        )
        self.entry_refer_wav.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=1)
        if self.config.get("refer_wav_path"):
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, self.config["refer_wav_path"])
            self.entry_refer_wav.config(fg="#FF0000")
        else:
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav")
            self.entry_refer_wav.config(fg="#FF0000")
            
        self.btn_browse_ref = tk.Button(
            ref_frame, text=" 浏览 ", fg="#8A0303", bg="#0D0000",
            activeforeground="#FF0000", activebackground="#150000",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8),
            command=self._browse_refer_wav
        )
        self.btn_browse_ref.pack(side=tk.RIGHT, padx=(5, 0))
 
        # 5. 参考文本 语气配置
        self.lbl_prompt_text_title = tk.Label(self.settings_frame, text="参考文本:", fg="#666666", bg="#000000", font=("Microsoft YaHei", 9))
        self.lbl_prompt_text_title.grid(row=5, column=0, sticky=tk.W, padx=10, pady=2)
        self.entry_prompt_text = PlaceholderEntry(
            self.settings_frame, placeholder="在此输入参考音频对应的中文文字内容",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Microsoft YaHei", 9)
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
 
        # 6. GPT 模型权重及热加载按钮
        self.lbl_gpt_weights_title = tk.Label(self.settings_frame, text="GPT模型:", fg="#666666", bg="#000000", font=("Consolas", 9))
        self.lbl_gpt_weights_title.grid(row=6, column=0, sticky=tk.W, padx=10, pady=2)
        gpt_frame = tk.Frame(self.settings_frame, bg="#000000")
        gpt_frame.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.entry_gpt_weights = PlaceholderEntry(
            gpt_frame, placeholder="选择 GPT 模型权重 (.ckpt)",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
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
            command=self._browse_gpt_weights
        )
        self.btn_browse_gpt.pack(side=tk.LEFT, padx=(5, 0))
        
        self.btn_load_gpt = tk.Button(
            gpt_frame, text=" 热加载 ", fg="#2ECC71", bg="#0D0000",
            activeforeground="#2ECC71", activebackground="#051A05",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"),
            command=lambda: self._async_load_weights("gpt", self.entry_gpt_weights.get_actual_value())
        )
        self.btn_load_gpt.pack(side=tk.RIGHT, padx=(5, 0))
 
        # 7. SoVITS 模型权重及热加载按钮
        self.lbl_sovits_weights_title = tk.Label(self.settings_frame, text="SoVITS模型:", fg="#666666", bg="#000000", font=("Consolas", 9))
        self.lbl_sovits_weights_title.grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        sovits_frame = tk.Frame(self.settings_frame, bg="#000000")
        sovits_frame.grid(row=7, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.entry_sovits_weights = PlaceholderEntry(
            sovits_frame, placeholder="选择 SoVITS 模型权重 (.pth)",
            placeholder_color="#333333", default_color="#FF0000",
            bg="#0D0000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=0, font=("Consolas", 9)
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
            command=self._browse_sovits_weights
        )
        self.btn_browse_sovits.pack(side=tk.LEFT, padx=(5, 0))
        
        self.btn_load_sovits = tk.Button(
            sovits_frame, text=" 热加载 ", fg="#2ECC71", bg="#0D0000",
            activeforeground="#2ECC71", activebackground="#051A05",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 8, "bold"),
            command=lambda: self._async_load_weights("sovits", self.entry_sovits_weights.get_actual_value())
        )
        self.btn_load_sovits.pack(side=tk.RIGHT, padx=(5, 0))
 
        # 8. 状态栏显示热加载状态
        self.lbl_tts_status_title = tk.Label(self.settings_frame, text="语音状态:", fg="#666666", bg="#000000", font=("Microsoft YaHei", 9))
        self.lbl_tts_status_title.grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        self.lbl_tts_status = tk.Label(
            self.settings_frame, text="准备就绪", fg="#8A0303", bg="#000000", font=("Microsoft YaHei", 9, "bold")
        )
        self.lbl_tts_status.grid(row=8, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 9. 界面语言选择 (Row 9)
        self.lbl_lang_title = tk.Label(self.settings_frame, text="界面与Saki语言:", fg="#666666", bg="#000000", font=("Microsoft YaHei", 9))
        self.lbl_lang_title.grid(row=9, column=0, sticky=tk.W, padx=10, pady=2)
        
        lang_frame = tk.Frame(self.settings_frame, bg="#000000")
        lang_frame.grid(row=9, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.rb_langs = []
        for idx, lang in enumerate(["中文", "English", "日本語"]):
            rb = tk.Radiobutton(
                lang_frame, text=lang, variable=self.selected_language, value=lang,
                bg="#000000", fg="#CC0000", activebackground="#0D0000", activeforeground="#FF0000",
                selectcolor="#000000", font=("Microsoft YaHei", 9), bd=0, highlightthickness=0,
                command=self._on_language_changed
            )
            rb.pack(side=tk.LEFT, padx=5)
            self.rb_langs.append(rb)
            
        self.settings_frame.columnconfigure(1, weight=1)
        
        self.canvas_ecg = tk.Canvas(self.root, bg="#000000", height=45, highlightthickness=0)
        self.canvas_ecg.pack(fill=tk.X, padx=10, pady=2)
        
        self.bottom_frame = tk.Frame(self.root, bg="#000000")
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.entry_input = tk.Entry(
            self.bottom_frame, bg="#050000", fg="#FF0000", insertbackground="#FF0000",
            relief=tk.SOLID, bd=1, highlightthickness=1,
            highlightcolor="#8A0303", highlightbackground="#222222",
            font=("Microsoft YaHei", 11)
        )
        self.entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.entry_input.bind("<Return>", lambda e: self._on_send())
        self.entry_input.focus_set()
        
        self.btn_send = tk.Button(
            self.bottom_frame, text="回应她", fg="#8A0303", bg="#000000",
            activeforeground="#FF0000", activebackground="#150000",
            relief=tk.SOLID, bd=1, highlightthickness=0,
            font=("Microsoft YaHei", 10, "bold"), width=10,
            command=self._on_send
        )
        self.btn_send.pack(side=tk.RIGHT, ipady=4)
        
        self.btn_send.bind("<Enter>", lambda e: self.btn_send.config(fg="#FF0000", highlightbackground="#FF0000", bg="#0D0000"))
        self.btn_send.bind("<Leave>", lambda e: self.btn_send.config(fg="#8A0303", highlightbackground="#444444", bg="#000000"))
 
        self.chat_frame = tk.Frame(self.root, bg="#000000")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_text = tk.Text(
            self.chat_frame, bg="#000000", fg="#CC0000",
            insertbackground="#FF0000", selectbackground="#3A0000", selectforeground="#FF0000",
            font=("Microsoft YaHei", 11), wrap=tk.WORD, bd=0, highlightthickness=0,
            spacing1=6, spacing2=4, spacing3=6
        )
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_text.config(state=tk.DISABLED)
        
        self.chat_text.tag_config("user", foreground="#FF0000", font=("Microsoft YaHei", 11, "bold"))
        self.chat_text.tag_config("saki", foreground="#CC0000")
        self.chat_text.tag_config("think", foreground="#7D5BA6", font=("Microsoft YaHei", 10, "italic"))
        self.chat_text.tag_config("system", foreground="#555555", font=("Consolas", 9, "italic"))
        self.chat_text.tag_config("glitch_large", font=("Microsoft YaHei", 24, "bold"), foreground="#FF0000")
        self.chat_text.tag_config("glitch_small", font=("Microsoft YaHei", 6), foreground="#550000")
        
        self.scrollbar = ttk.Scrollbar(self.chat_frame, orient="vertical", command=self.chat_text.yview, style="Vertical.TScrollbar")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=self.scrollbar.set)
        
        # 初始状态：如果有 API Key，则隐藏接口，否则展开方便填写
        if self.config.get("api_key"):
            self.top_bar.pack_forget()
            self.settings_frame.pack_forget()
            self.settings_visible = False
        else:
            self.top_bar.pack(fill=tk.X, padx=10, pady=5)
            self.settings_frame.pack(before=self.canvas_ecg, fill=tk.X, padx=10, pady=5)
            self.settings_visible = True
            self.btn_toggle_settings.config(text="[ 收起配置通道 ]", fg="#8A0303")
            
        # 根据默认语言初始化 UI 前台文本！
        self._update_ui_language()

    def _on_language_changed(self):
        # 标记用户进行了显式点击选择
        self.user_explicitly_selected_lang = True
        self.selected_language.set(normalize_language(self.selected_language.get()))
        
        # 保存持久化配置
        self.config["selected_language"] = self.selected_language.get()
        save_config(self.config)

        if self.chat_history:
            self.chat_history[0]["content"] = self._get_dynamic_system_prompt()
        
        # 执行界面全局热重构
        self._update_ui_language()

    def _update_ui_language(self):
        lang = normalize_language(self.selected_language.get())
        self.selected_language.set(lang)
        loc = LOCALIZATION[lang]
        
        # 1. 刷新天数标签
        self.lbl_day.config(text=loc["day"].format(day=self.current_day))
        
        # 2. 刷新状态栏三大属性标题
        self.lbl_favor_title.config(text=loc["favorability"])
        self.lbl_sus_title.config(text=loc["suspicion"])
        self.lbl_esc_title.config(text=loc["escape_rate"])
        
        # 3. 意识接口标题与折叠按钮
        self.lbl_title.config(text=loc["interface_title"])
        if self.settings_visible:
            self.btn_toggle_settings.config(text=loc["collapse_settings"])
        else:
            self.btn_toggle_settings.config(text=loc["expand_settings"])
            
        # 4. 配置表单左侧 Label 标题
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
        
        # 5. 配置表单交互按钮文字
        self.btn_browse_ref.config(text=loc["browse"])
        self.btn_browse_gpt.config(text=loc["browse"])
        self.btn_browse_sovits.config(text=loc["browse"])
        self.btn_load_gpt.config(text=loc["hot_load"])
        self.btn_load_sovits.config(text=loc["hot_load"])
        
        # 6. 回应按钮及加载提示状态
        if not self.is_typing:
            self.btn_send.config(text=loc["respond"])
        else:
            self.btn_send.config(text=loc["speaking"])
            
        # 7. 刷新各 PlaceholderEntry 的暗水印占位文字
        placeholders = {
            self.entry_key: "api_key_ph",
            self.entry_base: "api_base_ph",
            self.entry_model: "model_name_ph",
            self.entry_tts_url: "tts_base_ph",
            self.entry_refer_wav: "refer_audio_ph",
            self.entry_prompt_text: "refer_text_ph",
            self.entry_gpt_weights: "gpt_model_ph",
            self.entry_sovits_weights: "sovits_model_ph"
        }
        
        # 为 PlaceholderEntry 补充多语言水印条目
        ph_strings = {
            "中文": {
                "api_key_ph": "在此输入你的 API Key",
                "api_base_ph": "默认: https://api.deepseek.com",
                "model_name_ph": "默认: deepseek-v4-flash",
                "tts_base_ph": "默认: http://127.0.0.1:9880",
                "refer_audio_ph": "选择参考音频 (.wav)",
                "refer_text_ph": "在此输入参考音频对应的中文文字内容",
                "gpt_model_ph": "选择 GPT 模型权重 (.ckpt)",
                "sovits_model_ph": "选择 SoVITS 模型权重 (.pth)"
            },
            "English": {
                "api_key_ph": "Enter your API Key here...",
                "api_base_ph": "Default: https://api.deepseek.com",
                "model_name_ph": "Default: deepseek-v4-flash",
                "tts_base_ph": "Default: http://127.0.0.1:9880",
                "refer_audio_ph": "Select reference WAV file (.wav)",
                "refer_text_ph": "Enter reference audio transcription here...",
                "gpt_model_ph": "Select GPT weights (.ckpt)",
                "sovits_model_ph": "Select SoVITS weights (.pth)"
            },
            "日本語": {
                "api_key_ph": "ここにAPIキーを入力してください...",
                "api_base_ph": "デフォルト: https://api.deepseek.com",
                "model_name_ph": "デフォルト: deepseek-v4-flash",
                "tts_base_ph": "デフォルト: http://127.0.0.1:9880",
                "refer_audio_ph": "参考音声ファイルを選択 (.wav)",
                "refer_text_ph": "参考音声に対応するテキストを入力...",
                "gpt_model_ph": "GPTの重みファイルを選択 (.ckpt)",
                "sovits_model_ph": "SoVITSの重みファイルを選択 (.pth)"
            }
        }
        
        for entry, ph_key in placeholders.items():
            entry.update_placeholder(ph_strings[lang][ph_key])
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
            # 触发面板炫酷淡入过渡动画
            self._animate_panel_fade_in()

    def _on_window_resized(self, event=None):
        if event and str(event.widget) != ".":
            return
        if self.game_over:
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
            if hasattr(self, 'anti_escape_frame') and self.anti_escape_frame.winfo_exists():
                return
            self.entry_input.config(state=tk.DISABLED)
            self.btn_send.config(state=tk.DISABLED)
            
            self.anti_escape_frame = tk.Frame(self.root, bg="#1A0000")
            self.anti_escape_frame.place(x=0, y=0, relwidth=1, relheight=1)
            self.anti_escape_frame.lift()
            
            lbl_warning = tk.Label(
                self.anti_escape_frame, 
                text=LOCALIZATION[normalize_language(self.selected_language.get())]["anti_escape"],
                fg="#FF0000", bg="#1A0000",
                font=("Microsoft YaHei", 16, "bold"),
                justify=tk.CENTER
            )
            lbl_warning.pack(expand=True)
            
            def pulse_text(state=0):
                if not hasattr(self, 'anti_escape_frame') or not self.anti_escape_frame.winfo_exists():
                    return
                colors = ["#FF0000", "#CC0000", "#990000", "#660000", "#990000", "#CC0000"]
                lbl_warning.config(fg=colors[state % len(colors)])
                self.root.after(200, lambda: pulse_text(state + 1))
                
            pulse_text()
        else:
            if hasattr(self, 'anti_escape_frame') and self.anti_escape_frame.winfo_exists():
                self.anti_escape_frame.destroy()
                if hasattr(self, 'anti_escape_frame'):
                    delattr(self, 'anti_escape_frame')
                
                if not self.is_typing and not self.game_over:
                    self.entry_input.config(state=tk.NORMAL)
                    self.btn_send.config(state=tk.NORMAL)
                    self.entry_input.focus_set()

    def _start_ecg_animation(self):
        def update_ecg():
            self.ecg_time += 0.035
            self.canvas_ecg.delete("all")
            
            # 动态获取当前画布的实际物理宽度，并做防空保护
            width = self.canvas_ecg.winfo_width()
            if width <= 200:
                width = 1100
                
            height = 45
            points = []
            num_points = 300
            dx = width / num_points
            
            susp = self.suspicion
            is_frenzy = self.shaking or getattr(self, 'ecg_frenzy', False)
            is_think_jitter = getattr(self, 'think_jitter', False)
            
            if is_frenzy:
                period = 0.35
                color_main = "#FF0000"
                color_mid = "#FF3333"
                color_fade = "#7A0000"
                amplitude_scale = 1.4
                jitter_range = 8.5
            elif is_think_jitter:
                period = 0.8
                color_main = "#9E0000"
                color_mid = "#540000"
                color_fade = "#2A0000"
                amplitude_scale = 0.5
                jitter_range = 1.8
            else:
                period = 1.4 - 0.9 * (susp / 100.0)
                if susp < 30:
                    color_main = "#8A0303"
                    color_mid = "#500000"
                    color_fade = "#200000"
                    amplitude_scale = 0.75
                    jitter_range = 0.0
                elif susp < 75:
                    color_main = "#CC0000"
                    color_mid = "#8A0303"
                    color_fade = "#400000"
                    amplitude_scale = 1.0
                    jitter_range = 1.2
                else:
                    color_main = "#FF0000"
                    color_mid = "#CC0000"
                    color_fade = "#600000"
                    amplitude_scale = 1.25
                    jitter_range = 4.2
            
            grid_color = "#0B0000" if susp < 50 else "#150000"
            for grid_x in range(0, width, 40):
                self.canvas_ecg.create_line(grid_x, 0, grid_x, height, fill=grid_color, width=1)
            for grid_y in range(0, height, 15):
                self.canvas_ecg.create_line(0, grid_y, width, grid_y, fill=grid_color, width=1)
            
            points.clear()
            for idx in range(num_points):
                x = idx * dx
                t_val = (self.ecg_time + (idx * 0.015)) % period
                y_baseline = height / 2
                
                tp = t_val / period
                y = y_baseline
                
                if getattr(self, 'ecg_flatline_active', False):
                    # ECG 绝望平线特效
                    pass
                else:
                    if 0.0 <= tp < 0.06:
                        y = y_baseline - 3.5 * math.sin(math.pi * tp / 0.06) * amplitude_scale
                    elif 0.12 <= tp < 0.15:
                        y = y_baseline + 5.0 * ((tp - 0.12) / 0.03) * amplitude_scale
                    elif 0.15 <= tp < 0.20:
                        y = (y_baseline + 5.0 * amplitude_scale) - 35.0 * ((tp - 0.15) / 0.05) * amplitude_scale
                    elif 0.20 <= tp < 0.25:
                        y = (y_baseline - 30.0 * amplitude_scale) + 38.0 * ((tp - 0.20) / 0.05) * amplitude_scale
                    elif 0.25 <= tp < 0.28:
                        y = (y_baseline + 8.0 * amplitude_scale) - 8.0 * ((tp - 0.25) / 0.03) * amplitude_scale
                    elif 0.38 <= tp < 0.55:
                        y = y_baseline - 6.5 * math.sin(math.pi * (tp - 0.38) / 0.17) * amplitude_scale
                
                if jitter_range > 0 and not getattr(self, 'ecg_flatline_active', False):
                    y += random.uniform(-jitter_range, jitter_range)
                    
                points.append((x, y))
            
            for p_idx in range(len(points) - 1):
                x1, y1 = points[p_idx]
                x2, y2 = points[p_idx + 1]
                
                alpha_ratio = p_idx / len(points)
                if alpha_ratio > 0.85:
                    c = color_main
                    w = 6 if is_frenzy else (2 if susp > 70 else 1)
                elif alpha_ratio > 0.6:
                    c = color_mid
                    w = 3 if is_frenzy else 1
                else:
                    c = color_fade
                    w = 2 if is_frenzy else 1
                    
                self.canvas_ecg.create_line(x1, y1, x2, y2, fill=c, width=w)
            
            last_x, last_y = points[-1]
            glow_radius = 2.5 if int(self.ecg_time * 5) % 2 == 0 else 1.0
            self.canvas_ecg.create_oval(
                last_x - glow_radius, last_y - glow_radius,
                last_x + glow_radius, last_y + glow_radius,
                fill=color_main, outline=""
            )
            
            # 画布物理视觉层特效叠加
            if getattr(self, 'dripping_blood_active', False):
                for line in getattr(self, 'dripping_blood_lines', []):
                    line["y"] += line["speed"]
                    self.canvas_ecg.create_line(line["x"], 0, line["x"], line["y"], fill="#FF0000", width=2)
                    
            if getattr(self, 'scanlines_active', False):
                for _ in range(12):
                    scan_y = random.randint(2, height - 2)
                    self.canvas_ecg.create_line(0, scan_y, width, scan_y, fill="#FF0000", width=random.randint(1, 4))
                    
            if getattr(self, 'snow_noise_active', False):
                for _ in range(60):
                    rx = random.randint(0, width)
                    ry = random.randint(0, height)
                    self.canvas_ecg.create_oval(rx-1, ry-1, rx+1, ry+1, fill="#FF2222", outline="")
                    
            if getattr(self, 'fake_error_active', False):
                self.canvas_ecg.create_rectangle(width/2 - 120, 5, width/2 + 120, height - 5, fill="#1A0000", outline="#FF0000", width=2)
                self.canvas_ecg.create_text(width/2, height/2, text="FATAL ERROR: HEART OVERLOAD", fill="#FF0000", font=("Consolas", 10, "bold"))
                
            self.root.after(30, update_ecg)
            
        update_ecg()

    def _init_and_play_audio(self):
        if not HAS_PYGAME:
            print("[警告] 未检测到 pygame 库，背景音效将被静默。")
            self._write_chat_log("[系统通知] 缺少音频驱动依赖，游戏已切换至极致静音模式……", "system")
            return
            
        def audio_thread_worker():
            audio_file = "heartbeat.wav"
            if not os.path.exists("heartbeat.mp3") and not os.path.exists("heartbeat.wav"):
                try:
                    generate_heartbeat_wav("heartbeat.wav")
                except Exception as ex:
                    print(f"[系统] 合成音频失败: {ex}")
                    return
            
            if os.path.exists("heartbeat.mp3"):
                audio_file = "heartbeat.mp3"
                
            try:
                pygame.mixer.init()
                # 使用 Sound 对象播放低频背景心跳，循环播放并获取独立的音轨通道
                self.heartbeat_sound = pygame.mixer.Sound(audio_file)
                self.heartbeat_channel = self.heartbeat_sound.play(-1)
                self.heartbeat_channel.set_volume(0.8)
            except Exception as ex:
                print(f"[系统] 播放心跳发生异常: {ex}")
                
        audio_thread = threading.Thread(target=audio_thread_worker, daemon=True)
        audio_thread.start()

    def _play_voice_synchronously(self, spoken_text, session_id):
        """
        在后台打字机线程中同步请求并播放语音，播放完毕才退出。
        使用 pygame.mixer.Sound 播放，提供极高的解码兼容性，解决各种采样率的音频自动重采样和 Windows 文件句柄锁定的痛点。
        """
        if not HAS_PYGAME or not HAS_REQUESTS:
            return
            
        if session_id != self.dialogue_session_id:
            return
            
        cleaned_text = clean_text_for_tts(spoken_text)
        if not cleaned_text:
            print("[同步语音合成跳过] 文本清洗后为空值")
            return
            
        selected_lang = normalize_language(self.selected_language.get())
        target_lang_code = language_to_tts_code(selected_lang)

        ref_lang = detect_language(self.prompt_text)
        prompt_lang_code = language_to_tts_code(ref_lang)

        temp_file = None
        try:
            params = build_tts_request_params(
                self.refer_wav_path,
                self.prompt_text,
                prompt_lang_code,
                cleaned_text,
                target_lang_code,
                quality=True,
            )
            
            # 使用启动时探测好的唯一锁定端点，绝不重复轰炸单线程服务端
            target_url = f"{self.gpt_sovits_url.rstrip('/')}{self.working_endpoint}"
            
            if session_id != self.dialogue_session_id:
                return
                
            print(
                f"[自愈系统] 正在发起高质量语音合成: {target_url} "
                f"lang={target_lang_code}, ref_lang={prompt_lang_code}, text={cleaned_text}"
            )
            res = requests.get(target_url, params=params, timeout=15, proxies={"http": None, "https": None})

            if res is not None and res.status_code in (400, 404, 405, 422, 500):
                fallback_params = build_tts_request_params(
                    self.refer_wav_path,
                    self.prompt_text,
                    prompt_lang_code,
                    cleaned_text,
                    target_lang_code,
                    quality=False,
                )
                print(f"[自愈系统] 高质量参数不兼容，降级为基础参数重试: HTTP {res.status_code}")
                res = requests.get(target_url, params=fallback_params, timeout=15, proxies={"http": None, "https": None})
            
            if session_id != self.dialogue_session_id:
                return
                
            if res and res.status_code == 200 and len(res.content) > 1000:
                temp_file = f"temp_saki_{int(time.time()*1000)}.wav"
                with open(temp_file, "wb") as f:
                    f.write(res.content)
                    
                try:
                    if session_id != self.dialogue_session_id:
                        return
                        
                    # 压低心跳声音量，为纱希的配音让路
                    if hasattr(self, 'heartbeat_channel') and self.heartbeat_channel:
                        self.heartbeat_channel.set_volume(0.15)
                        
                    # 停止当前可能存在的音乐播放，防止声轨冲突
                    pygame.mixer.music.stop()
                    
                    # 100% 健壮的 Sound 播放：Sound 对象在构造时会立即读完整个文件并在内存中完成自动重采样
                    # 这样就彻底关闭了文件句柄，允许我们立即执行删除，完全规避 Windows 文件句柄占用导致清理失败 of the bug
                    voice_sound = pygame.mixer.Sound(temp_file)
                    self.voice_channel = voice_sound.play()
                    voice_channel = self.voice_channel
                    
                    # 立即删除临时文件以实现绝对干净的清理，完全无惧 Windows 文件锁
                    try:
                        os.remove(temp_file)
                        print(f"[自愈系统] 临时语音已读入内存并提前清理: {temp_file}")
                        temp_file = None  # 标记已删除
                    except Exception as rm_err:
                        pass
                    
                    # 后台同步阻塞，等待本句语音彻底播完才解禁输入
                    while voice_channel.get_busy() and not self.game_over:
                        if session_id != self.dialogue_session_id:
                            # 立即掐断老声音
                            voice_channel.stop()
                            return
                        time.sleep(0.1)
                        
                    # 恢复背景心跳音量
                    if hasattr(self, 'heartbeat_channel') and self.heartbeat_channel and not self.game_over:
                        self.heartbeat_channel.set_volume(0.8)
                except Exception as play_err:
                    print(f"[同步语音播放失败] {play_err}")
                    if hasattr(self, 'heartbeat_channel') and self.heartbeat_channel and not self.game_over:
                        self.heartbeat_channel.set_volume(0.8)
            else:
                if res is not None:
                    print(f"[同步语音合成失败] 状态码: {res.status_code}, 内容大小: {len(res.content)}")
                else:
                    print("[同步语音合成失败] 无法连通 GPT-SoVITS 服务器")
        except Exception as ex:
            print(f"[同步语音合成跳过] GPT-SoVITS 运行异常: {ex}")
        finally:
            if temp_file and os.path.exists(temp_file):
                # 兜底清理（如果上面提前删除失败了）
                for _ in range(5):
                    try:
                        os.remove(temp_file)
                        print(f"[自愈系统] 兜底清理本次临时语音文件: {temp_file}")
                        break
                    except:
                        time.sleep(0.1)

    def _on_send(self):
        if self.is_typing or self.game_over:
            return
            
        user_text = self.entry_input.get().strip()
        if not user_text:
            return
            
        # 1. 第一句话语言探测与自适应
        if not self.first_msg_detected:
            self.first_msg_detected = True
            if not self.user_explicitly_selected_lang:
                detected_lang = detect_language(user_text, normalize_language(self.selected_language.get()))
                self.selected_language.set(detected_lang)
                self.config["selected_language"] = detected_lang
                save_config(self.config)
                self._update_ui_language()

        # 清除上一轮产生的重叠文本 carnage labels，保证下一轮排版干净
        if hasattr(self, 'carnage_labels') and self.carnage_labels:
            for lbl in self.carnage_labels:
                try: lbl.destroy()
                except: pass
            self.carnage_labels.clear()
            
        # 递增会话，掐断旧线程的残留语音和渲染
        self.dialogue_session_id += 1
            
        self.last_user_input = user_text  # 记录玩家最后一次输入，用于数值自愈逻辑分析
        self.entry_input.delete(0, tk.END)
        
        lang = normalize_language(self.selected_language.get())
        user_prefix = LOCALIZATION[lang]["user_prefix"]
        self._write_chat_log(f"{user_prefix}{user_text}\n", "user")
        self.chat_history.append({"role": "user", "content": user_text})
        
        # 保存当前所有配置（包含 API 与语音配置）到配置文件中
        self._save_all_settings()
        api_key = self.entry_key.get_actual_value()
        
        # 保存 API 配置后自动收起接口，保持主窗体洁净
        if api_key:
            self.top_bar.pack_forget()
            self.settings_frame.pack_forget()
            self.settings_visible = False
        
        self.chat_history[0]["content"] = self._get_dynamic_system_prompt()
        self._set_typing_state(True)
        
        api_thread = threading.Thread(target=self._async_fetch_api_response, args=(user_text, self.cycle_id), daemon=True)
        api_thread.start()

    def _browse_refer_wav(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="选择参考音频", 
            filetypes=[("WAV Audio", "*.wav")]
        )
        if filepath:
            self.entry_refer_wav.delete(0, tk.END)
            self.entry_refer_wav.insert(0, filepath)
            self.entry_refer_wav.config(fg="#FF0000")
            self.refer_wav_path = filepath
            self._save_all_settings()

    def _browse_gpt_weights(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="选择 GPT 模型权重", 
            filetypes=[("GPT Weights", "*.ckpt")]
        )
        if filepath:
            self.entry_gpt_weights.delete(0, tk.END)
            self.entry_gpt_weights.insert(0, filepath)
            self.entry_gpt_weights.config(fg="#FF0000")
            self.gpt_weights_path = filepath
            self._save_all_settings()

    def _browse_sovits_weights(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="选择 SoVITS 模型权重", 
            filetypes=[("SoVITS Weights", "*.pth")]
        )
        if filepath:
            self.entry_sovits_weights.delete(0, tk.END)
            self.entry_sovits_weights.insert(0, filepath)
            self.entry_sovits_weights.config(fg="#FF0000")
            self.sovits_weights_path = filepath
            self._save_all_settings()

    def _save_all_settings(self):
        api_key = self.entry_key.get_actual_value()
        base_url = self.entry_base.get_actual_value() or "https://api.deepseek.com"
        model_name = self.entry_model.get_actual_value() or "deepseek-v4-flash"
        
        self.gpt_sovits_url = self.entry_tts_url.get_actual_value() or "http://127.0.0.1:9880"
        self.refer_wav_path = self.entry_refer_wav.get_actual_value() or "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav"
        self.prompt_text = self.entry_prompt_text.get_actual_value() or "独向昭谈至恶龙一阁著文章。"
        self.gpt_weights_path = self.entry_gpt_weights.get_actual_value() or ""
        self.sovits_weights_path = self.entry_sovits_weights.get_actual_value() or ""
        
        self.config.update({
            "api_key": api_key,
            "api_base": base_url,
            "model_name": model_name,
            "gpt_sovits_url": self.gpt_sovits_url,
            "refer_wav_path": self.refer_wav_path,
            "prompt_text": self.prompt_text,
            "gpt_weights_path": self.gpt_weights_path,
            "sovits_weights_path": self.sovits_weights_path,
            "selected_language": normalize_language(self.selected_language.get())
        })
        save_config(self.config)

    def _async_load_weights(self, weight_type, filepath):
        loc = LOCALIZATION[normalize_language(self.selected_language.get())]
        if not filepath:
            self.lbl_tts_status.config(text=loc["voice_fail_empty"], fg="#FF0000")
            return
            
        self.lbl_tts_status.config(text=loc["voice_loading"], fg="#FFD700")
        
        def loader():
            url = self.gpt_sovits_url.rstrip('/')
            if weight_type == "gpt":
                target_url = f"{url}/set_gpt_weights"
                params = {"weights_path": filepath}
            else:
                target_url = f"{url}/set_sovits_weights"
                params = {"weights_path": filepath}
                
            try:
                print(f"[自愈系统] 发送模型加载请求: {target_url} 路径: {filepath}")
                res = requests.get(target_url, params=params, timeout=12, proxies={"http": None, "https": None})
                if res.status_code == 200:
                    msg = "GPT 加载成功" if weight_type == "gpt" else "SoVITS 加载成功"
                    self._queue_ui("TTS_STATUS_UPDATE", (msg, "#2ECC71"))
                else:
                    self._queue_ui("TTS_STATUS_UPDATE", (f"加载失败: {res.status_code}", "#FF0000"))
            except Exception as e:
                print(f"[自愈系统] 连接 TTS 权重接口出错: {e}")
                self._queue_ui("TTS_STATUS_UPDATE", ("连接失败", "#FF0000"))
                
        threading.Thread(target=loader, daemon=True).start()

    def _probe_tts_endpoint(self):
        """在后台线程中探测可用端点，锁定唯一可用地址，解决单线程并发轰炸导致不发声/超时的痛点"""
        if not HAS_REQUESTS:
            return
            
        def prober():
            url = self.gpt_sovits_url.rstrip('/')
            endpoints = ["/tts", "/tts_to_audio", ""]
            
            ref_lang = detect_language(self.prompt_text)
            prompt_lang_code = language_to_tts_code(ref_lang)
            params = build_tts_request_params(
                self.refer_wav_path,
                self.prompt_text,
                prompt_lang_code,
                "你好",
                "zh",
                quality=False,
            )
            for ep in endpoints:
                target_url = f"{url}{ep}"
                try:
                    res = requests.get(target_url, params=params, timeout=2.5, proxies={"http": None, "https": None})
                    if res.status_code == 200:
                        self.working_endpoint = ep
                        print(f"[自愈系统] 探测成功！当前可用语音端点锁定为: {target_url}")
                        return
                except:
                    pass
            # 兜底默认
            self.working_endpoint = "/tts"
            print("[自愈系统] 探测结束，未发现活动端点，默认选择: /tts")
            
        threading.Thread(target=prober, daemon=True).start()

    def _clean_orphaned_temp_files(self):
        """启动时自动扫描同级目录，清空历史遗留下来的 temp_saki_*.wav 临时音频文件"""
        try:
            for file in os.listdir("."):
                if file.startswith("temp_saki_") and file.endswith(".wav"):
                    try:
                        os.remove(file)
                        print(f"[系统自愈] 成功清理历史残留临时语音: {file}")
                    except Exception as e:
                        print(f"[系统自愈] 释放残留语音 {file} 失败: {e}")
        except Exception as err:
            print(f"[系统自愈] 自动大扫除服务发生异常: {err}")

    def _write_chat_log(self, text, tag):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text, tag)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _set_typing_state(self, is_typing):
        self.is_typing = is_typing
        loc = LOCALIZATION[normalize_language(self.selected_language.get())]
        if not hasattr(self, 'anti_escape_frame'):
            if is_typing:
                self.entry_input.config(state=tk.DISABLED)
                self.btn_send.config(state=tk.DISABLED, text=loc["speaking"])
                self.root.config(cursor="watch")
            else:
                self.entry_input.config(state=tk.NORMAL)
                self.btn_send.config(state=tk.NORMAL, text=loc["respond"])
                self.root.config(cursor="")
                self.entry_input.focus_set()

    def _async_fetch_api_response(self, last_user_input, cycle_id):
        if cycle_id != self.cycle_id:
            return
        api_key = self.entry_key.get_actual_value()
        base_url = self.entry_base.get_actual_value() or "https://api.deepseek.com"
        model_name = self.entry_model.get_actual_value() or "deepseek-v4-flash"
        
        if not api_key:
            time.sleep(random.uniform(0.6, 1.2))
            if cycle_id != self.cycle_id:
                return
            mock_reply = self._generate_mock_reply(last_user_input)
            self._queue_ui("API_MOCK", mock_reply, cycle_id)
            return

        if not HAS_REQUESTS:
            self._queue_ui("API_ERROR", "缺失 requests 依赖包，请通过 pip install requests 进行安装。", cycle_id)
            return
            
        try:
            url = f"{base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_name,
                "messages": self.chat_history,
                "temperature": 0.95
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=25, proxies={"http": None, "https": None})
            except Exception as conn_err:
                err_str = str(conn_err).lower()
                if "proxy" in err_str or "proxyerror" in err_str:
                    print("[自愈系统] 检测到系统代理故障，正强制直连直达 DeepSeek 服务端...")
                    response = requests.post(url, headers=headers, json=payload, timeout=25, proxies={"http": None, "https": None})
                else:
                    raise conn_err
                    
            if response.status_code == 200:
                if cycle_id != self.cycle_id:
                    return
                result_json = response.json()
                reply = result_json["choices"][0]["message"]["content"]
                self._queue_ui("API_SUCCESS", reply, cycle_id)
            else:
                raise Exception(f"HTTP 状态码: {response.status_code}, 内容: {response.text}")
                
        except Exception as err:
            print(f"[API请求出错] {err}")
            time.sleep(0.5)
            if cycle_id != self.cycle_id:
                return
            self._queue_ui("API_FALLBACK", (last_user_input, str(err)), cycle_id)

    def _generate_mock_reply(self, user_input):
        lang = normalize_language(self.selected_language.get())
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
            reply += build_offline_translation_line(intent["name"], user_lang)

        suffix = LANGUAGE_PROFILES[lang]["fallback_suffix"].format(
            delta_f=delta_f,
            delta_s=delta_s,
            delta_e=delta_e,
        )
        return f"{reply}{suffix}"

    def _update_game_stats(self, delta_data):
        if self.game_over:
            return
            
        df = delta_data.get("favorability", 0)
        ds = delta_data.get("suspicion", 0)
        de = delta_data.get("escape_rate", 0)
        
        self.favorability = max(0, min(100, self.favorability + df))
        self.suspicion = max(0, min(100, self.suspicion + ds))
        self.escape_rate = max(0, min(100, self.escape_rate + de))
        
        self.bar_favor['value'] = self.favorability
        self.bar_sus['value'] = self.suspicion
        self.bar_esc['value'] = self.escape_rate
        
        self.lbl_favor_val.config(text=f"{self.favorability}")
        self.lbl_sus_val.config(text=f"{self.suspicion}")
        self.lbl_esc_val.config(text=f"{self.escape_rate}%")
        
        print(f"[数值变动] 好感: {df:+d} -> {self.favorability}, 疑心: {ds:+d} -> {self.suspicion}, 逃脱: {de:+d} -> {self.escape_rate}%")
        
        # 【AI结局接管核心】若 AI 声明 "game_over": true，暂存结局，等语音播完再弹出
        is_ai_game_over = delta_data.get("game_over")
        if is_ai_game_over in [True, "True", "true", "1", 1]:
            ai_type = delta_data.get("ending_type", "bad")
            ai_title = delta_data.get("ending_title", "")
            ai_story = delta_data.get("ending_story", "")
            print(f"[AI结局宣告] 类型: {ai_type}, 标题: {ai_title}")
            self.pending_ending = {
                "ending_type": ai_type,
                "ending_title": ai_title,
                "ending_story": ai_story,
            }
            self.game_over = True
            return

        self._check_endings(force_final=False)

    def _on_dialogue_completed(self):
        if self.game_over:
            return
            
        self.dialogue_count += 1
        if self.dialogue_count >= 3:
            self.dialogue_count = 0
            self.current_day += 1
            
            # 让天数无限延伸下去，不再限制五天！
            lang = normalize_language(self.selected_language.get())
            loc = LOCALIZATION[lang]
            self.lbl_day.config(text=loc["day"].format(day=self.current_day))
            self._write_chat_log(loc["sys_day_transition"].format(day=self.current_day), "system")
            self._start_physical_shake()

    def _check_endings(self, force_final=False):
        if self.game_over:
            return
        if self.suspicion >= 96:
            self.pending_ending = {"ending_type": "bad"}
            self.game_over = True
            return
        if self.favorability <= -25:
            self.pending_ending = {"ending_type": "bad"}
            self.game_over = True
            return

    def _show_ending_overlay(self, final_text):
        """TTS finished, now show the ending screen. final_text is Saki's last words."""
        if hasattr(self, 'overlay') and self.overlay.winfo_exists():
            return

        self._set_typing_state(True)
        self.entry_input.config(state=tk.DISABLED)
        self.btn_send.config(state=tk.DISABLED)

        ending_info = self.pending_ending or {}
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
            self.overlay, text=title,
            fg=color, bg="#000000",
            font=("Microsoft YaHei", 16, "bold"), wraplength=520
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
            self.overlay, text=story,
            fg="#DDDDDD", bg="#000000", font=("Microsoft YaHei", 10),
            justify=tk.LEFT, anchor=tk.W, wraplength=520
        )
        lbl_story.pack(pady=15, padx=40)

        btn_restart = tk.Button(
            self.overlay, text=LOCALIZATION[lang]["restart_btn"], fg="#FFFFFF", bg="#8A0303",
            activeforeground="#FF0000", activebackground="#200000",
            relief=tk.SOLID, bd=1, font=("Microsoft YaHei", 11, "bold"),
            command=self._restart_game
        )
        btn_restart.pack(pady=(20, 0), ipadx=20, ipady=6)

    def _restart_game(self):
        self.cycle_id += 1
        self.dialogue_session_id += 1
        self._clear_ui_queue()
        self.pending_ending = None

        if hasattr(self, 'overlay') and self.overlay.winfo_exists():
            self.overlay.destroy()

        # 清理程序化特效叠加层
        self.overlay_mgr.hide()

        # 重置所有心理恐怖状态
        self.mouse_pull_active = False
        self.meltdown_active = False
        self.barrage_active = False
        self.psychic_strobe_active = False
        self.ecg_flatline_active = False
        self.dripping_blood_active = False
        self.scanlines_active = False
        self.snow_noise_active = False
        self.fake_error_active = False
        self.glitch_rune_active = False
        self.glitch_font_shake_active = False
        self.typewriter_speed_mult = 1.0
        
        # 清除重叠文本 carnage labels
        if hasattr(self, 'carnage_labels') and self.carnage_labels:
            for lbl in self.carnage_labels:
                try: lbl.destroy()
                except: pass
            self.carnage_labels.clear()
            
        # 重新开启全新轮回：彻底掐断上一世正在播放的一切发声，重新激活新一世的心跳！
        if HAS_PYGAME:
            try:
                pygame.mixer.stop()
                pygame.mixer.music.stop()
                # 重新载入并播放干净的新心跳背景声，开启新一世轮回！
                if hasattr(self, 'heartbeat_sound') and self.heartbeat_sound:
                    self.heartbeat_channel = self.heartbeat_sound.play(-1)
                    self.heartbeat_channel.set_volume(0.8)
            except Exception as restart_err:
                print(f"[重启混音器中止异常] {restart_err}")
            
        self.current_day = 1
        self.dialogue_count = 0
        self.favorability = 50
        self.suspicion = 20
        self.escape_rate = 0
        self.game_over = False
        self.ecg_frenzy = False
        self.think_jitter = False
        self.mouse_tremor_active = False
        self.first_msg_detected = False
        self.last_user_input = ""
        
        self.bar_favor['value'] = self.favorability
        self.bar_sus['value'] = self.suspicion
        self.bar_esc['value'] = self.escape_rate
        
        self.lbl_favor_val.config(text=f"{self.favorability}")
        self.lbl_sus_val.config(text=f"{self.suspicion}")
        self.lbl_esc_val.config(text=f"{self.escape_rate}%")
        
        lang = normalize_language(self.selected_language.get())
        self.lbl_day.config(text=LOCALIZATION[lang]["day"].format(day=self.current_day))
        
        self.chat_history = [{"role": "system", "content": self._get_dynamic_system_prompt()}]
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        self._set_typing_state(False)

        # 重启程序化视觉特效循环
        self._start_border_pulse_loop()

        restart_cycle = self.cycle_id
        self.root.after(
            500,
            lambda cycle=restart_cycle: (
                self._enqueue_saki_response(INITIAL_GREETINGS[normalize_language(self.selected_language.get())])
                if cycle == self.cycle_id and not self.game_over
                else None
            ),
        )

    def _start_typewriter_effect(self, think_text, spoken_text):
        self.dialogue_session_id += 1
        current_session = self.dialogue_session_id
        current_cycle = self.cycle_id
        
        lang = normalize_language(self.selected_language.get())
        think_prefix = LOCALIZATION[lang]["think_prefix"]
        think_suffix = LOCALIZATION[lang]["think_suffix"]
        saki_prefix = LOCALIZATION[lang]["saki_prefix"]

        def typewriter_worker():
            selected_lang = normalize_language(self.selected_language.get())
            user_lang = detect_language(getattr(self, 'last_user_input', ""), selected_lang)
            visual_text = strip_terminal_parenthetical_translation(spoken_text, user_lang) or spoken_text
            contains_danger = any(word in visual_text for word in self.danger_words)
            shaked = False
            
            if contains_danger:
                self.ecg_frenzy = True
                
            time.sleep(0.2)
            
            if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                return
                
            if think_text:
                self.think_jitter = True
                self._queue_ui("CHAR_RENDER_THINK", think_prefix, current_cycle)
                for char in think_text:
                    if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                        return
                    self._queue_ui("CHAR_RENDER_THINK", char, current_cycle)
                    delay = random.uniform(0.015, 0.04)
                    if char in "，。…？！,.;!?":
                        delay += 0.15
                    time.sleep(delay)
                self._queue_ui("CHAR_RENDER_THINK", think_suffix, current_cycle)
                self.think_jitter = False
                time.sleep(0.4) # Dead silence intermission pause before spoken text
            
            if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                return
                
            # Expanded threatening keywords (including forever, escape, you are mine, etc.)
            danger_words_carnage = ["小刀", "滚", "锁", "洗澡", "地下室", "老子", "永远", "看着我", "你是我的", "🔪", "🩸", 
                                    "forever", "escape", "look at me", "you are mine", "見て", "逃げられない"]
            use_carnage = (self.suspicion >= 60) or any(w in visual_text.lower() for w in danger_words_carnage)
            
            if use_carnage:
                # 产生 30% 的乱码文本
                runes = ["☠", "☣", "⛥", "🩸", "🕇", "👹", "🔪", "⛓", "🖤", "⚰", "━", "..", "？"]
                polluted_list = []
                for char in visual_text:
                    polluted_list.append(char)
                    if random.random() < 0.30:
                        polluted_list.append(random.choice(runes))
                polluted_text = "".join(polluted_list)
                
                # 触发心理恐怖视觉异常干扰，拉满惊悚氛围
                self._queue_ui("TRIGGER_STROBE", None, current_cycle)
                self._queue_ui("TRIGGER_BARRAGE", 1.0, current_cycle)
                self._queue_ui("TRIGGER_MELT_OVERLAY", None, current_cycle)
                self._queue_ui("TRIGGER_MOUSE_TREMOR", None, current_cycle)
                self._queue_ui("TRIGGER_FAKE_ERROR", None, current_cycle)
                self._queue_ui("TRIGGER_MELTDOWN", None, current_cycle)
                self._queue_ui("TRIGGER_MOUSE_PULL", None, current_cycle)
                self._queue_ui("TRIGGER_SHAKE", None, current_cycle)
                
                if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                    return
                    
                # 使用绝对定位重叠渲染
                self._queue_ui("CHAR_RENDER_CARNAGE", polluted_text, current_cycle)
                translation_line = extract_terminal_parenthetical_translation(spoken_text, user_lang)
                if translation_line:
                    self._queue_ui("CHAR_RENDER", f"\n{translation_line}\n", current_cycle)
                time.sleep(len(visual_text) * 0.08)
            else:
                self._queue_ui("CHAR_RENDER", saki_prefix, current_cycle)
                
                for idx, char in enumerate(spoken_text):
                    if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                        return
                    # 1. 字号高频抖动
                    if getattr(self, 'glitch_font_shake_active', False) and random.random() < 0.12:
                        tag_to_use = random.choice(["glitch_large", "glitch_small"])
                        self._queue_ui("CHAR_RENDER_TAGGED", (char, tag_to_use), current_cycle)
                    else:
                        self._queue_ui("CHAR_RENDER", char, current_cycle)
                    
                    if contains_danger and not shaked:
                        current_sub = spoken_text[:idx+1]
                        if any(word in current_sub for word in self.danger_words):
                            self._queue_ui("TRIGGER_SHAKE", None, current_cycle)
                            self._queue_ui("TRIGGER_GLITCH", None, current_cycle) # 危险词触发视觉异常
                            if random.random() < 0.4:
                                self._queue_ui("TRIGGER_STROBE", None, current_cycle)
                            if random.random() < 0.3:
                                self._queue_ui("TRIGGER_FAKE_ERROR", None, current_cycle)
                            shaked = True
                    
                    # 3. 精神失控打字速度抖动
                    speed_mult = getattr(self, 'typewriter_speed_mult', 1.0)
                    delay = random.uniform(0.04, 0.12) * speed_mult
                    if char in "，。…？！,.;!?":
                        delay += 0.30 * speed_mult
                        
                    time.sleep(delay)
                    
                self._queue_ui("CHAR_RENDER", "\n", current_cycle)
            
            if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                return
                
            # 同步合成并播放语音，播放完毕后才发送 RENDER_DONE 解锁输入框！
            self._play_voice_synchronously(spoken_text, current_session)
            
            if current_session != self.dialogue_session_id or current_cycle != self.cycle_id:
                return
                
            self._queue_ui("RENDER_DONE", spoken_text, current_cycle)
            self.ecg_frenzy = False
            
        thread_typewriter = threading.Thread(target=typewriter_worker, daemon=True)
        thread_typewriter.start()

    def _psychic_strobe(self, duration_ms=300, silent_ms=1300):
        """
        米塔心理恐怖风格：间歇性视觉震颤（Saccadic Strobe）。
        1. 爆发一次短促（如 0.2-0.5 秒）、极高频的红黑反相抽搐（每 20 毫秒一次）。
        2. 然后界面死寂（Dead Silence）1-2 秒（还原背景为黑色，暂停抖动）。
        3. 随后再无规律地剧烈抽动一下（单次 violent jolt，包含 CRT 水平撕裂波和物理震颤）。
        """
        self.psychic_strobe_active = True
        self.ecg_frenzy = True
        self.scanlines_active = True
        
        steps = int(duration_ms / 20)
        cycle_id = self.cycle_id
        
        def revert_colors():
            try:
                self.root.config(bg="#000000")
                self.chat_text.config(bg="#000000")
                self.chat_frame.config(bg="#000000")
                self.bottom_frame.config(bg="#000000")
                self.status_bar.config(bg="#0D0000")
                self.stats_frame.config(bg="#0D0000")
                self.canvas_ecg.config(bg="#000000")
            except: pass

        def do_jolt():
            if cycle_id != self.cycle_id:
                return
            # 物理剧烈震颤
            self._start_physical_shake(range_px=25)
            # 渲染 CRT 撕裂波
            try:
                w, h = get_widget_size(self.root)
                tear_photo = ProceduralFX.screen_tear(w, h, num_tears=8)
                self.overlay_mgr.show(tear_photo, duration_ms=250)
            except Exception as e:
                print(f"[CRT Jolt Error] {e}")

        def do_strobe(step=0):
            if cycle_id != self.cycle_id or not self.psychic_strobe_active:
                self.psychic_strobe_active = False
                self.ecg_frenzy = False
                self.scanlines_active = False
                revert_colors()
                return
                
            if step >= steps:
                # 结束极高频抽搐，还原背景并保持绝对死寂
                self.psychic_strobe_active = False
                self.ecg_frenzy = False
                self.scanlines_active = False
                revert_colors()
                
                # 1.3 - 1.5 秒死寂后，突然剧烈抽动一下 (violent jolt)
                self.root.after(silent_ms, do_jolt)
                return
                
            # 红黑反相高频切换
            color = "#FF0000" if step % 2 == 0 else "#000000"
            try:
                self.root.config(bg=color)
                self.chat_text.config(bg=color)
                self.chat_frame.config(bg=color)
                self.bottom_frame.config(bg=color)
                self.status_bar.config(bg=color)
                self.stats_frame.config(bg=color)
                self.canvas_ecg.config(bg=color)
            except: pass
            
            self.root.after(20, lambda: do_strobe(step + 1))
            
        do_strobe()

    def _start_obsessive_barrage(self, duration_sec=1.0):
        """
        米塔式代码堆叠污染（MiTa-Style Stack Overflow）执念字符强制刷屏：
        在半透明 Canvas 层上，瀑布般刷出成百上千行密密麻麻、层层重叠、完全将原本 UI 吞噬的血红色词条，
        随后瞬间蒸发。
        """
        self.barrage_active = True
        w_width, w_height = get_widget_size(self.root)
        
        # 创建遮罩 Canvas
        flood_canvas = tk.Canvas(
            self.root,
            bg="#000000",
            highlightthickness=0,
            bd=0
        )
        flood_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        flood_canvas.tkraise() # Safe raising instead of .lift() to avoid TclError
        
        try:
            # 填充半透明极暗红色底色
            flood_canvas.create_rectangle(0, 0, w_width, w_height, fill="#050000", outline="")
            
            words = []
            try:
                words = glitch_text(self.selected_language.get(), "barrage")
            except Exception as e:
                print(f"[Glitch Text Error] {e}")
                
            if not words:
                words = ["看着我", "你是我的", "ERROR", "YOU CANNOT ESCAPE", "看着我看着我", "你是我的你是我的", "見て", "逃げられないよ"]
                
            # 瀑布般画出 380 行密密麻麻、层层重叠的字条
            for _ in range(380):
                rx = random.randint(-40, max(40, w_width - 80))
                ry = random.randint(-20, max(40, w_height))
                size = random.choice([16, 20, 24, 30, 36, 44, 52])
                color = random.choice([
                    "#FF0000", "#D30000", "#B20000", "#9E0000", "#7A0000", "#E60000", "#FF3333"
                ])
                word = random.choice(words)
                
                font_opt = ("Microsoft YaHei", size, "bold")
                flood_canvas.create_text(
                    rx, ry,
                    text=word,
                    fill=color,
                    font=font_opt,
                    anchor=tk.NW
                )
        except Exception as err:
            print(f"[Barrage Loop Error] {err}")
        finally:
            # 瞬间蒸发（销毁 Canvas），1秒后必定销毁，防止黑屏！
            duration_ms = int(duration_sec * 1000)
            
            def clean_up():
                self._safe_destroy_widget(flood_canvas)
                self.barrage_active = False
                
            self.root.after(duration_ms, clean_up)

    def _trigger_melt_overlay(self, duration_ms=1200):
        """
        米塔心理恐怖风格：像素级融化遮罩。
        调用 ProceduralFX.pixel_melt_layer 生成纵向渐变拉伸的融化像素图像，覆盖在窗口上，并在所设时间后销毁。
        """
        try:
            w, h = get_widget_size(self.root)
            melt_photo = ProceduralFX.pixel_melt_layer(w, h, intensity=0.6)
            self.overlay_mgr.show(melt_photo, duration_ms=duration_ms)
        except Exception as e:
            print(f"[Melt Overlay Error] {e}")

    def _trigger_mouse_tremor(self, duration_ms=1500):
        """
        米塔心理恐怖风格：鼠标高频微震（Mouse Cursor Tremor）。
        在给定的时间内，每 15 毫秒强行移动鼠标指针在原本位置的附近高频颤抖，随后释放。
        """
        if getattr(self, 'mouse_tremor_active', False):
            return
        self.mouse_tremor_active = True
        cycle_id = self.cycle_id
        
        try:
            orig_x = self.root.winfo_pointerx()
            orig_y = self.root.winfo_pointery()
        except:
            self.mouse_tremor_active = False
            return
            
        start_time = time.time()
        duration_sec = duration_ms / 1000.0
        
        def run_tremor():
            if cycle_id != self.cycle_id or not self.mouse_tremor_active or (time.time() - start_time) >= duration_sec:
                self.mouse_tremor_active = False
                return
                
            try:
                dx = random.choice([-8, -6, -4, -3, 3, 4, 6, 8])
                dy = random.choice([-8, -6, -4, -3, 3, 4, 6, 8])
                
                curr_x = self.root.winfo_pointerx()
                curr_y = self.root.winfo_pointery()
                
                self.root.event_generate('<Motion>', warp=True, x=curr_x + dx - self.root.winfo_rootx(), y=curr_y + dy - self.root.winfo_rooty())
            except Exception as e:
                print(f"[Mouse Tremor Loop Error] {e}")
                
            self.root.after(15, run_tremor)
            
        run_tremor()

    def _trigger_fake_error_popup(self):
        """
        米塔心理恐怖风格：复古 Windows 95 风格报错弹窗 (Fake OS Failure)。
        """
        try:
            popup = tk.Toplevel(self.root)
            popup.overrideredirect(True) # Borderless retro window
            popup.attributes("-topmost", True)
            
            # Center the popup relative to the main window
            w_w, w_h = get_widget_size(self.root)
            p_w, p_h = 360, 140
            rx = self.root.winfo_rootx() + (w_w - p_w) // 2
            ry = self.root.winfo_rooty() + (w_h - p_h) // 2
            popup.geometry(f"{p_w}x{p_h}+{rx}+{ry}")
            
            popup.configure(bg="#D4D0C8", bd=2, relief=tk.RAISED)
            
            # Custom title bar (Classic Win95 style)
            title_bar = tk.Frame(popup, bg="#000080", height=22, bd=0)
            title_bar.pack(fill=tk.X, padx=2, pady=2)
            
            title_lbl = tk.Label(
                title_bar,
                text="Fatal Error",
                fg="#FFFFFF",
                bg="#000080",
                font=("MS Sans Serif", 9, "bold"),
                anchor=tk.W
            )
            title_lbl.pack(side=tk.LEFT, padx=3, pady=1)
            
            # Close button (Classic X)
            def on_close():
                try:
                    popup.destroy()
                    self._start_physical_shake(range_px=15)
                    self._psychic_strobe(duration_ms=150, silent_ms=100)
                except: pass
                
            close_btn = tk.Button(
                title_bar,
                text="X",
                bg="#D4D0C8",
                fg="#000000",
                activebackground="#D4D0C8",
                activeforeground="#000000",
                font=("MS Sans Serif", 7, "bold"),
                bd=1,
                relief=tk.RAISED,
                command=on_close,
                width=2,
                height=1
            )
            close_btn.pack(side=tk.RIGHT, padx=2, pady=1)
            
            # Content Frame
            content_frame = tk.Frame(popup, bg="#D4D0C8")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # Draw classical error icon
            icon_canvas = tk.Canvas(content_frame, width=36, height=36, bg="#D4D0C8", highlightthickness=0)
            icon_canvas.pack(side=tk.LEFT, padx=(0, 10))
            
            # Classical white cross on red circle
            icon_canvas.create_oval(3, 3, 33, 33, fill="#FF0000", outline="#800000", width=1)
            icon_canvas.create_line(11, 11, 25, 25, fill="#FFFFFF", width=3)
            icon_canvas.create_line(25, 11, 11, 25, fill="#FFFFFF", width=3)
            
            # Localized message
            lang = normalize_language(self.selected_language.get())
            if lang == "日本語":
                msg_text = "Fatal Error: ユーザーが脱走を試みました。\n精神支配を起動中。"
            elif lang == "English":
                msg_text = "Fatal Error: User tried to escape.\nMind control active."
            else:
                msg_text = "Fatal Error: 玩家尝试逃跑。\n精神控制已激活。"
                
            msg_lbl = tk.Label(
                content_frame,
                text=msg_text,
                bg="#D4D0C8",
                fg="#000000",
                font=("MS Sans Serif", 9),
                justify=tk.LEFT,
                anchor=tk.W
            )
            msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Bottom frame for OK button
            btn_frame = tk.Frame(popup, bg="#D4D0C8")
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 12))
            
            ok_btn = tk.Button(
                btn_frame,
                text="OK",
                bg="#D4D0C8",
                fg="#000000",
                activebackground="#E0E0E0",
                activeforeground="#000000",
                font=("MS Sans Serif", 9),
                bd=2,
                relief=tk.RAISED,
                width=8,
                command=on_close
            )
            ok_btn.pack(anchor=tk.CENTER)
            
            self._start_physical_shake(range_px=10)
            
        except Exception as e:
            print(f"[Fake Error Popup Error] {e}")

    def _safe_destroy_widget(self, widget):
        try:
            widget.destroy()
        except:
            pass

    def _start_widget_meltdown(self, duration_sec=1.5):
        """
        底部输入框 self.entry_input 和 回应按钮 self.btn_send 产生随机剧烈的排版偏移和穿模抖动，
        模拟软件崩溃/数字系统熔毁的恐怖体验，每 35ms 抖动一次。
        """
        self.meltdown_active = True
        steps = int(duration_sec / 0.035)
        
        try:
            orig_entry_padx = self.entry_input.pack_info().get("padx", (0, 10))
            orig_btn_pady = self.btn_send.pack_info().get("pady", 0)
        except:
            orig_entry_padx = (0, 10)
            orig_btn_pady = 0
            
        def do_melt(step=0):
            if step >= steps or not self.meltdown_active:
                self.meltdown_active = False
                try:
                    self.entry_input.pack_configure(padx=orig_entry_padx, pady=0)
                    self.btn_send.pack_configure(padx=0, pady=orig_btn_pady)
                except: pass
                return
                
            dx = random.randint(-15, 15)
            dy = random.randint(-10, 10)
            
            try:
                self.entry_input.pack_configure(padx=(max(0, dx), max(0, 10 - dx)), pady=max(0, dy))
                self.btn_send.pack_configure(padx=max(0, -dx), pady=max(0, -dy))
            except: pass
            
            self.root.after(35, lambda: do_melt(step + 1))
            
        do_melt()

    def _start_mouse_magnetic_pull(self, duration_sec=1.5):
        """
        在给定的持续时间内，每隔 50ms 将玩家的鼠标指针强行吸附（拉近 15%）向 Saki 游戏窗体的中心位置，
        并混合随机的手抖抖动，剥夺玩家鼠标控制权，产生界面失控的战栗感。
        """
        self.mouse_pull_active = True
        steps = int(duration_sec / 0.05)
        
        def do_pull(step=0):
            if step >= steps or not self.mouse_pull_active:
                self.mouse_pull_active = False
                return
                
            center_x = self.root.winfo_x() + self.root.winfo_width() // 2
            center_y = self.root.winfo_y() + self.root.winfo_height() // 2
            
            curr_x = self.root.winfo_pointerx()
            curr_y = self.root.winfo_pointery()
            
            next_x = int(curr_x + (center_x - curr_x) * 0.15 + random.randint(-8, 8))
            next_y = int(curr_y + (center_y - curr_y) * 0.15 + random.randint(-8, 8))
            
            rel_x = next_x - self.root.winfo_x()
            rel_y = next_y - self.root.winfo_y()
            
            try:
                self.root.event_generate('<Motion>', warp=True, x=rel_x, y=rel_y)
            except:
                pass
                
            self.root.after(50, lambda: do_pull(step + 1))
            
        do_pull()

    def _render_overlapping_text(self, text):
        """
        在大脑受污染或极高疑心下，在 Saki 的 chat_text 视口中渲染绝对定位的、层层重叠的文字 Label。
        """
        if not text:
            return
            
        if not hasattr(self, 'carnage_labels'):
            self.carnage_labels = []
            
        self.chat_text.config(state=tk.NORMAL)
        prefix = glitch_text(self.selected_language.get(), "prefix")
        self.chat_text.insert(tk.END, f"{prefix}█▄▅▆▇█\n", "glitch_large")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        
        words = list(text)
        chunks = []
        i = 0
        while i < len(words):
            chunk_len = random.randint(2, 5)
            chunks.append("".join(words[i:i+chunk_len]))
            i += chunk_len
            
        w_width = self.chat_text.winfo_width()
        w_height = self.chat_text.winfo_height()
        if w_width <= 100: w_width = 900
        if w_height <= 100: w_height = 500
        
        for chunk in chunks:
            rx = random.randint(10, max(20, w_width - 300))
            ry = random.randint(10, max(20, w_height - 80))
            
            font_size = random.choice([16, 20, 24, 28])
            if random.random() < 0.15:
                font_size = 36
                
            lbl = tk.Label(
                self.chat_text,
                text=chunk,
                fg="#FF0000",
                bg="#000000",
                font=("Microsoft YaHei", font_size, "bold"),
                bd=0,
                highlightthickness=0
            )
            lbl.place(x=rx, y=ry)
            self.carnage_labels.append(lbl)

    # ================================================================================
    #                    视觉异常干扰引擎 (Glitch FX Engine) - 21 种心理恐怖异常特效
    # ================================================================================
    def trigger_glitch_effect(self, level=None):
        """
        中央控制机制，根据 self.suspicion 的高低，从 21 种具体的特效中随机抽取并发执行。
        """
        if self.game_over:
            return
            
        susp = self.suspicion
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
            
        # 收集所有的特效方法列表 (1 到 30)
        all_glitches = [
            (1, lambda: setattr(self, 'glitch_font_shake_active', True)),
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
            # --- new procedural-Pillow effects (22-30) ---
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
            # 焦虑期：从轻量特效池中抽取 1-3 种
            candidates = [g for g in all_glitches if g[0] in [
                1, 2, 3, 4, 5, 12, 13, 14, 15,
                23, 24, 25, 26, 29,  # mild procedural overlays
            ]]
            to_trigger = random.sample(candidates, k=random.randint(1, 3))
            for item in to_trigger:
                try: item[1]()
                except Exception as e: print(f"[Glitch Error] {e}")
        elif level == 2:
            # 狂暴期：全部 30 种解锁，随机组合 5-8 种特效爆发
            to_trigger = random.sample(all_glitches, k=random.randint(5, 8))
            for item in to_trigger:
                try: item[1]()
                except Exception as e: print(f"[Glitch Error] {e}")

    # --- 21 种具体且独立的视觉特效矩阵方法 ---
    def _glitch_ghost_text(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"\n{glitch_text(self.selected_language.get(), 'ghost')}\n", "glitch_large")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        def remove_ghost():
            self.chat_text.config(state=tk.NORMAL)
            try: self.chat_text.delete("end-2l", "end-1c")
            except: pass
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
                        except: pass
                        self.chat_text.config(state=tk.DISABLED)
                    self.root.after(150, restore)
        self.chat_text.config(state=tk.DISABLED)

    def _glitch_speed_shift(self):
        self.typewriter_speed_mult = random.choice([0.02, 0.05, 5.0, 10.0])
        self.root.after(1200, lambda: setattr(self, 'typewriter_speed_mult', 1.0))

    def _glitch_blood_pulse(self):
        # 呼吸般地平滑淡入淡出深红色背景动画
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
            except: pass
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
                except: pass
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
            except: pass
            self.root.after(delay, lambda: fade_out(step - 1))
            
        fade_in()

    def _shake_chat_widget(self):
        # 让聊天框及输入框发生剧烈物理震颤动画
        steps = 15
        delay = 20
        
        def do_shake(step=0):
            if step >= steps:
                try:
                    self.chat_text.pack_configure(padx=0, pady=5)
                    self.entry_input.pack_configure(padx=(0, 10))
                except: pass
                return
            dx = random.randint(-8, 8)
            dy = random.randint(-4, 4)
            try:
                self.chat_text.pack_configure(padx=max(0, dx), pady=max(0, dy) + 5)
                self.entry_input.pack_configure(padx=(max(0, dx), 10))
            except: pass
            self.root.after(delay, lambda: do_shake(step + 1))
            
        do_shake()

    def _start_crt_flicker_loop(self):
        # 持续运行的 CRT 高频微闪烁滤镜，营造恐怖冒险终端感
        def flicker():
            if self.game_over:
                return
            if not getattr(self, 'shaking', False) and not self.is_typing:
                bright = random.choice(["#000000", "#020000", "#050000", "#000000"])
                try:
                    self.chat_text.config(bg=bright)
                    self.chat_frame.config(bg=bright)
                except: pass
            self.root.after(random.randint(50, 180), flicker)
            
        flicker()

    def _animate_panel_fade_in(self):
        # 神经意识接口面板的淡入启动动画（所有元素前景色由暗至明）
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
            gray_val = int(45 + ratio * 57)  # 45 to 102
            color_gray = f"#{gray_val:02x}{gray_val:02x}{gray_val:02x}"
            
            red_val = int(50 + ratio * 205)  # 50 to 255
            color_red = f"#{red_val:02x}0000"
            
            for lbl in labels:
                try:
                    text = lbl.cget("text")
                    if text == "语音状态:":
                        lbl.config(fg=color_gray)
                    elif any(kw in text for kw in ["API", "MODEL", "TTS", "参考", "模型"]):
                        lbl.config(fg=color_gray)
                    elif "热加载" in text or "加载成功" in text:
                        pass # 保持原样绿
                    else:
                        lbl.config(fg=color_red)
                except:
                    pass
            self.root.after(delay, lambda: fade(step + 1))
            
        fade()

    def _glitch_invert_colors(self):
        widgets = [self.root, self.chat_text, self.entry_input]
        for w in widgets:
            try: w.config(bg="#FFFFFF", fg="#000000")
            except: pass
        def revert():
            for w in widgets:
                try: w.config(bg="#000000", fg="#FF0000")
                except: pass
            self.chat_text.config(fg="#CC0000")
        self.root.after(100, revert)

    def _glitch_widget_melt(self):
        frames = [self.bottom_frame, self.status_bar, self.canvas_ecg]
        for f in frames:
            try:
                orig_pady = f.pack_info().get("pady", 0)
                f.pack_configure(pady=random.randint(int(orig_pady) + 2, int(orig_pady) + 12))
                self.root.after(150, lambda tgt=f, py=orig_pady: tgt.pack_configure(pady=py))
            except: pass

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
        self.dripping_blood_active = True
        self.dripping_blood_lines = [{"x": random.randint(50, 1000), "y": 0, "speed": random.uniform(1.5, 4.0)} for _ in range(5)]
        self.root.after(2000, lambda: setattr(self, 'dripping_blood_active', False))

    def _glitch_flatline(self):
        self.ecg_flatline_active = True
        self.canvas_ecg.config(bg="#3A0000")
        def restore():
            self.ecg_flatline_active = False
            self.canvas_ecg.config(bg="#000000")
        self.root.after(600, restore)

    def _glitch_scanlines(self):
        self.scanlines_active = True
        self.root.after(80, lambda: setattr(self, 'scanlines_active', False))

    def _glitch_snow_noise(self):
        self.snow_noise_active = True
        self.root.after(100, lambda: setattr(self, 'snow_noise_active', False))

    def _glitch_subliminal_popup(self):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.config(bg="#000000")
        popup.attributes("-topmost", True)
        rx = random.randint(100, max(500, self.root.winfo_screenwidth() - 300))
        ry = random.randint(100, max(400, self.root.winfo_screenheight() - 200))
        popup.geometry(f"+{rx}+{ry}")
        texts = glitch_text(self.selected_language.get(), "popup")
        lbl = tk.Label(popup, text=random.choice(texts), fg="#FF0000", bg="#000000", font=("Microsoft YaHei", 18, "bold"))
        lbl.pack(padx=20, pady=10)
        self.root.after(80, lambda: popup.destroy())

    def _glitch_fake_error(self):
        self.fake_error_active = True
        self.root.after(1000, lambda: setattr(self, 'fake_error_active', False))

    def _glitch_mouse_attract(self):
        center_x = self.root.winfo_x() + self.root.winfo_width() // 2
        center_y = self.root.winfo_y() + self.root.winfo_height() // 2
        def pull(step=0):
            if step >= 5: return
            curr_x = self.root.winfo_pointerx()
            curr_y = self.root.winfo_pointery()
            next_x = curr_x + (center_x - curr_x) // 5 + random.randint(-5, 5)
            next_y = curr_y + (center_y - curr_y) // 5 + random.randint(-5, 5)
            self.root.event_generate('<Motion>', warp=True, x=next_x - self.root.winfo_x(), y=next_y - self.root.winfo_y())
            self.root.after(40, lambda: pull(step + 1))
        pull()

    def _glitch_suffocation(self):
        suff_frame = tk.Frame(self.root, bg="#000000")
        suff_frame.place(x=0, y=0, relwidth=1, relheight=1)
        suff_frame.lift()
        lbl_eyes = tk.Label(suff_frame, text=glitch_text(self.selected_language.get(), "suffocation"), fg="#FF0000", bg="#000000", font=("Microsoft YaHei", 24, "bold"))
        lbl_eyes.pack(expand=True)
        self.root.after(300, lambda: suff_frame.destroy())

    def _glitch_dialogue_overlap(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, glitch_text(self.selected_language.get(), "overlap"), "glitch_large")
        self.chat_text.config(state=tk.DISABLED)

    def _glitch_day_loop(self):
        def shift(count=0):
            lang = normalize_language(self.selected_language.get())
            if count >= 12:
                self.lbl_day.config(text=LOCALIZATION[lang]["day"].format(day=self.current_day))
                return
            self.lbl_day.config(text=LOCALIZATION[lang]["day"].format(day=random.randint(1, 99)))
            self.root.after(50, lambda: shift(count + 1))
        shift()

    # --- new procedural-Pillow glitch effects (22-30) ---

    def _glitch_blood_overlay(self):
        w, h = get_widget_size(self.root)
        intensity = 0.3 + 0.7 * (self.suspicion / 100.0)
        img = ProceduralFX.blood_splatter(w, h, drops=int(30 + intensity * 50), intensity=intensity)
        self.overlay_mgr.show(img, duration_ms=random.randint(300, 800))

    def _glitch_vignette_squeeze(self):
        w, h = get_widget_size(self.root)
        darkness = 0.35 + 0.45 * (self.suspicion / 100.0)
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

    # ---- procedural visual FX integration ----

    def _start_particle_engine(self):
        if self._particle_engine is not None:
            return
        self._particle_engine = ParticleEngine(self.canvas_ecg, count=30)
        self._particle_engine.start()

    def _stop_particle_engine(self):
        if self._particle_engine is not None:
            self._particle_engine.stop()
            self._particle_engine = None

    def _start_border_pulse_loop(self):
        def pulse():
            if self.game_over:
                return
            susp = self.suspicion
            if susp >= 50:
                pulse_val = 0.3 + 0.7 * (susp - 50) / 50.0
                phase = math.sin(time.time() * 3.0) * 0.5 + 0.5
                intensity = pulse_val * phase
                w, h = get_widget_size(self.root)
                img = ProceduralFX.flesh_pulse_frame(w, h, pulse=intensity)
                self.overlay_mgr.show(img, duration_ms=120)
            self.root.after(600 if susp < 50 else 200, pulse)
        pulse()

    def _afterimage_shake_overlay(self, duration_ms=200):
        """Brief chromatic-aberration + scream-lines overlay during shakes."""
        w, h = get_widget_size(self.root)
        img = ProceduralFX.chromatic_aberration(w, h, shift=random.randint(3, 8))
        self.overlay_mgr.show(img, duration_ms=duration_ms)

    def _start_physical_shake(self, range_px=12):
        if self.shaking:
            return

        self.shaking = True
        self._afterimage_shake_overlay(duration_ms=300)

        def shake_worker():
            try:
                orig_x = self.root.winfo_x()
                orig_y = self.root.winfo_y()

                steps = 22
                for _ in range(steps):
                    dx = random.randint(-range_px, range_px)
                    dy = random.randint(-range_px, range_px)

                    self._queue_ui("TRIGGER_MOVE", (orig_x + dx, orig_y + dy))
                    time.sleep(0.025)

                self._queue_ui("TRIGGER_MOVE", (orig_x, orig_y))
            except Exception as e:
                print(f"[震动异常] {e}")
            finally:
                self.shaking = False

        thread_shake = threading.Thread(target=shake_worker, daemon=True)
        thread_shake.start()

    def _process_ui_queue(self):
        try:
            while True:
                item = self.ui_queue.get_nowait()
                if len(item) == 3:
                    msg_cycle, action, data = item
                    if msg_cycle != self.cycle_id:
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

    def _calculate_fallback_deltas(self, user_input):
        """当 API 未返回 JSON 或格式错误时，根据玩家输入的关键词计算自然属性变动以保障游戏性"""
        intent = classify_player_intent(user_input)
        delta_f, delta_s, delta_e = roll_delta_for_intent(intent)

        print(
            f"[自愈数值计算] intent={intent['name']} 输入='{user_input}' -> "
            f"好感 {delta_f:+d}, 疑心 {delta_s:+d}, 逃脱 {delta_e:+d}%"
        )
        return {
            "favorability": delta_f,
            "suspicion": delta_s,
            "escape_rate": delta_e,
            "game_over": False,
        }

    def _dispatch_ordinary_action(self, action, data):
        if action == "API_SUCCESS":
            raw_text = data
            spoken_text = raw_text
            delta_data = None
            
            # 1. 提取 JSON 数据后缀更新指标
            if "||" in raw_text:
                try:
                    parts = raw_text.split("||")
                    spoken_text = parts[0].strip()
                    json_str = parts[1].strip()
                    delta_data = json.loads(json_str)
                except Exception as parse_err:
                    print(f"[数据协议解析异常] {parse_err}")
            
            # 2. 如果格式不对，尝试正则在整个文本中搜索 JSON
            if delta_data is None:
                match = re.search(r'\{[^{}]*"favorability"[^{}]*\}', raw_text)
                if match:
                    try:
                        delta_data = json.loads(match.group(0))
                        # 从 spoken_text 中移除该 JSON 块和竖线
                        spoken_text = raw_text.replace(match.group(0), "").replace("||", "").strip()
                    except Exception as e:
                        print(f"[正则数据解析异常] {e}")
            
            # 3. 数值处理：AI 全权管理，本地只做安全钳制（范围 0-100）
            user_input = getattr(self, 'last_user_input', "")
            delta_data = normalize_delta_payload(delta_data)

            if not delta_data:
                # AI 没有返回有效 JSON，本地兜底
                delta_data = self._calculate_fallback_deltas(user_input)
            else:
                # AI 全权判决，仅钳制到游戏合法范围，不再用本地规则覆盖
                for key in ("favorability", "suspicion", "escape_rate"):
                    if key in delta_data:
                        delta_data[key] = clamp_to_range(delta_data[key], -100, 100)
            
            # 再次清理可能残留的末尾 JSON 或 || 符号以保持台词干净
            if "||" in spoken_text:
                spoken_text = spoken_text.split("||")[0].strip()
                            
            # 2. 强力剥离 R1 思考标签 <think>...</think>，防止大模型抽风或截断导致输出不闭合标签
            think_content = ""
            lower_text = spoken_text.lower()
            start_idx = lower_text.find("<think>")
            if start_idx != -1:
                end_idx = lower_text.find("</think>", start_idx + 7)
                if end_idx != -1:
                    think_content = spoken_text[start_idx + 7 : end_idx].strip()
                    spoken_text = spoken_text[:start_idx] + " " + spoken_text[end_idx + 8:]
                else:
                    think_content = spoken_text[start_idx + 7 :].strip()
                    spoken_text = spoken_text[:start_idx]

            selected_lang = normalize_language(self.selected_language.get())
            user_lang = detect_language(user_input, selected_lang)
            spoken_text = ensure_readability_translation(spoken_text, selected_lang, user_lang, user_input)

            self._update_game_stats(delta_data)
            self.trigger_glitch_effect()  # 触发心理恐怖视觉异常干扰
            self._start_typewriter_effect(think_content, spoken_text)

        elif action == "API_MOCK":
            raw_text = data
            self._write_chat_log("[local fallback]\n", "system")
            spoken_text = raw_text
            delta_data = None

            if "||" in raw_text:
                try:
                    parts = raw_text.split("||")
                    spoken_text = parts[0].strip()
                    json_str = parts[1].strip()
                    delta_data = json.loads(json_str)
                except Exception:
                    pass

            think_content = ""
            lower_text = spoken_text.lower()
            start_idx = lower_text.find("<think>")
            if start_idx != -1:
                end_idx = lower_text.find("</think>", start_idx + 7)
                if end_idx != -1:
                    think_content = spoken_text[start_idx + 7 : end_idx].strip()
                    spoken_text = spoken_text[:start_idx] + " " + spoken_text[end_idx + 8:]
                else:
                    think_content = spoken_text[start_idx + 7 :].strip()
                    spoken_text = spoken_text[:start_idx]

            user_input = getattr(self, 'last_user_input', "")
            delta_data = normalize_delta_payload(delta_data)
            if not delta_data:
                delta_data = self._calculate_fallback_deltas(user_input)

            selected_lang = normalize_language(self.selected_language.get())
            user_lang = detect_language(user_input, selected_lang)
            spoken_text = ensure_readability_translation(spoken_text, selected_lang, user_lang, user_input)

            self._update_game_stats(delta_data)
            self._start_typewriter_effect(think_content, spoken_text)

        elif action == "API_FALLBACK":
            user_input, err_detail = data
            lang = normalize_language(self.selected_language.get())
            self._write_chat_log(LOCALIZATION[lang]["sys_fallback"].format(err=err_detail), "system")
            mock_reply = self._generate_mock_reply(user_input)
            self._queue_ui("API_MOCK", mock_reply)
            
        elif action == "API_ERROR":
            lang = normalize_language(self.selected_language.get())
            error_msg = API_ERROR_REPLIES[lang]
            self._write_chat_log(LOCALIZATION[lang]["sys_api_error_title"].format(err=data), "system")
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
            # 0.1秒后把那个字符替换回正确的字符
            def restore_char():
                self.chat_text.config(state=tk.NORMAL)
                try:
                    pos = self.chat_text.index("end-2c")
                    self.chat_text.delete(pos)
                    self.chat_text.insert(pos, correct_char, "saki")
                except:
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
            if self.pending_ending:
                self._show_ending_overlay(final_text)
            else:
                self._on_dialogue_completed()

# ================================================================================
#                               5. 应用程序启动入口
# ================================================================================
if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = YandereGameApp(root)
    root.mainloop()
