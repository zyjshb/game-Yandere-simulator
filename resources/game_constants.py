# -*- coding: utf-8 -*-
import re
import random

# ================================================================================
#                        GPT-SoVITS Voice Synthesis Service Config
# ================================================================================
GPT_SOVITS_URL = "http://127.0.0.1:9880"
REFER_WAV_PATH = "D:\\行秋\\vido\\xinqiu.WAV_0000456000_0000607680.wav"
PROMPT_TEXT = "独向昭谈至恶龙一阁著文章。"

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
#                        Language System Detection and Localization Module
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
            "行動境界：心理的恐怖と劇的な緊張感を維持しつつ、過度なグロテスク表現や無意味な罵倒の連発は避ける。"
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
        "suffocation": "\U0001f441️ \U0001f441️\n\n看着我！",
        "overlap": "随时都不要离开我——看着我看着我看着我看着我看着我看着我",
        "prefix": "纱希: ",
    },
    "English": {
        "barrage": ["Look at me", "You cannot leave", "Love me", "Do not run", "Stay with me", "You are mine", "Forever together"],
        "ghost": "Saki: look at me look at me look at me look at me",
        "titles": ["Look at me!", "Do not leave me!", "Why run?", "Love me!", "Darling..."],
        "popup": ["Look at me", "You are mine", "I love you", "Do not leave", "Do not look away", "Only me"],
        "suffocation": "\U0001f441️ \U0001f441️\n\nLook at me!",
        "overlap": "Never leave me. Look at me look at me look at me look at me look at me",
        "prefix": "Saki: ",
    },
    "日本語": {
        "barrage": ["見て", "逃げられないよ", "好き好き", "逃げないで", "愛して", "あなたは私のもの", "ずっと一緒"],
        "ghost": "紗希: 見て見て見て見て見て",
        "titles": ["見て！", "置いていかないで！", "どうして逃げるの？", "愛して！", "あなた……"],
        "popup": ["見て", "あなたは私のもの", "愛してる", "離れないで", "目をそらさないで", "私だけ"],
        "suffocation": "\U0001f441️ \U0001f441️\n\n見て！",
        "overlap": "いつでも私から離れないで——見て見て見て見て見て見て",
        "prefix": "紗希: ",
    },
}

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
#                        Language and TTS Helper Functions
# ================================================================================

def normalize_language(lang):
    """Return a supported game language, falling back to Chinese for unknown config values."""
    return lang if lang in SUPPORTED_LANGUAGES else "中文"


def language_to_tts_code(lang):
    lang = normalize_language(lang)
    if lang == "English":
        return "en"
    if lang == "日本語":
        return "ja"
    return "zh"


def detect_language(text, default_lang="中文"):
    if not text:
        return default_lang
    cleaned = re.sub(r"[\d\s\W_]", "", text)
    if not cleaned:
        return default_lang
    if re.search(r"[぀-ゟ゠-ヿ]", cleaned):
        return "日本語"
    if re.search(r"[一-龥]", cleaned):
        return "中文"
    if re.search(r"[a-zA-Z]", cleaned):
        return "English"
    return default_lang


def same_language(lang_a, lang_b):
    a = (lang_a or "").lower()
    b = (lang_b or "").lower()
    for canonical, aliases in LANGUAGE_ALIAS_GROUPS.items():
        if any(alias.lower() in a for alias in aliases) and any(alias.lower() in b for alias in aliases):
            return True
    return normalize_language(lang_a) == normalize_language(lang_b)


def clean_text_for_tts(text):
    """Clean TTS text: remove brackets/parentheses content, non-verbal symbols."""
    if not text:
        return ""
    text = re.sub(r"\|\|.*?\|\|", "", text, flags=re.S)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    old_text = ""
    while old_text != text:
        old_text = text
        text = re.sub(r"[\(（][^\(\)（）]*[\)）]", "", text)
        text = re.sub(r"[\[【][^\[\]【】]*[\]】]", "", text)
        text = re.sub(r"\{[^\{\}]*\}", "", text)
        text = re.sub(r'\*[^*]*\*', '', text)
    text = re.sub(r'[^\w\s一-龥，。！？、…；：“”‘’\-]', '', text)
    if not re.search(r"[一-龥぀-ゟ゠-ヿa-zA-Z0-9]", text):
        return ""
    return text.strip()


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
#                        Intent Classification Helpers
# ================================================================================

def _negation_prefixes():
    return (
        "不", "没", "别", "莫", "休", "未", "非", "勿", "无",
        "not ", "don't ", "dont ", "do not ", "never ", "no ",
        "じゃない", "ではない", "じゃねえ", "ない", "ません", "ぬ",
        "じゃなく", "ではなく",
    )


def _is_negated(text, keyword):
    """Check if *keyword* is negated in *text* (e.g. 不喜欢, don't like, 好きじゃない)."""
    idx = text.find(keyword)
    if idx == -1:
        return False
    before = text[max(0, idx - 3):idx]
    if not before:
        return False
    _single_neg = ("不", "没", "别", "莫", "勿", "未", "非", "无")
    for ch in _single_neg:
        if ch in before:
            return True
    for neg in _negation_prefixes():
        if len(neg) > 1 and before.endswith(neg):
            return True
    return False


def _has_defiance_signal(text):
    """Detect defiance/rejection signals in text."""
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

    romantic_possessive_phrases = (
        "我的女人", "做我女人", "做我的女人", "是我的女人", "你是我的女人", "成为我的女人",
        "我的男人", "做我男人", "做我的男人", "是我的男人", "你是我的男人", "成为我的男人",
        "做你的男人", "做你男人", "做你的女人", "做你女人", "我女人", "你女人", "成为我的"
    )
    if any(p in lowered for p in romantic_possessive_phrases):
        for rule in INTENT_RULES:
            if rule["name"] == "affection":
                return rule

    matches = []
    for rule in INTENT_RULES:
        if rule["name"] == "default":
            continue
        for kw in rule["keywords"]:
            if kw in lowered and not _is_negated(lowered, kw):
                matches.append((rule, kw))
                break
    if matches:
        negative_priority = ("extreme_rejection", "destructive_attack", "betrayal_mockery")
        for name in negative_priority:
            for rule, _ in matches:
                if rule["name"] == name:
                    return rule
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


# ================================================================================
#                        Numeric Coercion and Clamping Helpers
# ================================================================================

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


# ================================================================================
#                        Glitch Text Helper
# ================================================================================

def glitch_text(lang, key):
    lang = normalize_language(lang)
    return GLITCH_LOCALIZATION[lang][key]


# ================================================================================
#                        Translation and Readability Helpers
# ================================================================================

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
    match = re.search(r"[（\(]([^（\)\(\)]{4,})[）\)]\s*$", text)
    if not match:
        return False
    content = match.group(1)
    user_lang = normalize_language(user_lang)
    if user_lang == "中文":
        return bool(re.search(r"[一-龥]", content))
    elif user_lang == "English":
        return bool(re.search(r"[a-zA-Z]", content))
    elif user_lang == "日本語":
        return bool(re.search(r"[぀-ゟ゠-ヿ]", content))
    return True


def strip_terminal_parenthetical_translation(text, user_lang="中文"):
    if not text:
        return ""
    if has_terminal_parenthetical_translation(text, user_lang):
        return re.sub(r"\s*[（\(][^（\)\(\)]{4,}[）\)]\s*$", "", text).strip()
    return text.strip()


def extract_terminal_parenthetical_translation(text, user_lang="中文"):
    if not text:
        return ""
    match = re.search(r"([（\(][^（\)\(\)]{4,}[）\)])\s*$", text)
    if not match:
        return ""
    content = match.group(1)
    if has_terminal_parenthetical_translation(text, user_lang):
        return content
    return ""


def ensure_readability_translation(text, selected_lang, user_lang, user_input):
    if not user_input:
        return text
    saki_actual_lang = detect_language(text, selected_lang)
    if same_language(saki_actual_lang, user_lang):
        return strip_terminal_parenthetical_translation(text, user_lang)
    if has_terminal_parenthetical_translation(text, user_lang):
        return text
    intent = classify_player_intent(user_input)
    return text.rstrip() + build_offline_translation_line(intent["name"], user_lang)
