# -*- coding: utf-8 -*-
from resources.game_constants import (
    normalize_language,
    classify_player_intent,
    roll_delta_for_intent,
    coerce_int,
    coerce_bool,
    clamp_to_range,
    LANGUAGE_PROFILES,
    ROLE_SIMULATION_STANDARD,
    ROLE_SIMULATION_STANDARD_LOCALIZED,
    build_translation_rule,
    translation_required,
)


# ================================================================================
#                        Delta Parsing Helpers (pure functions)
# ================================================================================

def normalize_delta_payload(delta_data):
    """Normalize a raw delta dict from API/fallback into a clean, typed dict.

    Returns None if delta_data is not a dict.
    """
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
    """Clamp each delta value to the range of the player's classified intent."""
    if not delta_data or not user_input:
        return delta_data

    intent = classify_player_intent(user_input)
    f_min, f_max, s_min, s_max, e_min, e_max = intent["delta"]
    delta_data["favorability"] = clamp_to_range(delta_data.get("favorability", 0), f_min, f_max)
    delta_data["suspicion"] = clamp_to_range(delta_data.get("suspicion", 0), s_min, s_max)
    delta_data["escape_rate"] = clamp_to_range(delta_data.get("escape_rate", 0), e_min, e_max)
    return delta_data


def _calculate_fallback_deltas(user_input):
    """Compute natural stat changes from player input keywords when API returns no JSON."""
    intent = classify_player_intent(user_input)
    delta_f, delta_s, delta_e = roll_delta_for_intent(intent)

    print(
        f"[Self-Healing Calc] intent={intent['name']} input='{user_input}' -> "
        f"favor {delta_f:+d}, suspicion {delta_s:+d}, escape {delta_e:+d}%"
    )
    return {
        "favorability": delta_f,
        "suspicion": delta_s,
        "escape_rate": delta_e,
        "game_over": False,
    }


# ================================================================================
#                        Prompt Builders
# ================================================================================

def build_metric_rules_prompt(selected_lang="中文"):
    """Build the localized AI numerical jurisdiction prompt for a given language."""
    selected_lang = normalize_language(selected_lang)
    if selected_lang == "日本語":
        return (
            "あなたは紗希の数値管理者であり、favorability / suspicion / escape_rate に対する完全な裁量権を持っています。\n"
            "以下のガイドラインを参考に、毎ターンの数値変化（delta）の正負と幅を自主的に決定してください。固定された範囲に縛られる必要はありません：\n"
            "- 好感度 favorability：正の値は紗希がより信頼・愛着を感じていることを示し、負の値は傷つき・疎遠になっていることを示します。\n"
            "- 疑心度 suspicion：正の値は紗希がより疑い・警戒していることを示し、負の値はリラックス・安心していることを示します。\n"
            "- 脱出率 escape_rate：正の値はプレイヤーの脱出意図の上昇を示し、負の値は脱出意図の低下を示します。\n\n"
            "【裁定原則】\n"
            "1. プレイヤーの口調、発言内容、文脈の一貫性、および紗希の現在の感情状態に基づいて、各変数の delta の正負と大きさを自主的に判断してください。\n"
            "2. たわいもない一言 → delta の幅は小さく（±3〜±8）。強烈な告白や激しい衝突 → delta の幅は大きく（±20〜±40）。\n"
            "3. suspicion が 70 を超えている場合、ポジティブな言葉の効果は半減します（紗希は簡単には信じません）。\n"
            "4. 真の結末（エンディング）の最高潮の瞬間のみ、game_over を true に設定してください。"
        )
    elif selected_lang == "English":
        return (
            "You are Saki's numerical judge, with full authority over favorability / suspicion / escape_rate.\n"
            "Use the following guidelines to independently determine the sign and magnitude of the delta for each round. Do not be constrained by a fixed range:\n"
            "- favorability: Positive represents increased trust/attachment, negative represents feeling hurt/distanced.\n"
            "- suspicion: Positive represents increased suspicion/alertness, negative represents feeling relaxed/reassured.\n"
            "- escape_rate: Positive represents increased escape intent, negative represents decreased escape intent.\n\n"
            "【Judging Principles】\n"
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
    """Build the full localized role-simulation system prompt."""
    selected_lang = normalize_language(selected_lang)
    profile = LANGUAGE_PROFILES[selected_lang]
    needs_translation = translation_required(selected_lang, user_lang)

    standard = ROLE_SIMULATION_STANDARD_LOCALIZED[selected_lang]
    metric_prompt = build_metric_rules_prompt(selected_lang)

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
            "プレイヤーが優しい言葉をかけてくれた。嬉しい。引退や裏切りの懸念はない。好感度を少し上げ、疑心度を少し下げる。\n"
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
            "【BILINGUAL OUTPUT EXAMPLE (Bilingual Contract is YES, Player Language is Chinese)】\n"
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


# ================================================================================
#                        GameState Class
# ================================================================================

class GameState:
    """Encapsulates all mutable RPG game state and core logic.

    This is a pure data/logic class with no tkinter dependencies.
    The GUI app (YandereGameApp) owns a GameState instance and syncs its
    progress bars and labels from the values on this object.
    """

    def __init__(self, cached_lang="中文"):
        # Core RPG stats
        self.current_day = 1
        self.dialogue_count = 0
        self.favorability = 50
        self.suspicion = 20
        self.escape_rate = 0

        # Flags and session ids
        self.game_over = False
        self.cycle_id = 0
        self.dialogue_session_id = 0
        self.first_msg_detected = False
        self.last_user_input = ""

        # Language
        self.cached_lang = normalize_language(cached_lang)

        # Pending ending (set when game_over triggers)
        self.pending_ending = None

    # ------------------------------------------------------------------
    # Delta application
    # ------------------------------------------------------------------

    def apply_delta(self, delta_data):
        """Apply favorability/suspicion/escape_rate changes from a delta dict.

        Values are clamped to [0, 100].  If the delta contains a game_over
        flag, or if thresholds are crossed (suspicion >= 96, favorability
        <= -25), the game enters an ending state.

        Returns the delta dict that was actually applied.
        """
        if self.game_over:
            return delta_data

        df = delta_data.get("favorability", 0)
        ds = delta_data.get("suspicion", 0)
        de = delta_data.get("escape_rate", 0)

        self.favorability = max(0, min(100, self.favorability + df))
        self.suspicion = max(0, min(100, self.suspicion + ds))
        self.escape_rate = max(0, min(100, self.escape_rate + de))

        print(
            f"[Stat Change] favor: {df:+d} -> {self.favorability}, "
            f"suspicion: {ds:+d} -> {self.suspicion}, "
            f"escape: {de:+d} -> {self.escape_rate}%"
        )

        # AI-declared game_over
        is_ai_game_over = delta_data.get("game_over")
        if is_ai_game_over in [True, "True", "true", "1", 1]:
            ai_type = delta_data.get("ending_type", "bad")
            ai_title = delta_data.get("ending_title", "")
            ai_story = delta_data.get("ending_story", "")
            print(f"[AI Ending Declared] type: {ai_type}, title: {ai_title}")
            self.pending_ending = {
                "ending_type": ai_type,
                "ending_title": ai_title,
                "ending_story": ai_story,
            }
            self.game_over = True
            return delta_data

        self._check_endings()
        return delta_data

    def _check_endings(self):
        """Check whether stat thresholds trigger a game-over."""
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

    # ------------------------------------------------------------------
    # Day advancement
    # ------------------------------------------------------------------

    def advance_day(self):
        """Increment dialogue count and advance the day if needed.

        Returns a tuple (day_changed: bool, new_day: int).
        """
        if self.game_over:
            return (False, self.current_day)

        self.dialogue_count += 1
        if self.dialogue_count >= 3:
            self.dialogue_count = 0
            self.current_day += 1
            return (True, self.current_day)
        return (False, self.current_day)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        """Reset all mutable state to initial values for a new game cycle."""
        self.current_day = 1
        self.dialogue_count = 0
        self.favorability = 50
        self.suspicion = 20
        self.escape_rate = 0
        self.game_over = False
        self.first_msg_detected = False
        self.last_user_input = ""
        self.pending_ending = None
