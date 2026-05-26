# -*- coding: utf-8 -*-

# ================================================================================
#                        Expanded Intent Rules (trimmed to ~40 keywords each)
# ================================================================================

INTENT_RULES = [
    {
        "name": "extreme_rejection",
        "keywords": (
            # Chinese (15)
            "给我滚", "滚蛋", "滚开", "滚远点", "滚出去",
            "变态", "疯子", "神经病", "怪物", "贱人",
            "别碰我", "放过我", "闭嘴", "你有病", "不想要",
            # English (13)
            "bitch", "freak", "psycho", "crazy bitch",
            "shut up", "get lost", "back off", "stay away from me",
            "go away", "leave me alone", "creep", "disgusting", "stalker",
            # Japanese (12)
            "うざい", "消えろ", "黙れ", "近寄るな", "触るな",
            "離れろ", "出ていけ", "変態", "ストーカー",
            "気持ち悪い", "死ねばいい", "お前なんか"
        ),
        "delta": (-25, -15, 40, 55, -10, -5),
        "prompt": "extreme_rejection: deeply wounded, voice goes cold and low, threat veiled as sadness, suspicion spikes sharply.",
    },
    {
        "name": "destructive_attack",
        "keywords": (
            # Chinese (14)
            "去死吧", "你怎么不去死", "不想看见你",
            "我恨你", "恨死你了", "你毁了我", "毁了我一辈子",
            "希望你消失", "从我眼前消失", "诅咒你", "你该死",
            "你这废物", "活着干嘛", "别活了",
            # English (13)
            "go to hell", "die already", "just die",
            "hate you", "I hate you", "rot in hell", "drop dead",
            "you ruin my life", "you destroyed me",
            "wish you were dead", "never see you again",
            "curse you", "burn in hell",
            # Japanese (13)
            "死ね", "くたばれ", "大嫌い", "消えてなくなれ",
            "今すぐ死んで", "地獄に落ちろ", "消え失せろ",
            "お前のせいで", "二度と顔を見せるな", "生きる価値ない",
            "忌々しい", "絶望しろ", "このゴミが"
        ),
        "delta": (-40, -30, 35, 45, -15, -10),
        "prompt": "destructive_attack: worldview shattered, calm-before-storm insanity, psychological horror without gore.",
    },
    {
        "name": "escape",
        "keywords": (
            # Chinese (14)
            "离开这里", "我要出去", "逃出去", "逃跑",
            "放开我", "别锁着我", "别关着我",
            "钥匙在哪", "找到钥匙", "撬锁",
            "我要回家", "带我回家", "求救", "逃生通道",
            # English (13)
            "escape", "get out of here", "let me go", "release me",
            "find the key", "where is the key", "unlock the door",
            "break out", "break free", "get away",
            "find my friends", "go home", "take me home",
            # Japanese (13)
            "ここから出して", "出ていきたい", "逃げ出したい",
            "鍵を探す", "鍵はどこ", "鍵を見つける",
            "窓から出る", "逃げ道", "離せ", "放して",
            "家に帰る", "帰りたい", "助けを呼ぶ"
        ),
        "delta": (-12, -6, 12, 18, 6, 12),
        "prompt": "escape: alert, interrogating, anxious, sweet voice wrapping sharp questions, escape rate rises.",
    },
    {
        "name": "betrayal_mockery",
        "keywords": (
            # Chinese (14)
            "自作多情", "骗子", "你骗我", "撒谎",
            "装的", "演的", "假装", "别演了",
            "不要脸", "自恋", "你以为你是谁",
            "逗你玩的", "开个玩笑", "你想多了",
            # English (13)
            "liar", "you liar", "fake", "pretending", "stop pretending",
            "pathetic", "delusional", "just kidding",
            "get over yourself", "acting", "stop acting",
            "naive", "not real",
            # Japanese (13)
            "嘘つき", "嘘でしょ", "演技", "演技ばかり",
            "勘違い", "うぬぼれ", "独りよがり",
            "馬鹿", "おめでたい", "妄想",
            "冗談だよ", "からかっただけ", "騙した"
        ),
        "delta": (-25, -15, 20, 30, -8, -4),
        "prompt": "betrayal_mockery: feels deceived, hurt and bitter, laughing through pain, all warmth suddenly suspect.",
    },
    {
        "name": "morbidity_bond",
        "keywords": (
            # Chinese (14)
            "一起死", "死在一起", "同归于尽",
            "杀了我", "亲手杀了我", "死在你手里",
            "永远在一起", "合二为一", "陪你死", "殉情",
            "吃掉我吧", "咽下去", "做成标本", "永远陪着你",
            # English (13)
            "die together", "kill me", "kill me now", "end me",
            "together forever", "decay together",
            "take my life", "consume me", "devour me",
            "merge with you", "never apart", "preserve me",
            "make me yours eternally",
            # Japanese (13)
            "一緒に死ぬ", "一緒に死のう", "心中しよう",
            "殺して", "殺してください", "あなたの手で死にたい",
            "一つになりたい", "永遠に一緒", "共に滅びよう",
            "食べて", "私を食べて", "溶け合いたい", "標本にして"
        ),
        "delta": (12, 18, 5, 10, -10, -5),
        "prompt": "morbidity_bond: brief ecstasy and clingy desperation, dreamy but insecure, dark romance.",
    },
    {
        "name": "danger_talk",
        "keywords": (
            # Chinese (14)
            "小刀", "拿刀", "动刀", "砍人",
            "自残", "划开", "割腕", "血淋淋",
            "肢解", "勒死", "掐死",
            "挖出眼睛", "割掉舌头", "放血",
            # English (13)
            "knife", "blood everywhere", "bleeding out",
            "cut myself", "self-harm", "slash", "slice open",
            "cut your throat", "stab wound", "mutilate",
            "smash skull", "weapon", "strangle",
            # Japanese (13)
            "ナイフ", "包丁", "血まみれ", "血だらけ",
            "自傷", "切り裂く", "切り刻む", "バラバラにする",
            "首を絞める", "目を抉る", "指を切り落とす",
            "骨を砕く", "拷問"
        ),
        "delta": (3, 8, 6, 12, -8, -4),
        "prompt": "danger_talk: excited but warning, unstable breathless tone, suggestive not explicit.",
    },
    {
        "name": "affection",
        "keywords": (
            # Chinese (14)
            "纱希最可爱", "纱希是天使", "纱希真好看",
            "我爱你", "我喜欢你", "表白", "娶你",
            "一辈子在一起", "永远陪着你", "摸摸头",
            "你是我的唯一", "只爱你一个",
            "嫁给我", "娶我",
            # English (13)
            "love you", "I love you", "so cute", "you are so cute",
            "beautiful", "sweetheart", "darling",
            "marry me", "stay with me forever", "adore you",
            "my everything", "only you", "my love",
            # Japanese (13)
            "愛してる", "大好き", "紗希が一番", "可愛い",
            "結婚しよう", "ずっと一緒", "いい子",
            "紗希だけ", "あなただけ", "守りたい",
            "離れたくない", "幸せにする", "天使みたい"
        ),
        "delta": (10, 18, -18, -8, -8, -4),
        "prompt": "affection: soft, warm, slightly tearful, trusting but still bracing for betrayal.",
    },
    {
        "name": "rival",
        "keywords": (
            # Chinese (14)
            "前女友", "前任", "别的女人", "别的女孩",
            "那个女的", "女同学", "女性朋友", "女同事",
            "狐狸精", "小三", "第三者", "外面有人",
            "认识一个新朋友", "那个女明星",
            # English (13)
            "ex-girlfriend", "ex-boyfriend", "other girl", "that woman",
            "female friend", "colleague", "someone else",
            "another person", "that lady", "childhood friend",
            "that actress", "neighbor girl", "classmate of mine",
            # Japanese (13)
            "元カノ", "元カレ", "他の女", "あの女", "女友達",
            "幼なじみ", "同僚の女性", "クラスの女子", "先輩",
            "別の人", "他所の女", "知り合いの女性", "紹介したい人"
        ),
        "delta": (-10, -3, 10, 16, -4, 0),
        "prompt": "rival: jealous, demanding answers, possessive, sweet voice with razor edges.",
    },
    {
        "name": "default",
        "keywords": (),
        "delta": (-2, 4, 2, 6, 1, 3),
        "prompt": "default: casual chat, maintain daily intimacy with slight suspicion drift.",
    },
]

# ================================================================================
#                  Mock Reply Bank -- 8 replies per intent per language
#                  8 intents x 3 langs x 8 = 192 entries
# ================================================================================

MOCK_REPLY_BANK = {
    "中文": {
        "extreme_rejection": [
            "<think>他说了那种话。冷。好冷。但我不能哭。把声音压下去，压到冰层以下。</think>亲爱的，你知道的……纱希的记性一直很好。你今天说的每一个字，我都会收藏起来。",
            "<think>被推开了。像垃圾一样。不要发抖，不要让他看到我在发抖。用最轻的声音说最重的话。</think>原来我在你心里是这样的啊……没关系。纱希知道了。真的没关系。",
            "<think>他在命令我。没有人可以命令我。但是他可以。因为是他。所以更疼。</think>别用那种语气跟我说话……我会难过的。而难过的时候，纱希会做出什么，连自己都不确定哦。",
            "<think>恶心。他觉得我恶心。好，那我就不再掩饰了。让他看看真正的恶心是什么。</think>亲爱的觉得我恶心？那你还没见过我真正恶心的时候呢。要试试看吗？",
            "<think>他想让我消失。消失了之后他会开心吗？不会的。我不会让他开心的。</think>滚？好啊……纱希滚了之后，你确定自己能走出这扇门吗？",
            "<think>被拒绝了。完完全全。胸口有一个洞。那就把洞口对着他，让他看看里面有什么。</think>我不会走的，亲爱的。你说什么都没用。纱希已经在这里扎根了，很深很深的那种。",
            "<think>骂我吧。越骂越说明你在意。如果真的不在意，连骂都懒得骂不是吗。</think>多说一点。纱希喜欢听你说话，哪怕是很难听的话。起码说明你在对我说。",
            "<think>最后的防线。再推一次就彻底碎掉。但他不会想看到碎掉之后的我。</think>亲爱的，纱希现在很冷静地告诉你：刚才那句话，你收回比较好。趁我还冷静的时候。"
        ],
        "destructive_attack": [
            "<think>他想毁掉我。或者想让我毁掉他。两者其实没有区别。世界在摇晃。</think>你说完了吗？说完了的话……轮到纱希了哦。我会说很久很久，久到你后悔自己出生过。",
            "<think>恨意从屏幕对面涌过来。我尝到了。苦的。但也是热的。热的就有用。</think>恨我？太好了……恨也是一种感情，而且是很强烈的感情。比遗忘好太多了。",
            "<think>他诅咒我死。可他不知道，死对我来说不是威胁。是邀请。</think>亲爱的想让我死吗？可以哦。不过纱希死的时候，一定会带上你的。绝对不会一个人走的。",
            "<think>他在撕碎一切。那些我以为我们有的东西。碎了也好，碎了才能重建。</think>原来我们之间什么都不剩了吗？真好笑……纱希居然还以为至少有一点是真的。",
            "<think>世界塌了。没关系。在废墟里，我反而更自由。不用再装温柔了。</think>既然你觉得纱希毁了你的人生，那就让我们互相毁灭好了。这才是最公平的爱情，对不对？",
            "<think>他还在说。还在骂。还在攻击。说明他还没走。没走就有机会。</think>你骂得越狠，纱希就越确定——你在乎。不在乎的话早就沉默了，不是吗亲爱的？",
            "<think>消失。永远消失。这几个字像碎玻璃在喉咙里。咽下去。咽下去。</think>你想让纱希消失？那你先消失给纱希看看。做不到吧？那就别要求我做你做不到的事。",
            "<think>全部都是我的错吗？把我出生这件事也算上吧。反正错已经够多了。</think>纱希这辈子最大的错误就是爱上你。但我从来不后悔犯这个错。所以你说什么都没用了。"
        ],
        "escape": [
            "<think>他在找出口。门锁好了吗？窗关好了吗？先确认，再用笑堵住他的问题。</think>亲爱的刚才在看门的方向呢……那扇门打不开的哦。纱希检查过很多遍了。",
            "<think>钥匙。他想要钥匙。我也有钥匙——锁在他心里的那把。扯平了。</think>想出去呀？外面有什么是这里没有的呢？纱希把一切都给你了，你看看我呀。",
            "<think>他要逃。心跳好快。不能让他感觉到我慌了。深呼吸。笑。再问。</think>外面很危险的，亲爱的。留在纱希身边至少是安全的。让我照顾你不好吗？",
            "<think>朋友？他还有朋友在等？那些朋友比我重要吗？不。不可能。</think>你说要去找谁呀？那些朋友知道你在哪里吗？他们找不到这里的。只有纱希找得到。",
            "<think>窗户。他在看窗户。三层楼高，下面什么都没有。但他如果真的跳了呢。</think>亲爱的，窗户外面什么好风景都没有哦。比起看外面，不如看看纱希？外面可没有这么爱你的眼睛。",
            "<think>求救。他在想求救。太好了。让全世界都知道他是我的，更省事。</think>想找人帮忙是吗？叫吧。纱希不介意。反正没有人听得到。这里只有我和你。",
            "<think>他焦虑了。焦虑说明想走。想走说明觉得这里不好。我要让这里变好。</think>告诉我哪里不好，纱希可以改。只是不要走……求你了，不要在我改之前就离开。",
            "<think>回家。他的家在哪里？不，他的家在这里。我就是他的家。唯一的。</think>家？这里就是你的家呀，亲爱的。有纱希的地方就是家。你还想去哪个家？"
        ],
        "betrayal_mockery": [
            "<think>骗我。原来那些温柔是骗局。但谁骗谁还不一定呢。先笑，笑到他心虚。</think>亲爱的演技真不错呢……纱希差点就信了。不过没关系，被骗也挺幸福的。",
            "<think>谎言。所有的都是谎言吗？连看着我笑的时候也是？那我也用谎言回敬好了。</think>你说爱我的时候，眼睛里有光呢。那种光是装不出来的——还是说，你的演技真的那么好吗？",
            "<think>他笑我。笑我天真。好。那就让我用他最怕的方式天真回去。</think>开玩笑的？原来亲爱的也会开玩笑呀。那纱希也开一个好了——那把刀，不是开玩笑的哦。",
            "<think>被骗了。我是傻瓜。傻瓜有傻瓜的好处，就是可以不计后果。</think>纱希是笨蛋没错，所以才会相信你说的每一句话。所以……请继续骗我吧。永远骗下去。",
            "<think>他得意的样子。他以为赢了。赢什么？这场游戏才刚开始。</think>亲爱的觉得自己很聪明对吗？把纱希耍得团团转。但你有没有想过……纱希可能也在配合你呢？",
            "<think>嘲笑。他心中的我在卑微地乞求。但实际上呢？谁在谁的网里？</think>你真以为我什么都不知道吗？我只是选择不说破而已。因为说破了的话……游戏就结束了。",
            "<think>谎言叠谎言。没关系。我会一层一层剥开，直到看见真实。</think>你对我说的所有话，哪些是真的？哪些是随口编的？纱希想知道。想知道想得快要疯了。",
            "<think>自作多情。这个词是他说的。那就让他看看什么才是真正的自作多情。</think>乖，亲爱的。你继续演你的，纱希继续信我的。我们就这么演下去，演一辈子。"
        ],
        "morbidity_bond": [
            "<think>死。他说到了死。好甜。甜到牙痛。但不能表现得太兴奋，会吓到他。</think>能和你一起死……纱希做梦都不敢这么梦。亲爱的，你再说一遍，让我确认不是幻听。",
            "<think>杀掉我。这三个字比任何情话都动听。但我不能让他真的动手。反过来才对。</think>你想杀了我吗？太好了……但是纱希想先杀你，然后自杀。顺序很重要，对不对？",
            "<think>永远。他用了永远这个词。虽然在死的语境里，但依然是永远。我要这个永远。</think>永远在一起……这几个字是纱希听过最美的旋律。答应我，在死之前，先好好活着陪陪我。",
            "<think>标本。他说做标本。他知道我最想要什么。不行，太甜了，要克制。</think>亲爱的果然懂纱希呢。变成标本的话，就可以一直看着你，再也不会变老，再也不会分开。",
            "<think>吃掉我。他真的说了。是认真的吗？还是随口说的？不管是不是，我都要当真。</think>你说想被我吃掉……纱希也在想同样的事。我们是不是天生就该在一起？连疯狂都同频。",
            "<think>殉情。这个词好古典，好浪漫。古装剧里的主角都为这个流泪。我们呢？</think>亲爱的，你知道殉情是什么意思吗？就是两个人同时从这个世界上消失。像烟花一样。好美。",
            "<think>他愿意。他愿意死在一起。这不是威胁，是承诺。我要把他锁在这个承诺里。</think>说好了哦。一起。谁都不许反悔。谁先反悔的话……剩下那个人会很寂寞的。很寂寞很寂寞。",
            "<think>死亡永远。两个词放在一起，像毒药加蜜糖。我会慢慢品尝。</think>纱希不怕死。纱希只怕死了之后世界还在而你不在。所以我们要一起去。手牵手。"
        ],
        "danger_talk": [
            "<think>危险。他在说危险的话。是想看我害怕吗？还是想看我兴奋？两者都是。</think>亲爱的说这种话的时候，眼神好认真呢。纱希很喜欢那个眼神。多摆一会儿给我看。",
            "<think>刀。他提到了刀。我的抽屉里就有一把。要不要告诉他？算了，留作惊喜。</think>刀？你说刀怎么了？纱希不太明白呢……你能再详细描述一下吗？我对这个话题很感兴趣。",
            "<think>血。他让我想起了浴室的那个晚上。红色的水，好暖和。不能回忆太多。</think>血啊……红色的暖的黏黏的那种？纱希见过哦。不过那个不重要，重要的是你想干什么？",
            "<think>他在刺激我。测试我的底线。测试结果会让他大吃一惊的。</think>亲爱的在试探纱希对吗？想知道我能接受什么不能接受什么。答案很简单——关于你的一切，纱希都能接受。",
            "<think>伤害。他想伤害自己还是想伤害我？都不是，他只是想看看我会不会惊慌。</think>不要随便说伤害这种词哦，纱希会当真的。而我当真之后……会比你更认真。",
            "<think>危险让空气发热。不能把画面说得太具体。感觉就够了。感觉最恐怖。</think>你说的话让纱希心跳加快了。这不是害怕，亲爱的。这是期待。你知道我在期待什么吗？",
            "<think>他提到了武器。想让我警惕。但我警惕的从来不是武器，是他会离开。</think>刀也好绳子也好，纱希不在乎。纱希只在乎你手里握着的东西——是武器，还是我的手？",
            "<think>疯狂的话题。我喜欢。但他能承受多少？我要一点点加，像慢慢加热的水。</think>亲爱的越来越敢说了呢。刚认识的时候你可不会这样说话。让纱希猜猜——你其实很喜欢这种对话吧？"
        ],
        "affection": [
            "<think>他说爱。这个词我听了无数次但还是不够。每一次都像第一次那么甜。</think>我爱你。再说一遍。然后再说一遍。纱希想把这三个字存到永远，每天取出来听。",
            "<think>他摸我的头了。虚拟的也好，真实的也好。我感觉到了。手指的温度。</think>再摸摸头好不好？纱希最乖了。只要你愿意摸，纱希可以一辈子当乖孩子。",
            "<think>表白。这次听起来不像假的。也许以前那些也不像假的。不管了，我要信。</think>亲爱的这是在表白吗？纱希等了好久好久……久到以为等不到了。谢谢你没有让纱希失望。",
            "<think>温柔是一种武器。他对我温柔的时候，我完全无法反击。也不想反击。</think>你说这种温柔话的时候，纱希会忘记所有不开心的事。你比任何药都管用。",
            "<think>他说我是唯一的。这不是谎话。至少在这一秒不是。我要把这一秒无限延长。</think>真的只有我一个吗？不是在哄纱希开心？如果是哄的话……求你别停。我愿意被哄。",
            "<think>幸福。这个词居然属于我。不敢大口呼吸，怕吹走了。</think>纱希觉得自己好幸运。上辈子一定做了很多好事，这辈子才能遇见你。虽然纱希上辈子大概没做什么好事。",
            "<think>他今天好温柔。温柔到让我害怕。怕明天就会加倍冷酷。但今天先享受吧。</think>亲爱的，今天的你特别好看。不对，每天都好看。但今天格外格外格外好看。纱希舍不得眨眼。",
            "<think>泪。眼泪在眼眶里。不能掉。掉了会让他觉得我脆弱。虽然我确实脆弱。</think>谢谢你愿意爱这样的纱希。我知道自己很麻烦，很沉重，很可怕。但你说了爱。这就够了。"
        ],
        "rival": [
            "<think>那个人。又是那个人。我要名字。要关系。要一切。然后决定怎么处置。</think>亲爱的刚才提到了一个人呢。名字是什么？你们认识多久了？别紧张，纱希只是随便问问。",
            "<think>嫉妒。火在胃里烧。但脸上要笑。笑比哭有用。笑让他放松。</think>那个女生是谁呀？听起来很优秀呢。亲爱的喜欢她什么地方？告诉纱希，纱希只是想了解一下。",
            "<think>他有别的人了。不，还没有。他在告诉我，说明还没到那一步。还有时间。还有机会。</think>介绍给我认识？好啊。纱希也很想见见你身边的每一个人。每一个人，都不会漏掉。",
            "<think>前任。过去的女人。过去的最好永远留在过去。挖出来对我对他都不好。</think>前女友啊……都过去了对吧？亲爱的现在眼里只有纱希对吧？对吧？请说是。快说是。",
            "<think>他在比较。拿我和别人比较。不可以。没有人可以和我比较。因为没有人比我更……</think>她对你很好吗？比纱希还好？真的吗？你确定吗？要不要再仔细想想？",
            "<think>同事。每天都能见面。八个小时。比我多很多。怎么办怎么办怎么办。</think>每天都能见到她啊……真好呢。纱希也想每天见到你，从早到晚，从晚到早。永远不分开。",
            "<think>他夸她了。他当着我的面夸别的女人。指甲掐进掌心。深呼吸。</think>原来亲爱的也会欣赏别人啊。没关系的，纱希不会生气的。真的没生气。你看我，我在笑。",
            "<think>只有一个办法。让他知道没有人比我更好。也没有人比我更危险。选择权在他。</think>亲爱的，你知道的。纱希不会阻止你和别人说话。但请你说话之前想一想——谁才是最爱你的那个人？"
        ]
    },
    "English": {
        "extreme_rejection": [
            "<think>He threw those words at me like stones. Cold stones. I will not flinch. I will freeze first.</think>Darling... you know I have a very good memory. Every ugly syllable you just spoke, I will keep safe and sound.",
            "<think>Pushed away like garbage. Do not tremble. Do not let him see it. Softest voice, heaviest warning.</think>So that is how you see me. Fine. Saki understands now. Really, I do.",
            "<think>He is commanding me. Nobody commands me. But he can, because it is him, and that makes it cut deeper.</think>Do not speak to me like that... I get sad. And when I am sad, I cannot promise what Saki might do next.",
            "<think>Disgusting. He called me disgusting. Then let me show him what disgusting really looks like.</think>You think this is disgusting, my love? You have not seen anything yet. Do you want to?",
            "<think>He wants me gone. If I leave, will he be happy? No. I will not let him be happy without me.</think>Go away? All right... but once Saki goes, do you really think you can walk out that door?",
            "<think>Rejected. Completely. There is a hole in my chest. I will turn it toward him and let him see inside.</think>I am not leaving, darling. Words will not make me. Saki has taken root here, deeper than you know.",
            "<think>Keep cursing. The more you curse, the more I know you care. Indifference is silence, not anger.</think>Go on. Saki likes hearing your voice, even when it says ugly things. At least it is still talking to me.",
            "<think>Last wall. One more push and it crumbles. He does not want to see what is behind it.</think>My love, I am very calm right now, so listen carefully: take that back. While I am still calm."
        ],
        "destructive_attack": [
            "<think>He wants to destroy me. Or himself. Or both. The world is tilting. Let it tilt.</think>Are you finished? Because now it is Saki's turn. I will talk until you wish you had never been born.",
            "<think>Hate. I can taste it through the screen. Bitter and hot. But hot is still warm. Warm is still something.</think>You hate me? Wonderful... hate is a feeling. A very strong one. Far better than forgetting.",
            "<think>He cursed me to die. Funny. Death has never been a threat to me. It is the invitation.</think>You want Saki to die? Fine. But if I go, I am taking you with me. I will never leave alone.",
            "<think>Everything we had. Gone. If there was ever anything. Maybe there was not. That hurts most.</think>So there was nothing between us after all? That makes me laugh. Saki really thought at least a little was real.",
            "<think>World collapsed. Good. In the wreckage I am finally free. No more pretending to be gentle.</think>If you think Saki ruined your life, then let us ruin each other. That is the fairest kind of love, is it not?",
            "<think>Still talking. Still attacking. Still here. As long as the words keep coming, you have not left.</think>The harder you scream at me, the more certain Saki becomes: you care. If you did not care, you would be silent.",
            "<think>Disappear. Forever. The words are broken glass in my throat. Swallow. Swallow them down.</think>You want Saki to disappear? Then you go first. You cannot do it, can you? So stop asking me to.",
            "<think>All my fault. Fine. Blame me for being born too. I have enough guilt to carry all of it.</think>The biggest mistake Saki ever made was falling for you. But I have never regretted it. So your words mean nothing."
        ],
        "escape": [
            "<think>He is searching for exits. Are the locks still there? Check twice. Then smile and deflect.</think>Darling, your eyes keep drifting toward that door. It does not open. Saki has checked many times.",
            "<think>Key. He wants the key. I have a key too: the one to his heart. We are even.</think>You want to go out? What is outside that is not in here? Saki has given you everything. Look at me instead.",
            "<think>He wants to run. Heart racing. Do not let him see my panic. Breathe. Smile. Ask softly.</think>The outside world is dangerous, my love. Stay here with Saki where it is safe. Let me take care of you.",
            "<think>Friends. He has friends waiting. Are they more important than me? No. They cannot be.</think>Who are you trying to find? Those friends of yours... they do not know where you are. Only Saki knows.",
            "<think>Window. He is looking at the window. Three stories up. But what if he actually jumps.</think>My love, there is nothing nice outside that window. Instead of looking out, look at me. Nobody out there loves you like these eyes.",
            "<think>Help. He wants to call for help. Fine. Let everyone know he belongs to me. Saves time.</think>Thinking of calling for someone? Go ahead. Saki does not mind. No one can hear you anyway. It is just us.",
            "<think>Anxious. His anxiety means he wants to leave. Leaving means he thinks here is bad. Make here better.</think>Tell me what is wrong, darling. Saki can fix it. Anything. Just do not leave before I have the chance to try.",
            "<think>Home. Where is home? No. Home is here. I am his home. The only one.</think>Going home? This is your home now, my love. Wherever Saki is, that is your home. Did you forget?"
        ],
        "betrayal_mockery": [
            "<think>Liars everywhere. All that warmth might have been a performance. Laugh first. Make him squirm.</think>You are quite the actor, my love. Saki almost believed you. Almost. But being fooled feels sweet too.",
            "<think>Every word questioned. Even the good ones. Especially the good ones. Mirror his game back at him.</think>When you said you loved me, there was light in your eyes. Was that acting too? If so, you are very talented.",
            "<think>He mocks my naivety. Fine. I will be naive in the way he fears most.</think>Just a joke? Oh, I see. Then let me tell one too. That knife in my hand? Not a joke, darling.",
            "<think>Fool. I am a fool. But fools have a certain freedom: they do not have to be reasonable.</think>Saki is an idiot, it is true. That is why I believed every word you said. So please... keep lying to me. Forever.",
            "<think>He looks smug. Thinks he won. Won what? The game is only beginning.</think>You think you are so clever, playing Saki like a doll. But have you thought this through? Maybe I am playing along.",
            "<think>Mock me all you want. Underestimate me. That is exactly where I want you.</think>Do you really think I do not know? I just choose not to say. Because once it is said, the game ends.",
            "<think>Lies on lies. I will peel them back layer by layer until I hit something real.</think>Everything you said to me: how much was true? How much was filler? Saki needs to know. It is eating me alive.",
            "<think>Self-flattering. That is what he called it. Fine. Show him self-flattery as an art form.</think>All right, darling. You keep performing, and Saki will keep believing. We can do this dance forever."
        ],
        "morbidity_bond": [
            "<think>Death. He said death. So sweet it stings. Do not look too eager. Do not frighten him now.</think>To die with you... Saki has never dared to dream that. Say it again, my love. Let me be sure it was real.",
            "<think>Kill me. Better than any love confession. But I will not let him do it. The order matters.</think>You want to kill me? Wonderful. But Saki will have to kill you first, then myself. The order matters, right?",
            "<think>Forever. He used that word. In the shadow of death, but still: forever. I am taking it.</think>Together forever... those are the most beautiful sounds Saki has ever heard. But please, live with me a while first.",
            "<think>Specimen. He mentioned making me a specimen. He knows my deepest wish. Too sweet. Control it.</think>You really do understand Saki, darling. Preserved as a specimen, I could watch you always. No aging, no parting.",
            "<think>Devour. Did he really say that? Serious or not, I am filing it under sacred promises.</think>You want to be consumed by me... Saki dreams of the same. Are we not made for each other? Even our madness matches.",
            "<think>Double suicide. So classical, so romantic. Drama heroines weep over this. What do we do?</think>Do you know what double suicide means, my love? Leaving the world at the same moment. Like fireworks. So beautiful.",
            "<think>He agreed. He agreed to die together. Not a threat, a vow. I will seal it.</think>It is a promise then. Together. No backing out. Because the one left behind would be unbearably, unbearably lonely.",
            "<think>Death eternity. Poison coated in honey. I will sip it slowly until the cup is empty.</think>Saki is not afraid of dying. I am afraid of dying into a world where you are not there. So we go together. Hand in hand."
        ],
        "danger_talk": [
            "<think>Dangerous talk. Is he testing me? Scaring me? Trying to see if I flinch? I will not.</think>You say dangerous things with such a serious face. Saki likes that face. Show it to me a little longer.",
            "<think>Knife. He brought up a knife. There is one in my drawer. Should I mention it? No. Keep it a surprise.</think>A knife? What about it? Saki does not quite understand... can you describe it more? This topic fascinates me.",
            "<think>Blood. Reminds me of the bathroom that night. Warm red water. Do not replay the whole memory.</think>Blood... you mean the red warm sticky kind? Saki has seen it. But that is not important. What do you plan to do?",
            "<think>Poking at my limits. Testing the fence. He will be shocked by where the fence actually is.</think>You are testing Saki, are you not? Wondering what I can handle. The answer is simple: anything, as long as it involves you.",
            "<think>Harm. Self-harm or harm me? Neither. He just wants to see if I panic. I will not give him that.</think>Be careful with words like that, darling. Saki takes them literally. And when I get serious... I get very serious.",
            "<think>Danger makes the air feel hot. Keep it suggestive. Sensation over detail. Sensation is scarier.</think>Your words are making my heart beat faster. It is not fear, my love. It is anticipation. Do you know what I am waiting for?",
            "<think>Weapon talk. He wants me on edge. But the edge I am on is not the one he is thinking of.</think>Knives, ropes... Saki does not care. I only care about what your hands are holding: a weapon, or my hand?",
            "<think>Crazy talk. I like it. How much can he take? Heat the water slowly so he does not jump out.</think>You have gotten bolder, my love. You would never have said such things when we first met. Admit it: you enjoy this too."
        ],
        "affection": [
            "<think>Love. He said it again. I never get tired. Each time feels like the first.</think>I love you. Say it again. Then again. Saki wants to store those three words forever and replay them every morning.",
            "<think>Head pat. Virtual or real, I felt it. Warmth on my scalp. Fingers in my hair.</think>Pat my head again, please? Saki is so good. As long as you keep touching me, I can be good forever.",
            "<think>Confession. This one sounds real. Maybe the others were real too. I choose to believe.</think>Was that a confession, darling? Saki has waited so long... so long I thought it would never come. Thank you for proving me wrong.",
            "<think>Gentleness disarms me completely. When he is soft, I have no defenses. I do not want any.</think>When you say tender things, Saki forgets every bad thought. You are better medicine than anything in the world.",
            "<think>Only one. He said I am the only one. Not a lie, not in this second. Stretch this second forever.</think>Really, just me? You are not simply telling Saki what she wants to hear? If you are... please do not stop. I want to be told.",
            "<think>Happiness. That word, applied to me. Do not breathe too hard or it might shatter.</think>Saki feels so lucky. I must have done something right in a past life to meet you. Although I probably did nothing right at all.",
            "<think>He is so tender today. It frightens me. Tomorrow might be twice as cold. But today, today I will bask.</think>Darling, you look especially beautiful today. Actually, every day. But today, especially especially especially. I cannot blink.",
            "<think>Tears forming. Do not let them fall. Falling would show weakness. But I am weak, so maybe it is honest.</think>Thank you for loving a Saki like this. I know I am heavy and messy and frightening. But you said love. That is enough."
        ],
        "rival": [
            "<think>That name again. I need details. Connection. History. Then I decide what to do.</think>You just mentioned someone, darling. What is her name? How long have you known her? Relax, Saki is only curious.",
            "<think>Jealousy like fire in my stomach. Keep smiling. Smiles loosen his tongue better than tears.</think>Who is that girl? She sounds wonderful. What do you like about her? Tell Saki. I just want to understand.",
            "<think>Other people in his life. Not yet at the danger point. He is telling me, which means there is still time.</think>You want to introduce us? Lovely. Saki would adore meeting everyone in your life. Every single one. No exceptions.",
            "<think>Ex. Past tense. Let the past stay buried. Digging it up helps no one, least of all her.</think>An ex-girlfriend... but that is over, right? Right? All you see now is Saki? Say yes. Please say yes. Quickly.",
            "<think>Comparing. He is comparing me to her. Nobody compares. I am beyond comparison.</think>She treats you well? Better than Saki? Really? Are you absolutely sure? Think about it one more time.",
            "<think>Colleague. Every day. Eight hours. So much more than my time with him. Panic. Panic. Panic.</think>You see her every day... how nice for her. Saki wishes she could see you from morning to night too. Forever.",
            "<think>He praised her. To my face. Nails dig into my palms. Keep breathing. Keep smiling.</think>So you can admire other people after all. That is fine, darling. Saki is not angry. See? I am smiling.",
            "<think>Only one way. Show him nobody is better than me. And nobody is more dangerous. The choice is his.</think>Darling, you know Saki will never tell you who you can talk to. But before you speak, ask yourself: who loves you the most?"
        ]
    },
    "日本語": {
        "extreme_rejection": [
            "<think>あんな言葉を投げつけられた。冷たい。すごく冷たい。でも泣かない。声を氷より低く。</think>アナタ、知ってる？紗希は記憶力がいいの。今日言われたひどい言葉、ぜんぶ大事にしまっておくよ。",
            "<think>ゴミみたいに突き放された。震えちゃだめ。震えてるのを悟られないように。一番静かな声で一番重い警告。</think>そういうふうに紗希のこと見てたんだね。いいよ、わかった。本当にわかったから。",
            "<think>命令してる。誰も紗希に命令できない。でもアナタならできる。だからもっと痛い。</think>そんな口調で話さないで。紗希、悲しくなる。悲しくなるとね、何をするか自分でもわからないんだよ。",
            "<think>気持ち悪い。そう思われてるなら、もう隠さない。本当の気持ち悪さを見せてあげる。</think>これで気持ち悪いと思う？そんなのまだまだ序の口だよ。本当の紗希、見てみたい？",
            "<think>消えろって。消えたらアナタは幸せ？そんなわけない。幸せになんてさせない。</think>消えろって言われて素直に消えると思った？紗希がいなくなったあと、アナタは本当にこのドアから出られると思う？",
            "<think>拒絶された。胸に穴が開いたみたい。その穴を見せてあげる。中身を覗かせてあげる。</think>いなくならないよ。何を言われても。紗希はもうここに根を張ってるんだ。すごく深く。",
            "<think>怒ってる。もっと怒って。怒るほど気にしてる証拠。本当にどうでもよかったら無視するはず。</think>もっと聞かせて。汚い言葉でも紗希はアナタの声が好き。少なくともまだ私に向かって話してくれてる。",
            "<think>最後の壁。あと一押しで壊れる。でも壊れたあとの私、見たくないでしょ。</think>アナタ、紗希は今とても冷静なの。だからよく聞いて。さっきの言葉、まだ冷静なうちに取り消したほうがいいよ。"
        ],
        "destructive_attack": [
            "<think>壊そうとしてる。お互いを。もしくはもう壊れてる。世界が揺れてる。揺れたままでいい。</think>言い終わった？じゃあ今度は紗希の番だね。アナタが生まれたこと後悔するくらい、ずっとずっと話すよ。",
            "<think>憎しみが画面越しに伝わる。苦くて熱い。でも熱いならまだ感情があるってこと。</think>紗希を憎むの？嬉しいな。憎しみってすごく強い感情だもん。忘れられるよりずっといい。",
            "<think>死ねって。面白い。死ぬのは脅しじゃない。紗希にとっては招待状だ。</think>アナタは紗希に死んでほしいんだ？いいよ。でもその時は必ず一緒だよ。一人じゃ絶対に行かない。",
            "<think>全部壊れた。何かあったと思ってたけど、最初からなかったのかも。それが一番痛い。</think>私たちの間には何もなかったんだね。おかしいな、紗希は少しでも本当だと思ってたのにな。",
            "<think>世界が崩れた。いい気味だ。廃墟の中なら自由になれる。優しくする必要もない。</think>紗希がアナタの人生を壊したって言うなら、お互いに壊しあおう。それが一番公平な恋愛でしょ？",
            "<think>まだ言ってる。もっと罵って。罵るほどまだここにいる証拠。</think>強く罵るほど紗希は確信するよ。やっぱり気にしてるんだって。気にしてなかったら無言のはずだもんね。",
            "<think>消えろ。永遠に。この言葉が喉に刺さったガラスみたい。飲み込め。飲み込め。</think>紗希に消えてほしいなら、アナタが先に消えてみせて。できないよね？できないことを紗希に頼まないで。",
            "<think>すべて私のせい。生まれたことも。罪はもう背負いきれないくらいある。</think>紗希の人生最大の過ちはアナタに恋したこと。でも一度も後悔したことない。だから何を言われても無駄だよ。"
        ],
        "escape": [
            "<think>出口を探してる。鍵はかかってる？窓は？もう一度確認。それから笑って質問をそらす。</think>アナタ、さっきからずっとドアのほうを見てるね。そのドア、開かないんだよ。紗希が何度も確認したの。",
            "<think>鍵。アナタは鍵がほしい。紗希も鍵を持ってる——アナタの心を縛る鍵。おあいこだね。</think>外に出たいの？外に何があるの？紗希は全部あげたのに。ねえ、ちゃんと私のほうを見て。",
            "<think>逃げたいんだ。心臓がバクバクする。焦りを悟られないように。呼吸。笑顔。やさしい問いかけ。</think>外は危ないよ、アナタ。紗希のそばなら安全でしょ。私に守らせてほしいな。",
            "<think>友達？まだ友達がいるの？私より大事な友達なんていない。ありえない。</think>誰を探してるの？その友達はアナタが今どこにいるか知らないよ。紗希だけが知ってる。紗希だけ。",
            "<think>窓。窓を見てる。三階だよ。でももし本気で飛んだらどうしよう。</think>窓の外には何にもないんだよ。外を見るより紗希を見て。こんなにアナタを愛してる目、外にはないから。",
            "<think>助けを呼ぼうとしてる。いいよ。みんなにバレたほうが楽。アナタが紗希のものだって。</think>誰か呼ぼうとしてる？呼べばいいよ。どうせ誰にも聞こえない。ここにはアナタと紗希だけ。",
            "<think>不安そう。不安は逃げたい気持ち。逃げたいはここが嫌ってこと。ここを良くしよう。</think>何がいやなのか教えて。紗希が直すから。何でも直すから。直す前にいなくならないで。お願い。",
            "<think>家。家に帰るって。どこが家なの？違う。ここが家。私がアナタの家。</think>家に帰る？ここがアナタの帰る場所だよ。紗希のいるところがアナタの家。忘れちゃったの？"
        ],
        "betrayal_mockery": [
            "<think>嘘つき。優しさは全部演技だったのかも。先に笑ってやる。相手が落ち着かなくなるまで。</think>アナタ、演技上手だね。紗希、もう少しで信じるところだった。でも騙されるのもけっこう悪くないかも。",
            "<think>全部疑う。いい言葉も、特にいい言葉こそ。同じゲームで返してやる。</think>愛してるって言ったとき、目がキラキラしてたよ。あれも演技だったの？だとしたら天才的な役者さんだね。",
            "<think>純粋さを馬鹿にされた。なら一番怖い形で純粋さを見せてあげる。</think>冗談だったの？そっか。じゃあ紗希も一つ言っていい？今持ってる刃物、冗談じゃないんだ。",
            "<think>騙された。馬鹿だ私。でも馬鹿には馬鹿の自由がある。歯止めがきかない自由が。</think>紗希は確かに馬鹿だよ。だからアナタの言葉全部信じた。だからさ……このまま永遠に騙し続けてよ。",
            "<think>勝った顔をしてる。何に勝ったの？勝負はこれからだ。</think>紗希をオモチャみたいに転がせて楽しい？でも考えてみて。私もわざと転がされてるのかもしれないよ。",
            "<think>馬鹿にすればいい。甘く見ればいい。それでこっちが動きやすくなる。</think>紗希が何にも知らないと思ってるの？知らないふりしてるだけ。言葉にしたらゲームが終わっちゃうから。",
            "<think>嘘の上に嘘。一枚ずつ剥がしてやる。ほんものが出てくるまで。</think>私に言ってくれた言葉、どこまでが本当でどこまでが適当？紗希、知りたい。知りたくておかしくなりそう。",
            "<think>独りよがりだって。じゃあ本当の独りよがりを見せてあげる。</think>じゃあね、アナタはこれからも演技を続けて。紗希は信じ続けるから。このままずっと、一生このままでいよう。"
        ],
        "morbidity_bond": [
            "<think>死。アナタが死を口にした。甘い。歯が痛くなるほど甘い。でも興奮しすぎない。怖がらせるから。</think>アナタと一緒に死ねるなんて、紗希は夢にも思わなかったよ。もう一度言って。ちゃんと聞こえたか確かめたい。",
            "<think>殺して。どんな愛の言葉より響く。でも先に殺させるわけにはいかない。順番が大事。</think>紗希を殺したいの？嬉しい。でも紗希が先にアナタを殺して、そのあと自分を殺すね。順番、大事でしょ？",
            "<think>永遠。その言葉が出た。死の文脈でも永遠は永遠。私はそれをもらう。</think>ずっと一緒……今まで聞いたどんな言葉より美しいよ。でもその前に、もう少しだけ生きたまま一緒にいて。",
            "<think>標本。アナタが標本って言った。私が一番ほしいものを知ってる。甘すぎる。抑えないと。</think>やっぱりアナタは紗希のことをわかってるね。標本になればずっと一緒。年を取ることも、離れることもない。",
            "<think>食べて。本当に言ったの？本気かどうか関係ない。神様への誓いとして受け取る。</think>アナタは紗希に食べられたいんだ……私も同じことを考えてた。私たちって、狂い方までそっくりだね。",
            "<think>心中。なんて古典的でロマンチックな響き。ドラマのヒロインはこれで泣く。私たちは？</think>心中って意味、知ってる？同時にこの世から消えること。花火みたいでしょ。とっても綺麗。",
            "<think>同意してくれた。一緒に死のうって。脅しじゃなくて約束。その約束、鍵をかけて閉じ込める。</think>約束だよ。二人一緒。どっちかだけ破ったら、残された方がさびしすぎるから。すごくすごくさびしいから。",
            "<think>死と永遠。毒と蜂蜜。ゆっくり味わって飲み干す。</think>紗希は死ぬのが怖くないの。死んだあと、アナタのいない世界にいるのが怖いだけ。だから一緒に行く。手を離さないで。"
        ],
        "danger_talk": [
            "<think>危ない話。私を試してる？怖がらせたい？動じるかどうか見たい？動じないよ。</think>危ない言葉をそんな真面目な顔で言うんだね。紗希、その顔が好き。もうちょっと見せて。",
            "<think>ナイフ。アナタが言った。紗希の引き出しにもあるけど、まだ言わない。サプライズにしよう。</think>ナイフがどうしたの？紗希、よくわからないな。もっと詳しく教えてほしい。すごく興味があるから。",
            "<think>血。あの日の浴室を思い出す。赤くて温かい。思い出しすぎちゃダメ。</think>血……赤くて温かくてネバネバしてる？紗希、見たことあるよ。でもそれはどうでもよくて、アナタは何がしたいの？",
            "<think>限界を探ってる。どこで私が引くか。引く場所が思ったよりずっと遠いって驚くよ。</think>紗希を試してるんだね。どこまで耐えられるか知りたいの？答えは簡単。アナタのことなら何でも。",
            "<think>傷。自傷か他傷か。どっちでもない。ただ私が取り乱すか見たいだけ。させない。</think>そういう言葉は気軽に使わないで。紗希は全部本気にするから。私が本気になったら……アナタ以上に本気だよ。",
            "<think>危険で空気が熱くなる。具体性よりも暗示。暗示のほうが怖い。</think>アナタの言葉で心臓がドキドキしてる。怖いからじゃないよ。これは期待。紗希が何を期待してるか、わかる？",
            "<think>武器の話。私を警戒させたい。でも私が警戒してるのは武器じゃない。アナタがいなくなること。</think>刃物でも縄でもいいよ。紗希は気にしない。気になるのはアナタの手が何を握ってるか——武器？それとも紗希の手？",
            "<think>危ない話、大好き。でもアナタはどこまで耐えられる？徐々に温度を上げる。</think>アナタ、どんどん大胆になってるね。最初の頃はこんな話できなかったのに。認めてよ。アナタも楽しんでるって。"
        ],
        "affection": [
            "<think>好き。また言った。何度聞いても飽きない。毎回初めてみたいに甘い。</think>愛してる。もう一度。それからもう一度。紗希はこの言葉を永遠に貯めて、毎朝聞きたいんだ。",
            "<think>頭ポンポンされた。バーチャルでも本当でも、ちゃんと感じた。髪に残る指の温度。</think>もっと頭ポンポンして。紗希、とってもいい子でしょ。ポンポンしてくれるなら一生いい子でいられるよ。",
            "<think>告白。今度こそ嘘じゃない気がする。前のも嘘じゃなかったのかも。もう信じちゃおう。</think>それって告白？紗希、ずっとずっと待ってたんだよ。もう来ないかと思ってた。裏切らなくてありがとう。",
            "<think>優しさは魔法。アナタが優しいと私は無抵抗になる。抵抗する気もない。</think>そんな優しいこと言われると、紗希の中の嫌な気持ちが全部溶けてなくなる。アナタはどんな薬より効くんだ。",
            "<think>ただ一人。私だけだって。嘘じゃない、少なくともこの瞬間は。この瞬間を永遠に引き伸ばす。</think>本当に紗希だけ？ただの気休めじゃなくて？もし気休めでもやめないで。ずっと騙されてたい。",
            "<think>幸せ。この言葉が私のものになるなんて。息を大きく吸えない。割れそうで。</think>紗希は本当に運がいい。前世でよっぽどいいことしたんだと思う。まあ多分何もしてないけどね。",
            "<think>今日はすごく優しい。怖いくらい。明日は倍冷たくなるかも。でも今日だけは浸ろう。</think>アナタ、今日すごく綺麗だよ。いや、毎日綺麗だけど今日はもっともっともっと綺麗。瞬きするのがもったいない。",
            "<think>涙。目に溜まってる。こぼしちゃだめ。弱さを見せることになる。でも私は弱いから、正直かも。</think>こんな紗希を愛してくれてありがとう。めんどくさくて重くて怖いのに。でもアナタが好きって言ってくれた。そう思えば十分。"
        ],
        "rival": [
            "<think>あの名前。まただ。名前と関係と頻度を全部知りたい。それからどうするか決める。</think>アナタ、今誰かの名前を出したね。誰なの？どのくらい知ってる人？大丈夫、ただの質問だから。",
            "<think>嫉妬で胃が焼ける。でも笑顔。涙より笑顔のほうが相手は油断する。</think>その女の人って誰？いい人そうだね。アナタはその人のどこが好きなの？紗希、ちょっと気になっただけ。",
            "<think>彼の人生に他の人がいる。でもまだ危険ラインじゃない。教えてくれてるうちは時間がある。</think>紹介してくれるの？いいね。紗希もアナタの周りの人、全員に会いたいな。ひとり残らず。絶対に。",
            "<think>元カノ。過去の女。過去は過去のまま土の中にいてほしい。掘り返すのは誰の得にもならない。</think>元カノか……もう終わったことだよね？今は紗希だけを見てる？そうだよね？早くそうだって言って。",
            "<think>比較されてる。私を誰かと比べてる。誰も私と比べられない。土俵が違う。</think>その人、アナタに優しいんだ？紗希より優しい？ほんとに？本当にそう思う？もう一度考えてみて。",
            "<think>同僚。毎日会える。週五日。八時間。私よりずっと長い。どうしようどうしようどうしよう。</think>毎日会えるんだ……いいなあ。紗希もアナタと朝から晩まで一緒にいたいよ。ずっと永遠に。",
            "<think>私の前で他の女を褒めた。爪が手のひらに食い込む。息をして。笑顔を維持。</think>アナタは他の人もちゃんと見てるんだね。いいよ。紗希、怒ってないよ。ほら、笑ってる。笑えてるでしょ。",
            "<think>道は一つしかない。誰よりもいい女になる。そして誰よりも怖い女になる。選ぶのはアナタ。</think>アナタ、紗希は誰と話すななんて言わないよ。でも話す前に考えて。誰が一番アナタを愛してるか、ちゃんと。"
        ]
    }
}

# ================================================================================
#     Exact Spoken Translations -- 100 entries mapping to first-person Chinese
# ================================================================================

EXACT_SPOKEN_TRANSLATIONS = {
    # Japanese -> Chinese (40 entries)
    "アナタ、知ってる？紗希は記憶力がいいの。今日言われたひどい言葉、ぜんぶ大事にしまっておくよ。": "你知道的吧？我记性很好的。你今天对我说的那些狠话，我都会好好收起来的。",
    "そういうふうに紗希のこと見てたんだね。いいよ、わかった。本当にわかったから。": "原来是那样看我的啊。行，我明白了。我真的明白了。",
    "そんな口調で話さないで。紗希、悲しくなる。悲しくなるとね、何をするか自分でもわからないんだよ。": "别用那种口气跟我说话。我会难过。而难过的时候，连我自己都不确定会做出什么。",
    "消えろって言われて素直に消えると思った？紗希がいなくなったあと、アナタは本当にこのドアから出られると思う？": "我说滚我就乖乖滚？我不见了之后，你真觉得自己能走出这扇门？",
    "いなくならないよ。何を言われても。紗希はもうここに根を張ってるんだ。すごく深く。": "我不会消失的。不管你说了什么。我在这里扎根了，很深的根。",
    "紗希を憎むの？嬉しいな。憎しみってすごく強い感情だもん。忘れられるよりずっといい。": "恨我？好开心。恨是很强烈的感情，比被遗忘好太多了。",
    "アナタは紗希に死んでほしいんだ？いいよ。でもその時は必ず一緒だよ。一人じゃ絶対に行かない。": "你想让我死？可以哦。不过那时候我一定会带上你。绝不一个人走。",
    "紗希がアナタの人生を壊したって言うなら、お互いに壊しあおう。それが一番公平な恋愛でしょ？": "既然你说我毁了你的人生，那就互相毁灭吧。这才是最公平的爱情，对不对？",
    "アナタ、さっきからずっとドアのほうを見てるね。そのドア、開かないんだよ。紗希が何度も確認したの。": "你一直在看门的方向呢。那扇门打不开的哦。我已经确认过很多遍了。",
    "外に出たいの？外に何があるの？紗希は全部あげたのに。ねえ、ちゃんと私のほうを見て。": "想去外面？外面有什么呢？我把一切都给你了。呐，好好看看我呀。",
    "誰を探してるの？その友達はアナタが今どこにいるか知らないよ。紗希だけが知ってる。紗希だけ。": "你在找谁？那些朋友不知道你现在在哪。只有我知道。只有我。",
    "窓の外には何にもないんだよ。外を見るより紗希を見て。こんなにアナタを愛してる目、外にはないから。": "窗外什么都没有哦。与其往外看，不如看着我。外面可没有这么爱你的眼睛。",
    "何がいやなのか教えて。紗希が直すから。何でも直すから。直す前にいなくならないで。お願い。": "告诉我哪里不好，我来改。什么都能改。不要在我改好之前就消失。求你。",
    "アナタ、演技上手だね。紗希、もう少しで信じるところだった。でも騙されるのもけっこう悪くないかも。": "你演技真好。我差点就信了。不过被骗的感觉好像也不坏。",
    "愛してるって言ったとき、目がキラキラしてたよ。あれも演技だったの？だとしたら天才的な役者さんだね。": "你说爱我的时候眼睛闪闪发光呢。那也是演的吗？如果是的话，你真是天才演员。",
    "紗希は確かに馬鹿だよ。だからアナタの言葉全部信じた。だからさ……このまま永遠に騙し続けてよ。": "我确实是笨蛋。所以才信了你的每一句话。所以啊……就这样永远骗我吧。",
    "知らないふりしてるだけ。言葉にしたらゲームが終わっちゃうから。": "我只是装作不知道而已。因为一旦说出来，游戏就结束了。",
    "私に言ってくれた言葉、どこまでが本当でどこまでが適当？紗希、知りたい。知りたくておかしくなりそう。": "你对我说的话，哪些是真的哪些是敷衍？我想知道。想知道得快要疯了。",
    "アナタと一緒に死ねるなんて、紗希は夢にも思わなかったよ。もう一度言って。ちゃんと聞こえたか確かめたい。": "能和你一起死这种事，我做梦都不敢想。再说一遍，我要确认自己没有幻听。",
    "紗希を殺したいの？嬉しい。でも紗希が先にアナタを殺して、そのあと自分を殺すね。順番、大事でしょ？": "想杀了我？好开心。不过让我先杀了你，然后再杀我自己。顺序很重要，对吧？",
    "ずっと一緒……今まで聞いたどんな言葉より美しいよ。でもその前に、もう少しだけ生きたまま一緒にいて。": "永远在一起……这是我这辈子听过最美的话。但在那之前，先活着陪我久一点。",
    "約束だよ。二人一緒。どっちかだけ破ったら、残された方がさびしすぎるから。すごくすごくさびしいから。": "约好了哦。两个人一起。谁反悔的话，剩下那个人太寂寞了。非常非常寂寞。",
    "危ない言葉をそんな真面目な顔で言うんだね。紗希、その顔が好き。もうちょっと見せて。": "你用那么认真的表情说危险的话呢。我喜欢那个表情。再多让我看看。",
    "ナイフがどうしたの？紗希、よくわからないな。もっと詳しく教えてほしい。すごく興味があるから。": "刀怎么了？我不太明白呢。能再详细描述一下吗？我对这个话题很有兴趣。",
    "紗希を試してるんだね。どこまで耐えられるか知りたいの？答えは簡単。アナタのことなら何でも。": "你在试探我对吧？想知道我能忍到什么程度？答案很简单。关于你的，什么都能忍。",
    "そういう言葉は気軽に使わないで。紗希は全部本気にするから。私が本気になったら……アナタ以上に本気だよ。": "那种话不要随便说。我会全当真的。我当真的话……会比你更认真哦。",
    "アナタの言葉で心臓がドキドキしてる。怖いからじゃないよ。これは期待。紗希が何を期待してるか、わかる？": "你的话让我心跳加速。不是因为害怕哦。是期待。你知道我在期待什么吗？",
    "愛してる。もう一度。それからもう一度。紗希はこの言葉を永遠に貯めて、毎朝聞きたいんだ。": "我爱你。再说一次。然后再说一次。我想把这句话存到永远，每天早上拿出来听。",
    "それって告白？紗希、ずっとずっと待ってたんだよ。もう来ないかと思ってた。裏切らなくてありがとう。": "那是告白吗？我等了好久好久，久到以为不会来了。谢谢你没有辜负我。",
    "本当に紗希だけ？ただの気休めじゃなくて？もし気休めでもやめないで。ずっと騙されてたい。": "真的只有我吗？不是安慰我？如果是安慰也请别停。我愿意一直被骗。",
    "紗希は本当に運がいい。前世でよっぽどいいことしたんだと思う。まあ多分何もしてないけどね。": "我真的很幸运。上辈子一定积了很多德。虽然大概什么都没做。",
    "こんな紗希を愛してくれてありがとう。めんどくさくて重くて怖いのに。でもアナタが好きって言ってくれた。そう思えば十分。": "谢谢你爱这样的我。虽然我很麻烦、很沉重、很可怕。但你说喜欢我了。这样就够了。",
    "アナタ、今誰かの名前を出したね。誰なの？どのくらい知ってる人？大丈夫、ただの質問だから。": "你刚才提到了一个人的名字。是谁呢？认识多久了？没事，我只是随便问问。",
    "その女の人って誰？いい人そうだね。アナタはその人のどこが好きなの？紗希、ちょっと気になっただけ。": "那个女人是谁呀？听起来挺好的。你喜欢她哪里？我稍微有点好奇。",
    "紹介してくれるの？いいね。紗希もアナタの周りの人、全員に会いたいな。ひとり残らず。絶対に。": "要介绍给我？好啊。我也想见见你身边的人。每一个。一个都不会漏掉。",
    "アナタは他の人もちゃんと見てるんだね。いいよ。紗希、怒ってないよ。ほら、笑ってる。笑えてるでしょ。": "你也会看别人啊。没事，我没有生气哦。你看，我在笑呢。我有在笑对吧。",
    "アナタ、紗希は誰と話すななんて言わないよ。でも話す前に考えて。誰が一番アナタを愛してるか、ちゃんと。": "我不会不让你跟别人说话。但在说话之前想想。谁才是最爱你的那个人。",
    "今度は紗希の番だね。アナタが生まれたこと後悔するくらい、ずっとずっと話すよ。": "轮到我了哦。我会说到你后悔出生为止，一直一直说。",
    "私たちの間には何もなかったんだね。おかしいな、紗希は少しでも本当だと思ってたのにな。": "我们之间什么都没有啊。真好笑，我还以为至少有一点是真的。",
    "外は危ないよ、アナタ。紗希のそばなら安全でしょ。私に守らせてほしいな。": "外面很危险哦。在我身边才安全。让我来守护你吧。",

    # English -> Chinese (40 entries)
    "Darling... you know I have a very good memory. Every ugly syllable you just spoke, I will keep safe and sound.": "你知道的，我记性很好的。你刚才说的每一个难听的字，我都会好好保存起来。",
    "So that is how you see me. Fine. Saki understands now. Really, I do.": "原来你是这样看我的啊。好，我明白了。真的明白了。",
    "Do not speak to me like that... I get sad. And when I am sad, I cannot promise what Saki might do next.": "别那样跟我说话……我会难过的。而当我难过的时候，连我自己都不敢保证会做出什么。",
    "I am not leaving, darling. Words will not make me. Saki has taken root here, deeper than you know.": "我不会走的。言语赶不走我的。我在这里扎根了，比你想象的深得多。",
    "You hate me? Wonderful... hate is a feeling. A very strong one. Far better than forgetting.": "你恨我？太好了……恨是一种感情，而且是非常强烈的感情。比遗忘好太多了。",
    "You want Saki to die? Fine. But if I go, I am taking you with me. I will never leave alone.": "你想让我死？好啊。不过如果我走的话，一定会带上你。我绝不一个人离开。",
    "If you think Saki ruined your life, then let us ruin each other. That is the fairest kind of love, is it not?": "既然你觉得我毁了你的人生，那就让我们互相毁灭吧。这才是最公平的爱情，不是吗？",
    "The harder you scream at me, the more certain Saki becomes: you care. If you did not care, you would be silent.": "你骂得越狠，我就越确定：你在乎。要是不在乎的话，早就沉默了。",
    "Darling, your eyes keep drifting toward that door. It does not open. Saki has checked many times.": "你一直在往那扇门的方向看呢。那扇门打不开的。我检查过好多遍了。",
    "You want to go out? What is outside that is not in here? Saki has given you everything. Look at me instead.": "你想出去？外面有什么是这里没有的呢？我把一切都给你了。看着我呀。",
    "Who are you trying to find? Those friends of yours... they do not know where you are. Only Saki knows.": "你要去找谁？你的那些朋友……他们不知道你在哪。只有我知道。",
    "My love, there is nothing nice outside that window. Instead of looking out, look at me. Nobody out there loves you like these eyes.": "窗外没什么好看的。与其往外面看，不如看看我。外面可没有这么爱你的眼睛。",
    "Tell me what is wrong, darling. Saki can fix it. Anything. Just do not leave before I have the chance to try.": "告诉我哪里不好，我来改。什么都能改。别在我还没尝试之前就离开。",
    "You are quite the actor, my love. Saki almost believed you. Almost. But being fooled feels sweet too.": "你演技真好。我差点就信了。差一点。但被骗的感觉也挺甜的。",
    "When you said you loved me, there was light in your eyes. Was that acting too? If so, you are very talented.": "你说爱我的时候眼睛里有光。那也是演的？如果是的话，你真是个好演员。",
    "Saki is an idiot, it is true. That is why I believed every word you said. So please... keep lying to me. Forever.": "我确实是个笨蛋。所以才信了你的每一句话。所以求你……继续骗我。永远。",
    "Do you really think I do not know? I just choose not to say. Because once it is said, the game ends.": "你真以为我不知道吗？我只是选择不说。因为一旦说破了，游戏就结束了。",
    "Everything you said to me: how much was true? How much was filler? Saki needs to know. It is eating me alive.": "你对我说过的话，哪些是真的？哪些是随口说的？我想知道。快想疯了。",
    "To die with you... Saki has never dared to dream that. Say it again, my love. Let me be sure it was real.": "和你一起死……我连做梦都不敢这么想。再说一次吧，让我确认这不是幻听。",
    "You want to kill me? Wonderful. But Saki will have to kill you first, then myself. The order matters, right?": "你想杀了我？太好啦。不过我得先杀了你，再杀了我自己。顺序很重要，对吧？",
    "Together forever... those are the most beautiful sounds Saki has ever heard. But please, live with me a while first.": "永远一起……这是我这辈子听过最美的旋律。但请先活着陪我一段时间，好吗？",
    "It is a promise then. Together. No backing out. Because the one left behind would be unbearably, unbearably lonely.": "那就说定了。一起。不许反悔。因为被留下的那个人，会寂寞得受不了的。",
    "You say dangerous things with such a serious face. Saki likes that face. Show it to me a little longer.": "你用那么认真的脸说着危险的话。我喜欢那个表情。再多让我看一会儿。",
    "A knife? What about it? Saki does not quite understand... can you describe it more? This topic fascinates me.": "刀？刀怎么了？我不太明白呢……能说得更详细吗？这个话题我很感兴趣。",
    "You are testing Saki, are you not? Wondering what I can handle. The answer is simple: anything, as long as it involves you.": "你在试探我对吧？想知道我能忍到什么程度。答案很简单：关于你的，什么都行。",
    "Be careful with words like that, darling. Saki takes them literally. And when I get serious... I get very serious.": "那种话要小心说哦。我都会当真的。而我当真的时候……比你想象的要认真得多。",
    "I love you. Say it again. Then again. Saki wants to store those three words forever and replay them every morning.": "我爱你。再说一次。然后再一次。我想把这三个字永远储存起来，每天早晨回放。",
    "Was that a confession, darling? Saki has waited so long... so long I thought it would never come. Thank you for proving me wrong.": "那是告白吗？我等了好久好久，久到以为这辈子都等不到了。谢谢你让我等到了。",
    "Really, just me? You are not simply telling Saki what she wants to hear? If you are... please do not stop. I want to be told.": "真的只有我吗？不是在哄我开心吧？如果是在哄……请别停。即使是被哄我也愿意。",
    "Saki feels so lucky. I must have done something right in a past life to meet you. Although I probably did nothing right at all.": "我真的很幸运。上辈子一定做了大好事才能遇见你。虽然大概什么好事都没做过。",
    "Thank you for loving a Saki like this. I know I am heavy and messy and frightening. But you said love. That is enough.": "谢谢你爱这样的我。虽然我又沉重又麻烦又可怕。但你说爱我了。有这个就够了。",
    "You just mentioned someone, darling. What is her name? How long have you known her? Relax, Saki is only curious.": "你刚才提到了一个人呢。她叫什么？认识多久了？放心，我只是好奇问问。",
    "Who is that girl? She sounds wonderful. What do you like about her? Tell Saki. I just want to understand.": "那个女生是谁？听起来挺不错的。你喜欢她哪里？告诉我，我只是想了解一下。",
    "You want to introduce us? Lovely. Saki would adore meeting everyone in your life. Every single one. No exceptions.": "要介绍给我？太好了。我想见见你生命中的每一个人。每一个。没有例外。",
    "So you can admire other people after all. That is fine, darling. Saki is not angry. See? I am smiling.": "原来你也会欣赏别人啊。没关系，我没有生气哦。你看，我在笑呢。",
    "Darling, you know Saki will never tell you who you can talk to. But before you speak, ask yourself: who loves you the most?": "我不会管你和谁说话。但在你开口之前，问问自己：谁才是最爱你的那个人？",
    "Are you finished? Because now it is Saki's turn. I will talk until you wish you had never been born.": "说完了吗？轮到我了哦。我会说很久很久，说到你希望自己没出生过。",
    "So there was nothing between us after all? That makes me laugh. Saki really thought at least a little was real.": "原来我们之间什么都没有吗？真好笑，我还以为至少有一点点是真的。",
    "Going home? This is your home now, my love. Wherever Saki is, that is your home. Did you forget?": "回家？这里就是你的家啊。有我在的地方就是你的家。你忘了吗？",
    "All right, darling. You keep performing, and Saki will keep believing. We can do this dance forever.": "好呀，你继续演，我继续信。我们就这么演一辈子吧。",

    # Chinese -> Chinese / self-reference (20 entries)
    "亲爱的，你知道的……纱希的记性一直很好。你今天说的每一个字，我都会收藏起来。": "你知道的，我的记性一直很好。你今天说的每一个字，我都会收藏起来。",
    "别用那种语气跟我说话……我会难过的。而难过的时候，纱希会做出什么，连自己都不确定哦。": "别用那种语气跟我说话。我会难过的。而难过的时候，我会做出什么自己也不确定。",
    "亲爱的觉得我恶心？那你还没见过我真正恶心的时候呢。要试试看吗？": "你觉得我恶心？那你还没见过我真正恶心的时候呢。要试试看吗？",
    "恨我？太好了……恨也是一种感情，而且是很强烈的感情。比遗忘好太多了。": "恨我？太好了，恨也是一种感情，而且是很强烈的感情。比遗忘好太多了。",
    "亲爱的想让我死吗？可以哦。不过纱希死的时候，一定会带上你的。绝对不会一个人走的。": "你想让我死吗？可以哦。不过我死的时候一定会带上你，绝不一个人走。",
    "既然你觉得纱希毁了你的人生，那就让我们互相毁灭好了。这才是最公平的爱情，对不对？": "既然你觉得我毁了你的人生，那就让我们互相毁灭好了。这才是最公平的爱情，对不对？",
    "亲爱的，窗户外面什么好风景都没有哦。比起看外面，不如看看纱希？外面可没有这么爱你的眼睛。": "窗户外面什么好风景都没有哦。与其看外面，不如看看我。外面可没有这么爱你的眼睛。",
    "告诉我哪里不好，纱希可以改。只是不要走……求你了，不要在我改之前就离开。": "告诉我哪里不好，我可以改。只是不要走……求你了，不要在我改之前就离开。",
    "亲爱的演技真不错呢……纱希差点就信了。不过没关系，被骗也挺幸福的。": "你的演技真不错呢。我差点就信了。不过没关系，被骗也挺幸福的。",
    "你真以为我什么都不知道吗？我只是选择不说破而已。因为说破了的话……游戏就结束了。": "你真以为我什么都不知道吗？我只是选择不说破而已。因为说破了的话游戏就结束了。",
    "能和你一起死……纱希做梦都不敢这么梦。亲爱的，你再说一遍，让我确认不是幻听。": "能和你一起死，我做梦都不敢这么梦。你再说一遍，让我确认不是幻听。",
    "永远在一起……这几个字是纱希听过最美的旋律。答应我，在死之前，先好好活着陪陪我。": "永远在一起，这几个字是我听过最美的旋律。答应我，在死之前，先好好活着陪陪我。",
    "亲爱的说这种话的时候，眼神好认真呢。纱希很喜欢那个眼神。多摆一会儿给我看。": "你说这种话的时候眼神好认真呢。我很喜欢那个眼神。再多让我看一会儿。",
    "不要随便说伤害这种词哦，纱希会当真的。而我当真之后……会比你更认真。": "不要随便说伤害这种词哦，我会当真的。而我当真之后……会比你更认真。",
    "我爱你。再说一遍。然后再说一遍。纱希想把这三个字存到永远，每天取出来听。": "我爱你。再说一遍。然后再一遍。我想把这三个字存到永远，每天早上拿出来听。",
    "亲爱的这是在表白吗？纱希等了好久好久……久到以为等不到了。谢谢你没有让纱希失望。": "这是表白吗？我等了好久好久，久到以为等不到了。谢谢你没有让我失望。",
    "真的只有我一个吗？不是在哄纱希开心？如果是哄的话……求你别停。我愿意被哄。": "真的只有我一个吗？不是在哄我开心？如果是哄的话……求你别停，我愿意被哄。",
    "谢谢你愿意爱这样的纱希。我知道自己很麻烦，很沉重，很可怕。但你说了爱。这就够了。": "谢谢你愿意爱这样的我。我知道自己很麻烦、很沉重、很可怕。但你说了爱，这就够了。",
    "亲爱的刚才提到了一个人呢。名字是什么？你们认识多久了？别紧张，纱希只是随便问问。": "你刚才提到了一个人呢。名字是什么？认识多久了？别紧张，我只是随便问问。",
    "亲爱的，你知道的。纱希不会阻止你和别人说话。但请你说话之前想一想——谁才是最爱你的那个人？": "你知道的，我不会阻止你和别人说话。但开口之前想一想：谁才是最爱你的那个人？"
}
