# -*- coding: utf-8 -*-
import re

file_path = "resources/game_constants.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace OFFLINE_TRANSLATION_SUMMARIES
target_summaries = """OFFLINE_TRANSLATION_SUMMARIES = {
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
}"""

# Normalize line endings for replacement
content_norm = content.replace("\r\n", "\n")
target_norm = target_summaries.replace("\r\n", "\n")

new_summaries = """OFFLINE_TRANSLATION_SUMMARIES = {
    "中文": {
        "default": "亲爱的……你这样跟我说话的时候，纱希会觉得世界安静下来了。再多说一点，好不好？",
        "escape": "亲爱的，你刚才说要走……是开玩笑的吧？看着我，慢慢说，你到底想去哪里？",
        "rival": "那个人是谁呀，亲爱的？你提到他的时候，眼神好像离开了我小会儿。",
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
        "morbidity_bond": "あなたと永遠にいられるなら、夢みたい。配置その前に、もう少し生きてそばにいて。",
        "danger_talk": "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。",
    },
}"""

if target_norm in content_norm:
    content_norm = content_norm.replace(target_norm, new_summaries)
    print("OFFLINE_TRANSLATION_SUMMARIES replaced successfully!")
else:
    print("Could not find OFFLINE_TRANSLATION_SUMMARIES in file!")

# 2. Add EXACT_SPOKEN_TRANSLATIONS and update build_offline_translation_line
exact_spoken_trans_code = """EXACT_SPOKEN_TRANSLATIONS = {
    "中文": {
        # Japanese -> Chinese
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

        # English -> Chinese
        "I'm listening, my love. Say a little more for me, okay? Your voice makes the room feel less empty.": "我在听哦，我的爱人。再多对我说一点，好不好？你的声音让房间显得不那么空旷了。",
        "Mm... I heard you. Saki will remember every word, even the tiny ones you thought did not matter.": "嗯……我听到了哦。纱希会记住你的每一个字，哪怕是你觉得不重要的细微言语。",
        "You said you wanted to go, my love. That was a joke, wasn't it? Look at me and tell me where you think you need to be.": "你说你想走，我的爱人。那是开玩笑的，对吧？看着我，告诉我想去哪里。",
        "Who is that person, darling? Your eyes moved away from me when you mentioned them.": "那个人是谁呀，亲爱的？你提到他们的时候，眼神从我身上移开了哦。",
        "You love me...? Say it again, please. Look straight at me this time.": "你爱我……？请再说一遍。这次请看着我。",
        "You were lying to me...? My love, that is a cruel joke. Saki believes words like that.": "你在骗我吗……？我的爱人，这种玩笑太残忍了。纱希会把这种话当真的。",
        "That is a cruel thing to say, darling. I am still here. I am still listening.": "这样说很残忍哦，亲爱的。可我还是在这里，我依然在听着。",
        "Don't command me like that, my love. Saki gets sad... and Saki remembers.": "别那样命令我，我的爱人。纱希会难过……而且纱希会记住的。",
        "Forever with you sounds beautiful. But stay alive with me a little longer first, okay?": "能和你永远在一起听起来很美妙……但先活下去陪我久一点，好吗？",
        "Don't test me with words like that, my love. You know I take every syllable seriously.": "别用那样的话试探我，我的爱人。你知道的，我会把你的每一个字都当真。"
    },
    "English": {
        # Japanese -> English
        "聞いているよ、あなた。もう少しだけ話して。紗希は、その声を失くしたくないの。": "I'm listening, my love. Speak a little more. Saki doesn't want to lose that voice.",
        "うん……その言葉、ちゃんと覚えたよ。あなたの小さな声も、紗希は落とさないから。": "Mm... I remembered those words. Even your quietest whisper, Saki won't let it go.",
        "今、出ていくって言った……？ 冗談だよね。ねえ、私を見て。どこへ行きたいの？": "You just said you wanted to leave...? It's a joke, right? Hey, look at me. Where do you want to go?",
        "その人、誰なの？ あなたがその名前を言う時、少しだけ私を見なくなった気がしたの。": "Who is that person? When you said that name, I felt like you looked away from me for just a moment.",
        "愛してるって……もう一度言って。今度は、紗希の目を見て。": "You love me...? Say it again, please. Look straight into Saki's eyes this time.",
        "嘘だったの……？ ねえ、そういう冗談は痛いよ。紗希、本気にしちゃうから。": "Were you lying...? Hey, that kind of joke hurts. Saki will take it seriously, you know.",
        "そんな言い方、ひどいよ。だけど紗希はここにいる。あなたの声を、まだ聞いている。": "Saying it that way is cruel. But Saki is still here, still listening to your voice.",
        "そんなふうに命令しないで。紗希は悲しくなるし……ちゃんと覚えてしまうよ。": "Don't command me like that. Saki will be sad... and Saki will remember it well.",
        "あなたと永遠にいられるなら、夢みたい。配置その前に、もう少し生きてそばにいて。": "If I can be with you forever, it sounds like a dream. But before that, stay alive and stay by my side a little longer, okay?",
        "あなたと永遠にいられるなら、夢みたい。でもその前に、もう少し生きてそばにいて。": "If I can be with you forever, it sounds like a dream. But before that, stay alive and stay by my side a little longer, okay?",
        "そういう言葉で紗希を試さないで。私は、あなたの一文字まで本気にするから。": "Don't test Saki with those words. Because I will take every single letter you say seriously.",

        # Chinese -> English
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
        # Chinese -> Japanese
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

        # English -> Japanese
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
"""

# Replace definition of build_offline_translation_line
old_build_func = """def build_offline_translation_line(intent_name, user_lang):
    user_lang = normalize_language(user_lang)
    summaries = OFFLINE_TRANSLATION_SUMMARIES[user_lang]
    return f"\\n（{summaries.get(intent_name, summaries['default'])}）\""""

new_build_func = exact_spoken_trans_code + """
def build_offline_translation_line(intent_name, user_lang, spoken_text=None):
    user_lang = normalize_language(user_lang)
    
    # Try exact match first
    if spoken_text:
        # Strip <think>...</think> block if present in spoken_text
        clean_spoken = re.sub(r"<think>.*?</think>", "", spoken_text, flags=re.S | re.I)
        clean_spoken = re.sub(r"\\|\\|.*?\\|\\|", "", clean_spoken, flags=re.S)
        clean_spoken = clean_spoken.strip()
        
        # Exact spoken match
        lang_trans = EXACT_SPOKEN_TRANSLATIONS.get(user_lang, {})
        if clean_spoken in lang_trans:
            return f"\\n（{lang_trans[clean_spoken]}）"
            
        # Try finding a key that is a substring of clean_spoken or vice versa
        for original, translation in lang_trans.items():
            if original in clean_spoken or clean_spoken in original:
                return f"\\n（{translation}）"
                
        # Custom default with embedded user_input match
        if user_lang == "中文":
            if "って言ったね。ちゃんと聞こえたよ。" in clean_spoken:
                match = re.search(r"今、[『\\"'](.*)[』\\"']って言ったね", clean_spoken)
                if match:
                    extracted_val = match.group(1)
                    return f"\\n（你刚才说了“{extracted_val}”呢。我听得很清楚哦。再多让纱希听听你的声音吧。）"
            if "I heard it, my love. Say another small thing" in clean_spoken:
                match = re.search(r"You just said [\\"'](.*)[\\"']\\\\.\\\\.\\\\. I heard it", clean_spoken)
                if match:
                    extracted_val = match.group(1)
                    return f"\\n（亲爱的刚才说“{extracted_val}”……纱希听见了哦。再说一句给我，好不好。）"
                    
    # Fallback to the immersive first-person intent summaries
    summaries = OFFLINE_TRANSLATION_SUMMARIES[user_lang]
    return f"\\n（{summaries.get(intent_name, summaries['default'])}）"
"""

# Match the old build_offline_translation_line definition and insert the EXACT_SPOKEN_TRANSLATIONS dictionary along with it
old_def = """def build_offline_translation_line(intent_name, user_lang):
    user_lang = normalize_language(user_lang)
    summaries = OFFLINE_TRANSLATION_SUMMARIES[user_lang]
    return f"\\n（{summaries.get(intent_name, summaries['default'])}）\""""

# Let's search by locating the exact lines 645-648:
old_def_exact = """def build_offline_translation_line(intent_name, user_lang):
    user_lang = normalize_language(user_lang)
    summaries = OFFLINE_TRANSLATION_SUMMARIES[user_lang]
    return f"\\n（{summaries.get(intent_name, summaries['default'])}）\""""

# Find real definition using regex
pattern = r"def build_offline_translation_line\(intent_name, user_lang\):\n\s+user_lang = normalize_language\(user_lang\)\n\s+summaries = OFFLINE_TRANSLATION_SUMMARIES\[user_lang\]\n\s+return f\"\\n（\{summaries\.get\(intent_name, summaries\['default'\]\)\}）\""

if re.search(pattern, content_norm):
    content_norm = re.sub(pattern, new_build_func.replace("\\", "\\\\"), content_norm)
    print("build_offline_translation_line replaced successfully!")
else:
    # Try literal match
    literal_old = "def build_offline_translation_line(intent_name, user_lang):\n    user_lang = normalize_language(user_lang)\n    summaries = OFFLINE_TRANSLATION_SUMMARIES[user_lang]\n    return f\"\\n（{summaries.get(intent_name, summaries['default'])}）\""
    if literal_old in content_norm:
        content_norm = content_norm.replace(literal_old, new_build_func)
        print("build_offline_translation_line replaced literally!")
    else:
        print("Could not find build_offline_translation_line definition in file!")

# 3. Update ensure_readability_translation to pass text as the third parameter
old_ensure = "return text.rstrip() + build_offline_translation_line(intent[\"name\"], user_lang)"
new_ensure = "return text.rstrip() + build_offline_translation_line(intent[\"name\"], user_lang, text)"

if old_ensure in content_norm:
    content_norm = content_norm.replace(old_ensure, new_ensure)
    print("ensure_readability_translation call updated!")
else:
    print("Could not find ensure_readability_translation call!")

# Save the modifications
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content_norm.replace("\n", "\r\n"))

print("Patching completed successfully!")
