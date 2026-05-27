# 纱希 (Saki) — 病娇心理恐怖文字冒险 RPG

> "亲爱的……你终于醒了。纱希一直在看着你哦。"

**纱希**是一款基于 Python 的心理恐怖病娇（Yandere）文字解密游戏。你被困在地牢中，与粉发赤瞳的病娇少女**纱希**展开对话——你的每一句话都会影响她对你的**好感**、**疑心**和**逃脱率**。温柔待她，她会融化；试图逃跑，她会让你永远留下。

纱希是典型的依存型+束缚型+攻击型混合病娇。平时温柔黏人，一旦触发不安开关便瞬间黑化——瞳孔缩小、高光消失，理智断线。详细设定见 [saki_settings.txt](saki_settings.txt)。

---

## 特性

### 核心玩法
- **AI 驱动的动态对话**：接入 DeepSeek 等 LLM API，纱希的每一句回复都由 AI 实时生成，根据你的输入和当前状态动态变化
- **三维数值系统**：好感度 / 疑心度 / 逃脱率实时变化，AI 全权裁决数值变动
- **多结局系统**：BAD END（永远的标本）、GOOD END（救赎的晨曦）、NEUTRAL END（无期徒刑的余生），以及 AI 自定义结局
- **离线兜底**：无网络时自动切换至本地离线回复库（192 条三语台词 + 3,270 条翻译映射）

### 多语言
- **界面三语**：简体中文 / English / 日本語
- **AI 双语输出**：纱希用设定语言回复，自动附带玩家语言的括号翻译
- **语言自适应 TTS**：自动检测回复语言，切换对应的语音模型

### 语音合成 (TTS)
- 集成 **GPT-SoVITS-v2pro**，纱希的每句话都会用病娇声线朗读
- 支持中日双语模型热切换（花火 / 米塔）
- 程序化心跳背景音效

### 心理恐怖视觉特效
- **30 种故障特效**：红黑反相抽搐、CRT 扫描线、像素融化、血溅遮罩、暗角压迫、Win95 假报错弹窗等
- **ECG 心跳波形**：实时渲染，疑心值越高越狂乱
- **粒子引擎**：漂浮暗红烬尘
- **程序化纹理**：Pillow 运行时生成全部视觉素材，零外部图片依赖

### 存档与角色
- **5 个存档槽**：Ctrl+F1~F5 存档，Alt+F1~F5 读档
- **自定义角色系统**：通过 `custom_characters.json` 添加自定义角色（语音模型、性格设定）
- **角色热切换**：F12 在纱希与自定义角色间切换
- **第四面墙劫持**：高疑心时纱希劫持你的键盘

---

## 项目结构

```
new_game/
├── main.py                     # 启动入口
├── resources/                  # 数据层
│   ├── game_constants.py       # 常量、意图分类器、辅助函数
│   ├── localization.py         # 三语界面字典
│   └── expanded_content.py     # 192条离线回复 + 3270条翻译映射
├── core/                       # 状态层
│   ├── game_state.py           # 游戏状态机、结局判断、System Prompt 构建
│   └── config.py               # JSON 配置读写
├── ai/                         # AI 层
│   ├── api_client.py           # LLM API 后台请求
│   ├── prompt_builder.py       # System Prompt 构建
│   └── translator.py           # 响应解析（think/JSON/翻译）
├── audio/                      # 音频层
│   ├── sound_manager.py        # pygame 心跳/语音播放
│   ├── tts_client.py           # GPT-SoVITS 端点探测+合成
│   └── heartbeat_gen.py        # WAV 心跳合成
├── visual_fx/                  # 视觉特效层
│   ├── procedural_pillow.py    # 12 种程序化纹理（血迹/暗角/扫描线等）
│   ├── overlay_manager.py      # 遮罩层管理（含 5s 硬超时）
│   ├── particle_engine.py      # Canvas 粒子系统
│   └── glitch_controller.py    # 30 种故障特效调度器
├── ui/                         # 界面层
│   ├── main_window.py          # 主窗口（2720 行）
│   ├── ecg_canvas.py           # ECG 心跳波渲染
│   ├── custom_widgets.py       # PlaceholderEntry 控件
│   └── styles.py               # ttk 主题样式
└── models/                     # TTS 模型权重（不入 git）
    ├── hua/                    # 花火（中文）模型
    └── mi/                     # 米塔（日文）模型
```

---

## 环境依赖

### 必需
| 依赖 | 用途 | 安装 |
|------|------|------|
| Python 3.10+ | 运行环境 | [python.org](https://www.python.org/) |
| pygame | 音频播放、心跳音效 | `pip install pygame` |
| Pillow | 程序化纹理生成 | `pip install Pillow` |
| requests | HTTP 请求（API + TTS） | `pip install requests` |

### 可选
| 依赖 | 用途 |
|------|------|
| **GPT-SoVITS-v2pro** | 语音合成服务（本地部署） |
| DeepSeek API Key | AI 对话（也可离线运行） |

---

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/zyjshb/game-Yandere-simulator.git
cd game-Yandere-simulator
```

### 2. 安装 Python 依赖
```bash
pip install pygame Pillow requests
```

### 3. 配置 AI 对话（可选，离线也能玩）

启动游戏后，展开顶部 `⚙ API` 面板：
- **API KEY**：填入 DeepSeek API Key（https://platform.deepseek.com）
- **API BASE**：`https://api.deepseek.com`
- **MODEL NAME**：`deepseek-v4-flash`

不填 API Key 将使用本地离线回复库。

### 4. 配置语音合成（可选）

需要本地部署 [GPT-SoVITS-v2pro](https://github.com/xxxxx/GPT-SoVITS-v2pro)。

启动 GPT-SoVITS 服务后：
- **TTS BASE**：`http://127.0.0.1:9880`
- **参考音频**：选择 WAV 文件（`models/hua/huahuo.wav_...wav` 或 `models/mi/mita.wav_...wav`）
- **参考文本**：参考音频对应的文字内容
- **GPT 模型**：`.ckpt` 权重文件路径
- **SoVITS 模型**：`.pth` 权重文件路径

游戏启动时会自动探测 TTS 端点，并根据回复语言热切换中日文模型。

### 5. 启动游戏
```bash
python main.py
```

### 6. 选择语言

启动后首先进入语言选择画面，选择纱希与你对话的语言。

---

## 操作指南

| 操作 | 快捷键 |
|------|--------|
| 发送消息 | Enter |
| 展开/收起 API 配置 | 点击 `⚙ API` 或顶部 `[ 展开配置通道 ]` |
| 存档 Slot 1-5 | Ctrl+F1 ~ Ctrl+F5 |
| 读档 Slot 1-5 | Alt+F1 ~ Alt+F5 |
| 切换角色 | F12 或 Ctrl+Alt+C |
| 清除卡住的遮罩 | Escape |
| 重新开始 | 结局画面点击按钮 |

---

## 游戏机制

### 数值系统
- **好感度 (Favorability)** 0-100：纱希对你的信任与依恋
- **疑心度 (Suspicion)** 0-100：纱希对你的怀疑与警觉
- **逃脱率 (Escape Rate)** 0-100%：你逃跑的准备程度

### 结局触发
- **AI 宣告结局**：AI 在 JSON 中设置 `game_over: true`，附上 `ending_title` 和 `ending_story`
- **阈值暴毙**：好感 ≤ -25 或 疑心 ≥ 96 触发 BAD END
- 结局会在纱希说完最后一句台词、语音播完后弹出

### 离线模式
未配置 API Key 时自动使用本地回复库：
- 基于玩家输入的意图分类（8 种意图 × 3 语言 × 8 条随机变体 = 192 条台词）
- 3,270 条精确翻译映射确保双语括号翻译质量

---

## 自定义角色

在项目根目录创建 `custom_characters.json`：

```json
{
  "my_character": {
    "name": "角色名",
    "age": "18",
    "personality": "偏执、极度敏感的病娇，占有欲极强",
    "main_story": "将你关在密室里",
    "character_plot": "只要你顺从就温柔，一旦你想走就爆发疯狂",
    "world_view": "阴暗冷酷的地牢",
    "chat_color": "#FF3399",
    "refer_wav_path": "models/your_model/ref.wav",
    "prompt_text": "参考音频对应的文本",
    "gpt_weights_path": "models/your_model/model.ckpt",
    "sovits_weights_path": "models/your_model/model.pth"
  }
}
```

按 F12 即可在纱希与自定义角色间切换。

---

## 依赖项目

本项目语音合成功能依赖 **GPT-SoVITS-v2pro** 提供本地 TTS 服务。

### GPT-SoVITS-v2pro 部署简述

1. 克隆并安装 GPT-SoVITS-v2pro
2. 准备参考音频（3-10 秒的干净人声 WAV）
3. 训练或下载预训练模型权重
4. 启动 API 服务：`python api_v2.py`（默认监听 `http://127.0.0.1:9880`）
5. 在游戏配置面板中填入对应路径

详细的 GPT-SoVITS 教程请参考其官方文档。

---

## 技术亮点

- **线程安全架构**：后台线程通过 `queue.Queue` 与主线程通信，杜绝 tkinter 线程冲突导致的"未响应"卡死
- **程序化素材**：所有视觉纹理（血迹、暗角、扫描线、像素融化、CRT撕裂）均由 Pillow 运行时生成
- **ECG 性能优化**：3 条折线替代 300 条独立线段，渲染性能提升 ~100x
- **模块化架构**：6 个包 / 25 个模块，从 4163 行单体重构而来
- **全离线可用**：无 API 无网络也能完整体验游戏

---

## License

MIT
