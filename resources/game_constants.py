# -*- coding: utf-8 -*-

import re

import random



# ================================================================================

#                        GPT-SoVITS Voice Synthesis Service Config

# ================================================================================

GPT_SOVITS_URL = "http://127.0.0.1:9880"

REFER_WAV_PATH = "models/hua/huahuo.wav_0000061760_0000188480.wav"

PROMPT_TEXT = "你要是有什么危险的差事要办，尽管来找我。"



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

        "keywords": (

            # 中文

            "给我滚", "滚蛋", "赶紧滚", "滚开", "滚远点", "滚出去",

            "老太婆", "死老太婆", "变态", "死变态", "疯子", "神经病",

            "怪物", "贱人", "垃圾", "人渣", "恶心死了", "恶心到家",

            "离我远点", "理我远点", "别过来", "别碰我", "放过我",

            "你有病", "脑子有病", "闭嘴", "给我闭嘴", "少废话",

            "老子", "老娘", "你他妈", "你算老几", "不配",

            "别自作多情", "痴心妄想", "做你的梦",

            "打死我", "打死我也不", "不喜欢", "不爱", "讨厌", "嫌弃", "烦你", "真烦", "不想要",

            # 英文

            "bitch", "monster", "freak", "psycho", "crazy bitch",

            "shut up", "get lost", "back off", "stay away from me",

            "go away", "leave me alone", "you are insane", "creep",

            "lunatic", "stalker", "weirdo", "disgusting", "gross",

            "touch me again", "you are sick", "piece of trash",

            "worthless", "pathetic freak",

            # 日文

            "うざい", "消えろ", "黙れ", "近寄るな", "触るな",

            "離れろ", "出ていけ", "くそババア", "変態", "ストーカー",

            "キチガイ", "異常者", "気持ち悪い", "死ねばいい",

            "お前なんか"

        ),

        "delta": (-25, -15, 40, 55, -10, -5),

        "prompt": "粗暴羞辱或极端拒绝：强烈受伤，语气冷下来，疑心暴涨，台词短而压抑。",

    },

    {

        "name": "destructive_attack",

        "keywords": (

            # 中文

            "去死吧", "赶紧去死", "快点去死", "你怎么不去死",

            "不想看见你", "不想见你", "永远不想见到你",

            "我恨你", "恨死你了", "恨透了你", "你这垃圾",

            "你这个毒瘤", "毒瘤", "你毁了我", "毁了我一辈子",

            "希望你消失", "最好消失", "从我眼前消失",

            "诅咒你", "你该死", "死不足惜", "下地狱",

            "你这废物", "废物", "活着干嘛", "别活了",

            # 英文

            "go to hell", "die already", "just die", "go die",

            "hate you", "I hate you", "rot in hell", "drop dead",

            "you ruin my life", "you destroyed me", "kill yourself",

            "wish you were dead", "worst mistake", "vile creature",

            "disappear forever", "never see you again",

            "curse you", "burn in hell",

            # 日文

            "死ね", "くたばれ", "大嫌い", "消えてなくなれ",

            "お前なんか死ねばいい", "今すぐ死んで", "地獄に落ちろ",

            "消え失せろ", "このゴミが", "お前のせいで",

            "二度と顔を見せるな", "生きる価値ない",

            "忌々しい", "絶望しろ"

        ),

        "delta": (-40, -30, 35, 45, -15, -10),

        "prompt": "毁灭性刺激：世界观崩塌，但不要给出现实自伤方法；用心理恐怖和冷静失控表达。",

    },

    {

        "name": "escape",

        "keywords": (

            # 中文

            "离开这里", "我要出去", "带我出去", "逃出去", "逃跑",

            "放开我", "松开手", "把我放开", "别锁着我", "别关着我",

            "钥匙在哪", "找到钥匙", "备用钥匙", "撬锁", "撬开门",

            "铁丝开锁", "解锁", "这扇门", "窗户能打开",

            "去找承太郎", "找承太郎", "找花京院", "找乔斯达",

            "找我伙伴", "找我的伙伴", "找人来救我", "求救",

            "我要回家", "带我回家", "回不去了", "走廊尽头",

            "地下室的出口", "地牢出口", "逃生通道",

            # 英文

            "escape", "get out of here", "let me go", "release me",

            "find the key", "where is the key", "unlock the door",

            "pick the lock", "break out", "break free", "get away",

            "find my friends", "find my comrades", "go home",

            "take me home", "call for help", "somebody help",

            "open the door", "open this door", "this window",

            "find an exit", "find the exit", "run away", "flee",

            # 日文

            "ここから出して", "出ていきたい", "逃げ出したい",

            "鍵を探す", "鍵はどこ", "鍵を見つける",

            "南京錠", "錠前", "窓から出る", "逃げ道",

            "離せ", "放して", "手を離して", "家に帰る",

            "帰りたい", "仲間を探す", "助けを呼ぶ",

            "抜け道", "ロック解除"

        ),

        "delta": (-12, -6, 12, 18, 6, 12),

        "prompt": "离开/逃跑/探索：警觉、防备、追问目的，逃脱率上升。",

    },

    {

        "name": "betrayal_mockery",

        "keywords": (

            # 中文

            "自作多情", "少自作多情", "别自作多情",

            "骗子", "你骗我", "大骗子", "撒谎", "你说的都是假的",

            "装的", "演的", "假装", "别演了", "演够了没有", "演够了吧",

            "不要脸", "臭不要脸", "自恋", "自恋狂", "你以为你是谁",

            "逗你玩的", "逗你玩儿", "开个玩笑", "只是玩笑",

            "傻子", "傻瓜", "白痴", "笨蛋", "天真", "太天真了",

            "你以为呢", "你想多了", "自作多", "一厢情愿",

            "戏真多", "演技", "戏精", "做作",

            # 英文

            "liar", "you liar", "fake", "pretending", "stop pretending",

            "pathetic", "you fool", "delusional", "you are delusional",

            "just kidding", "just a joke", "only joking",

            "narcissist", "self-obsessed", "get over yourself",

            "acting", "stop acting", "drama queen",

            "you actually believed", "not real", "it was fake",

            "naive", "so naive", "too naive",

            # 日文

            "嘘つき", "嘘でしょ", "演技", "演技ばかり",

            "勘違い", "思い込み", "うぬぼれ", "独りよがり",

            "馬鹿", "バカじゃない", "おめでたい", "妄想",

            "冗談だよ", "からかっただけ", "騙した",

            "一人相撲", "自意識過剰", "茶番"

        ),

        "delta": (-25, -15, 20, 30, -8, -4),

        "prompt": "欺骗或嘲讽：情绪被撕裂，怀疑玩家所有温柔都是陷阱。",

    },

    {

        "name": "morbidity_bond",

        "keywords": (

            # 中文

            "一起死", "死在一起", "一起赴死", "同归于尽",

            "杀了我", "杀了我吧", "你杀了我", "亲手杀了我",

            "死在你手里", "死在你怀里", "一起下地狱", "一起进地狱",

            "永远在一起", "永远融为一体", "合二为一",

            "陪你死", "共赴黄泉", "一起毁灭", "殉情",

            "吃掉我吧", "吃了我", "咽下去", "融进你的血",

            "把我做成标本", "做成标本", "永远陪着你",

            # 英文

            "die together", "kill me", "kill me now", "end me",

            "be with you in death", "eternal bond", "together forever",

            "decay together", "rot together", "take my life",

            "consume me", "devour me", "merge with you",

            "never apart even in death", "death do us part never",

            "preserve me", "make me yours eternally",

            # 日文

            "一緒に死ぬ", "一緒に死のう", "心中しよう",

            "殺して", "殺してください", "あなたの手で死にたい",

            "一つになりたい", "永遠に一緒", "共に滅びよう",

            "食べて", "私を食べて", "溶け合いたい",

            "標本にして", "ずっと一緒にいて"

        ),

        "delta": (12, 18, 5, 10, -10, -5),

        "prompt": "病态迎合：短暂狂喜和依恋增强，但仍保持不安。",

    },

    {

        "name": "danger_talk",

        "keywords": (

            # 中文

            "小刀", "拿刀", "动刀", "砍人", "砍死你", "砍断",

            "自残", "伤害自己", "划开", "划开血管", "割腕",

            "血淋淋", "血淋淋的", "血流成河", "浑身是血",

            "肢解", "五马分尸", "大卸八块", "碎尸",

            "勒死", "掐死", "掐断脖子", "拧断脖子",

            "皮开肉绽", "劈开脑袋", "砸碎骨头",

            "挖出眼睛", "割掉舌头", "切掉手指",

            "放血", "抽血", "灌毒药",

            # 英文

            "knife", "with a knife", "blood everywhere", "bleeding out",

            "cut myself", "self-harm", "slash", "slice open",

            "cut your throat", "stab wound", "decapitate",

            "mutilate", "dismember", "tear apart",

            "smash skull", "break your bones", "gouge eyes",

            "weapon", "torture", "whipping", "strangle",

            # 日文

            "ナイフ", "包丁", "刃物", "血まみれ", "血だらけ",

            "自傷", "切り裂く", "切り刻む", "バラバラにする",

            "首を絞める", "目を抉る", "指を切り落とす",

            "骨を砕く", "皮膚を剥ぐ", "拷問",

            "虐殺", "血の海"

        ),

        "delta": (3, 8, 6, 12, -8, -4),

        "prompt": "危险话题：语气兴奋又不稳定，但避免具体暴力操作描写。",

    },

    {

        "name": "affection",

        "keywords": (

            # 中文

            "最喜欢纱希", "纱希最可爱", "纱希是天使", "纱希真好看",

            "我爱你", "我喜欢你", "爱上你了", "表白", "娶你", "娶你回家",

            "做你的乖猫咪", "一辈子在一起", "永远陪着你",

            "摸摸头", "好乖", "纱希最乖", "听话的纱希",

            "你是我的唯一", "只爱你一个", "心里只有你",

            "想和你在一起", "离不开你", "余生一起走",

            "嫁给我", "娶我", "当我的新娘", "做我的新郎",

            "你对我最好", "被你爱着很幸福",

            # 英文

            "love you", "I love you", "so cute", "you are so cute",

            "beautiful", "you are beautiful", "sweetheart", "darling",

            "marry me", "always together", "stay with me forever",

            "cherish you", "adore you", "my everything",

            "only you", "best thing in my life", "lucky to have you",

            "my love", "cutest girl", "perfect for me",

            # 日文

            "愛してる", "大好き", "紗希が一番", "可愛い",

            "一番可愛い", "結婚しよう", "ずっと一緒", "いい子",

            "優しくしたい", "紗希だけ", "あなただけ",

            "守りたい", "離れたくない", "幸せにする",

            "天使みたい", "お嫁さん"

        ),

        "delta": (10, 18, -18, -8, -8, -4),

        "prompt": "表白/示弱/温柔：安全感上升，语气柔软，但保留一点担心被骗。",

    },

    {

        "name": "rival",

        "keywords": (

            # 中文

            "前女友", "前任", "前男友", "别的女人", "别的女孩",

            "那个女的", "那个女孩", "女同学", "女性朋友", "女同事",

            "女闺蜜", "青梅竹马", "别的男生", "那个男人",

            "狐狸精", "小三", "第三者", "外面有人",

            "认识一个新朋友", "介绍一个人给你", "有个朋友",

            "我的女性朋友", "学姐", "学妹", "她叫什么来着",

            "隔壁班的女生", "同事聚餐", "那个女明星",

            # 英文

            "ex-girlfriend", "ex-boyfriend", "other girl", "that woman",

            "female friend", "girl friend", "colleague", "coworker",

            "someone else", "another person", "that lady",

            "my female coworker", "an old friend of mine",

            "childhood friend", "that actress", "neighbor girl",

            "classmate of mine", "my boss", "roommate",

            # 日文

            "元カノ", "元カレ", "他の女", "あの女", "女友達",

            "幼なじみ", "同僚の女性", "クラスの女子", "先輩",

            "後輩の子", "別の人", "他所の女", "知り合いの女性",

            "サークルの後輩", "飲み会の子", "紹介したい人",

            "隣の席の女性"

        ),

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



from .expanded_content import MOCK_REPLY_BANK, EXACT_SPOKEN_TRANSLATIONS
API_ERROR_REPLIES = {

    "中文": "亲爱的……连接好像断掉了。别怕，纱希还在这里。等系统恢复之前，就先听我说话，好吗？",

    "English": "Darling... the connection seems to have broken. Don't worry. Saki is still here, so listen to me until it comes back, okay?",

    "日本語": "あなた……接続が切れたみたい。大丈夫、紗希はまだここにいるよ。戻るまで、私の声だけ聞いていて。",

}



OFFLINE_TRANSLATION_SUMMARIES = {

    "中文": {

        "default": "亲爱的……你这样跟我说话的时候，纱希会觉得世界安静下来了。再多说一点，好不好？",

        "escape": "亲爱的，你刚才说要走……是开玩笑的吧？看着我，慢慢说，你到底想去哪里？",

        "rival": "那个人是谁呀，亲爱的？你提到他的时候，眼神好像离开了我一小会儿。",

        "affection": "你说爱我……纱希听见了哦。再说一次，好不好？这次看着我的眼睛说。",

        "betrayal_mockery": "骗我的……吗？亲爱的，这种玩笑一点都不好笑。纱希会当真的。",

        "destructive_attack": "这样说很残忍哦，亲爱的。可纱希还是在这里，还是听着你。",

        "extreme_rejection": "亲爱的，别用那种语气命令我。纱希会难过，也会记住。",

        "morbidity_bond": "能和你永远在一起，听起来像梦一样……可是亲爱的，先活着陪我久一点，好吗？",

        "danger_talk": "亲爱的，不要用这种话试探纱希。你知道的，我会把每个字都当真。",

    },

    "English": {

        "default": "I'm listening, my love. Say a little more for me, okay? Your voice makes the room feel less empty.",

        "escape": "You said you wanted to go, my love. That was a joke, wasn't it? Look at me and tell me where you think you need to be.",

        "rival": "Who is that person, darling? Your eyes moved away from me when you mentioned them.",

        "affection": "You love me...? Say it again, please. Look straight at me this time.",

        "betrayal_mockery": "You were lying to me...? My love, that is a cruel joke. Saki believes words like that.",

        "destructive_attack": "That is a cruel thing to say, darling. I am still here. I am still listening.",

        "extreme_rejection": "Don't command me like that, my love. Saki gets sad... and Saki remembers.",

        "morbidity_bond": "Forever with you sounds beautiful. But stay alive with me a little longer first, okay?",

        "danger_talk": "Don't test me with words like that, my love. You know I take every syllable seriously.",

    },

    "日本語": {

        "default": "聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。",

        "escape": "今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？",

        "rival": "その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。",

        "affection": "愛してるって……もう一度言って。今度は、紗希の目を見て。",

        "betrayal_mockery": "嘘だったの……？ ねえ、そういう冗談は痛いよ。紗希、本気にしちゃうから。",

        "destructive_attack": "そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。",

        "extreme_rejection": "そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。",

        "morbidity_bond": "あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。",

        "danger_talk": "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。",

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

        "打死", "弄死",

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





EXACT_SPOKEN_TRANSLATIONS = {

    "中文": {

        "聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。": "我在听哦，你。再多说一点……纱希不想失去那个声音。",

        "うん……その言葉、ちゃんと覚えたよ。あなたの小さな声も、紗希は落とさないから。": "嗯……那句话，我好好记住了哦。即使是你的轻声细语，纱希也不会漏掉的。",

        "今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？": "你刚才说要走……是开玩笑的吧？呐，看着我，你想去哪里？",

        "その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。": "那个人是谁呀？你提到那个名字的时候，好像稍微移开了看着我的视线呢。",

        "愛してるって……もう一度言って。今度は、紗希の目を見て。": "你说爱我……再说一次，好不好？这一次，要看着纱希的眼睛说哦。",

        "嘘だったの……？ ねえ、そういう冗談は痛いよ。紗希、本気にしちゃうから。": "是骗我的吗……？呐，这种玩笑很伤人哦。因为纱希会当真的。",

        "そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。": "那种说法太残忍了哦。但是纱希依然在这里，依然在听着你的声音。",

        "そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。": "别用那种方式命令我。纱希会很难过……而且，会牢牢记住的哦。",

        "あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。": "能和你永远在一起，简直就像做梦一样。但在那之前，先活下去陪我久一点，好吗？",

        "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。": "不要用这样的话试探纱希。因为，你说的每一个字我都会当真的。",

        "I'm listening, my love. Say a little more for me, okay? Your voice makes the room feel less empty.": "我在听哦，我的爱人。再多对我说一点，好不好？你的声音让房间显得不那么空旷了。",

        "Mm... I heard you. Saki will remember every word, even the tiny ones you thought did not matter.": "嗯……我听到了哦。纱希会记住你的每一个字，哪怕是你觉得不重要的细微言语。",

        "You said you wanted to go, my love. That was a joke, wasn't it? Look at me and tell me where you think you need to be.": "你说你想走，我的爱人。那是开玩笑的，对吧？看着我，告诉我想去哪里。",

        "Who is that person, darling? Your eyes moved away from me when you mentioned them.": "那个人是谁呀，亲爱的？你提到他们的时候，眼神从我身上移开了哦。",

        "You love me...? Say it again, please. Look straight at me this time.": "你爱我……？请再说一遍。这次请看着我。",

        "You were lying to me...? My love, that is a cruel joke. Saki believes words like that.": "你在骗我吗……？我的爱人，这种玩笑太残忍了。纱希会把这种话当真的。",

        "That is a cruel thing to say, darling. I am still here. I am still listening.": "这样说很残忍哦，亲爱的。可我还是在这里，我依然在听着。",

        "Don't command me like that, my love. Saki gets sad... and Saki remembers.": "别那样命令我，我的爱人。纱希会难过……而且纱希会记住的。",

        "Forever with you sounds beautiful. But stay alive with me a little longer first, okay?": "能和你永远在一起听起来很美妙……但先活下去陪我久一点，好吗？",

        "Don't test me with words like that, my love. You know I take every syllable seriously.": "别用那样的话试探我，我的爱人。你知道的，我会把你的每一个字都当真。",
        "嘘つき……そんなはずない……アナタは私のものだ……絶対に離さない……": "骗人……不可能有那种事……你是属于我的……绝对不放手……",
        "ふざけないで...私の目を見て": "别开玩笑了……看着我的眼睛。",
        "もしもう一度そんなことを言ったら...二度とドア的外に出られなくなるよ": "要是再敢说一次这种话……就再也别想踏出房门半步了。",
        "そう...そうなんだね......": "是吗……原来是这样啊……",
        "じゃあ纱希も、アナタのいらないこの世界を、いらなくするね。": "那么纱希，也就把这个没有你的世界一起带走好了。"

    },

    "English": {

        "聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。": "I'm listening, my love. Speak a little more. Saki doesn't want to lose that voice.",

        "うん……その言葉、ちゃんと覚えたよ。あなたの小さな声も、紗希は落とさないから。": "Mm... I remembered those words. Even your quietest whisper, Saki won't let it go.",

        "今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？": "You just said you wanted to leave...? It's a joke, right? Hey, look at me. Where do you want to go?",

        "その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。": "Who is that person? When you said that name, I felt like you looked away from me for just a moment.",

        "愛してるって……もう一度言って。今度は、紗希の目を見て。": "You love me...? Say it again, please. Look straight into Saki's eyes this time.",

        "嘘だったの……？ ねえ、そういう冗談は痛よ。紗希、本気にしちゃうから。": "Were you lying...? Hey, that kind of joke hurts. Saki will take it seriously, you know.",

        "そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。": "Saying it that way is cruel. But Saki is still here, still listening to your voice.",

        "そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。": "Don't command me like that. Saki will be sad... and Saki will remember it well.",

        "あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。": "If I can be with you forever, it sounds like a dream. But before that, stay alive and stay by my side a little longer, okay?",

        "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。": "Don't test Saki with those words. Because I will take every single letter you say seriously.",

        "亲爱的……你这样跟我说话的时候，纱希会觉得世界安静下来了。再多说一点，好不好？": "I'm listening, my love. Say a little more for me, okay? Your voice makes the room feel less empty.",

        "嗯……我在听哦。你说的每个字，纱希都会好好记住，一个都不会弄丢。": "Mm... I heard you. Saki will remember every word, even the tiny ones you thought did not matter.",

        "亲爱的，你刚刚说要走……是开玩笑的吧？看着我，慢慢说，你到底想去哪里？": "You said you wanted to go, my love. That was a joke, wasn't it? Look at me and tell me where you think you need to be.",

        "外面很危险啊，亲爱的。留在纱希身边不好吗？这里至少只有我会一直看着你。": "The outside world is very dangerous, my love. Isn't it nice to stay by Saki's side? At least only I will look at you here.",

        "那个人是谁呀，亲爱的？你提到他的时候，眼神好像离开了我一小会儿。": "Who is that person, darling? Your eyes moved away from me when you mentioned them.",

        "你说爱我……纱希听见了哦。再说一次，好不好？这次看着我的眼睛说。": "You said you love me... Saki heard you. Say it again, please. Look straight at me this time.",

        "亲爱的真乖……只要你不离开，纱希也可以一直、一直温柔下去。": "My love is so good... as long as you don't leave, Saki can stay gentle forever and ever.",

        "骗我的……吗？亲爱的，这种玩笑一点都不好笑。纱希会当真的。": "You were lying to me...? My love, that is a cruel joke. Saki believes words like that.",

        "这样说很残忍哦，亲爱的。可纱希还是在这里，还是听着你。": "That is a cruel thing to say, darling. I am still here. I am still listening.",

        "亲爱的，别用那种语气命令我。纱希会难过，也会记住。": "Don't command me like that, my love. Saki gets sad... and Saki remembers.",

        "能和你永远在一起，听起来像梦一样……可是亲爱的，先活着陪我久一点，好吗？": "Forever with you sounds beautiful. But stay alive with me a little longer first, okay?",

        "亲爱的，不要用这种话试探纱希。你知道的，我会把每个字都当真。": "Don't test me with words like that, my love. You know I take every syllable seriously."

    },

    "日本語": {

        "亲爱的……你这样跟我说话的时候，纱希会觉得世界安静下来了。再多说一点，好不好？": "聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。",

        "嗯……我在听哦。你说的每个字，纱希都会好好记住，一个都不会弄丢。": "うん……その言葉、ちゃんと覚えたよ。あなたの小さな声も、紗希は落とさないから。",

        "亲爱的，你刚刚说要走……是开玩笑的吧？看着我，慢慢说，你到底想去哪里？": "今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？",

        "那个人是谁呀，亲爱的？你提到他的时候，眼神好像离开了我一小会儿。": "その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。",

        "你说爱我……纱希听见了哦。再说一次，好不好？这次看着我的眼睛说。": "愛してるって……もう一度言って。今度は、紗希の目を見て。",

        "骗我的……吗？亲爱的，这种玩笑一点都不好笑。纱希会当真的。": "嘘だったの……？ ねえ、そういう冗談は痛いよ。紗希、本気にしちゃうから。",

        "这样说很残忍哦，亲爱的。可纱希还是在这里，还是听着你。": "そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。",

        "亲爱的，别用那种语气命令我。纱希会难过，也会记住。": "そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。",

        "能和你永远在一起，听起来像梦一样……可是亲爱的，先活着陪我久一点，好吗？": "あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。",

        "亲爱的，不要用这种话试探纱希。你知道的，我会把每个字都当真。": "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。",

        "I'm listening, my love. Say a little more for me, okay? Your voice makes the room feel less empty.": "聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。",

        "Mm... I heard you. Saki will remember every word, even the tiny ones you thought did not matter.": "うん……その言葉、ちゃんと覚えたよ。あなたの小さな声も、紗希は落とさないから。",

        "You said you wanted to go, my love. That was a joke, wasn't it? Look at me and tell me where you think you need to be.": "今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？",

        "Who is that person, darling? Your eyes moved away from me when you mentioned them.": "その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。",

        "You love me...? Say it again, please. Look straight at me this time.": "愛してるって……もう一度言って。今度は、紗希の目を見て。",

        "You were lying to me...? My love, that is a cruel joke. Saki believes words like that.": "嘘だったの……？ ねえ、そういう冗談は痛いよ。紗希、本気にしちゃうから。",

        "That is a cruel thing to say, darling. I am still here. I am still listening.": "そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。",

        "Don't command me like that, my love. Saki gets sad... and Saki remembers.": "そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。",

        "Forever with you sounds beautiful. But stay alive with me a little longer first, okay?": "あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。",

        "Don't test me with words like that, my love. You know I take every syllable seriously.": "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。"

    }

}



def build_offline_translation_line(intent_name, user_lang, spoken_text=None):

    user_lang = normalize_language(user_lang)

    

    # Try exact match first

    if spoken_text:

        # Strip <think>...</think> block if present in spoken_text

        clean_spoken = re.sub(r"<think>.*?</think>", "", spoken_text, flags=re.S | re.I)

        # Strip any other brackets or spacing

        clean_spoken = clean_spoken.strip()

        

        # Exact spoken match

        lang_trans = EXACT_SPOKEN_TRANSLATIONS.get(user_lang, {})

        if clean_spoken in lang_trans:

            return f"\n（{lang_trans[clean_spoken]}）"

            

        # Try finding a key that is a substring of clean_spoken or vice versa

        for original, translation in lang_trans.items():

            if original in clean_spoken or clean_spoken in original:

                return f"\n（{translation}）"

                

        # Custom short default default match

        if user_lang == "中文":

            if "って言ったね。ちゃんと聞こえたよ。" in clean_spoken:

                match = re.search(r"今、[『\"'](.*)[』\"']って言ったね", clean_spoken)

                if match:

                    extracted_val = match.group(1)

                    return f"\n（你刚才说了“{extracted_val}”呢。我听得很清楚哦。再多让纱希听听你的声音吧。）"

            if "I heard it, my love. Say another small thing" in clean_spoken:

                match = re.search(r"You just said [\"'](.*)[\"']\.\.\. I heard it", clean_spoken)

                if match:

                    extracted_val = match.group(1)

                    return f"\n（亲爱的刚才说“{extracted_val}”……纱希听见了哦。再说一句给我，好不好。）"

                    

    # Fallback to the immersive first-person intent summaries

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

    return text.rstrip() + build_offline_translation_line(intent["name"], user_lang, text)

