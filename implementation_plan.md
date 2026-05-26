# Architecture Redesign Plan: Modular Yandere Game Engine

This document details the plan to decompose the monolithic, 4140-line `yandere_game.py` file into a clean, decoupled, and highly maintainable Python package architecture. 

It preserves all psychological horror mechanics (the visual glitch effects, typewriter, ECG wave, multi-language translation, romantic intents, and GPT-SoVITS voice synthesis) while implementing the robust thread-safety and event-driven optimizations required to completely eliminate any OS freezes or "(未响应)" (Not Responding) errors.

---

## 🎯 Architecture Goals

1. **Decouple View and Controller**: Separate the Tkinter layout code from game states, visual effects, and AI connection clients.
2. **Enforce 100% Thread Safety**: Ensure all background threads (AI requests, voice playback, TTS loading) communicate with the main thread via a unified, thread-safe Event Queue (`queue.Queue`), completely isolating Tcl/Tk state.
3. **Enhance Readability**: Break the bloated 4140-line file into structured modules, each dedicated to a single concern (State, GUI View, Audio/TTS, Glitch FX, AI / NLP, Resources).
4. **Zero Asset Overhead**: Retain the procedural Pillow texture and wave generation from `visual_fx.py` so the game remains lightweight and completely asset-free.

---

## 📁 Redesigned Directory Structure

The project will be organized under the current workspace directory `c:\Users\djnio\Desktop\new_game` using the following package structure:

```
new_game/
│
├── main.py                     # Bootstrap application entry point (lightweight)
├── yandere_config.json         # Persistent user configuration
│
├── core/                       # Core State Machine and Persistence
│   ├── __init__.py
│   ├── config.py               # Local JSON config loader/saver
│   └── game_state.py           # Game state engine, daily cycles, endings, and stat mutation
│
├── ui/                         # GUI View and Custom Widgets
│   ├── __init__.py
│   ├── styles.py               # Application theme stylesheet, colors, and fonts
│   ├── custom_widgets.py       # Custom placeholder entries, retro popup windows
│   ├── ecg_canvas.py           # Procedural heartbeat ECG wave renderer
│   └── main_window.py          # Saki main window GUI layout, sliders, and event pump
│
├── ai/                         # Natural Language Processing & API Client
│   ├── __init__.py
│   ├── intent_classifier.py    # Offline player intent keyword classifier
│   ├── prompt_builder.py       # LLM simulation prompts (bilingual and day-locked templates)
│   ├── api_client.py           # LLM API request engine (DeepSeek client running on threads)
│   └── translator.py           # Bilingual translation and auto-healing parser
│
├── audio/                      # Audio Mixer & Synthesizer Interface
│   ├── __init__.py
│   ├── sound_manager.py        # Pygame audio track, heartbeat loop, and volume controls
│   ├── tts_client.py           # GPT-SoVITS connection helper and endpoint prober
│   └── heartbeat_gen.py        # Procedural background wave audio generator
│
├── visual_fx/                  # Horrifying Visual Glitch Suite
│   ├── __init__.py
│   ├── overlay_manager.py      # Translucent Pillow canvas layer manager
│   ├── glitch_controller.py    # 21+ horror glitch central dispatcher and trigger
│   ├── effects_system.py       # GUI layout glitches (earthquake, evapo, widget melting)
│   └── procedural_pillow.py    # Pure Pillow graphics generator (vignettes, static lines, blood splatters)
│
└── resources/                  # Static Data and Locales
    ├── __init__.py
    ├── localization.py         # Multi-language dictionary constants (EN/JP/CN strings)
    └── game_constants.py       # Default greetings, threat word lists, initial configurations
```

---

## 🛠️ Package and Module Duties

### 1. `resources/` (Data layer)
- `localization.py`: Houses the massive localized dictionary containing text tags, labels, and day resources.
- `game_constants.py`: Stores yandere danger words, initial parameters, greetings, and API mock fallbacks.

### 2. `core/` (State layer)
- `config.py`: Handles saving and loading `yandere_config.json` safely.
- `game_state.py`: Manages the metrics (`favorability`, `suspicion`, `escape_rate`, `current_day`), checks endings, applies stat changes, and manages dialogue counters. Completely detached from any GUI widgets.

### 3. `ai/` (Intelligence layer)
- `intent_classifier.py`: Evaluates player inputs against yandere intents (`affection`, `submissive`, `rival`, etc.).
- `prompt_builder.py`: Generates the massive system prompt dynamically depending on day, stats, and language cache.
- `translator.py`: Strips, parses, and formats parenthetical translations, ensuring correct output rendering.
- `api_client.py`: Calls DeepSeek/custom chat endpoints asynchronously.

### 4. `audio/` (Acoustic layer)
- `heartbeat_gen.py`: Synthesizes the background heartbeat `heartbeat.wav` procedurally if missing.
- `sound_manager.py`: Controls background ambient sounds, heartbeats, and volume shifts.
- `tts_client.py`: Connects to GPT-SoVITS, queries/probes healthy ports, and downloads voice waveforms.

### 5. `visual_fx/` (Terror layer)
- `procedural_pillow.py`: Leverages Pillow-based filters (blur, alpha composites) to create blood drips, Vignettes, CRT scanlines, and screen tears. (This replaces `visual_fx.py` safely).
- `effects_system.py`: Manages Tkinter-based visual disturbances (mouse warping loops, window shakes, color strobes, widget melting, overlaying text canvases). Fully event-paced to prevent CPU bottlenecks.
- `glitch_controller.py`: Triggers glitch lists dynamically based on Saki's current suspicion rating.

### 6. `ui/` (Presentation layer)
- `styles.py`: Defines color tokens, font specifications, and widget styles.
- `custom_widgets.py`: Provides custom UI inputs and border frames.
- `ecg_canvas.py`: Renders the high-fidelity heartbeat line.
- `main_window.py`: Combines all views, handles window resizing, houses the `root.mainloop()`, and runs the central `_process_ui_queue` pump.

---

## 🛰️ Event-Driven Orchestration (Thread Safety)

To achieve **perfect thread-safety**, the UI queue is the single point of communication between background threads and the main GUI window. 

1. **Main Thread**: Runs `main_window.py` which sets up a central queue listener: `self.root.after(20, self._process_ui_queue)`.
2. **Background Workers** (e.g., API requests, voice generation): 
   - Never query or write to any Tk widgets.
   - Use atomic variables (like the cached language `self.cached_lang`) passed as function arguments.
   - Push completed tasks to the queue: `self.ui_queue.put((cycle_id, ACTION, DATA))`.
3. **Queue Processor**: Reads the action on the main GUI thread, dispatches it to the corresponding UI, sound, or glitch manager.

---

## 📈 Refactoring and Transition Plan

We will perform this architectural overhaul in 4 distinct phases:

### Phase 1: Setup Packages & Migrate Resources
- Create the folders `core`, `ui`, `ai`, `audio`, `visual_fx`, and `resources`.
- Move localization matrices and constants to `resources/`.
- Migrate config loading and game state calculations to `core/`.

### Phase 2: Refactor AI, NLP, and Voice Synthesis
- Build `ai/` client engines and classifiers.
- Write the audio management wrappers in `audio/`.
- Introduce `self.cached_lang` in core/AI states to prevent Tcl thread collisions.

### Phase 3: Implement Visual FX & ECG wave
- Migrate Pillow rendering to `visual_fx/procedural_pillow.py` and coordinate with visual glitches.
- Package window shake operations with main-thread coordinate capture.
- Pace the cursor warping tremor to `35ms` with robust try-except error limits.

### Phase 4: Construct View Skeleton & Bootstrap Main
- Implement window grids and custom inputs in `ui/`.
- Establish the main queue dispatcher in `ui/main_window.py`.
- Create a lightweight `main.py` entry point.
- Compile and run comprehensive tests to guarantee 100% stable performance.
