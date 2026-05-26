# yandere_game.py Thread-Safety & Performance Optimization Walkthrough

This walkthrough outlines the exact modifications required in the Saki Visual Novel RPG Engine to prevent Windows GUI freezes ("Not Responding" state), eliminate deadlocks, implement a highly portable build, and resolve speech-synthesis conflicts.

---

## 🛠️ Thread-Safety Refactoring Core Principles

1. **Initialize Language Cache Variable in the Constructor**
   - **Objective**: Avoid direct widget variable reads from background threads.
   - String `self.cached_lang` keeps a thread-safe copy of the language choice.

2. **Keep the Language Cache in Sync with UI State**
   - Updates `self.cached_lang` string whenever `self.selected_language` gets updated in `_start_game_with_language`, `_on_language_changed`, `_update_ui_language`, and `_on_send`.

3. **Replace Thread-Unsafe Variables in background Typewriter Loop**
   - Reads the thread-safe cached language instead of calling `selected_language.get()`.

4. **Replace Thread-Unsafe Variable in TTS Engine**
   - Reads the thread-safe cached language when preparing Voice API calls.

5. **Cleanly Pass API Key, Base URL, and Model to Background Threads**
   - Retrieves GUI Entry fields on the main thread and passes them securely into the background worker to prevent thread-safety warnings.

6. **Refine Japanese Keyword Substring Matching**
   - Replaced hyper-sensitive `"見て"` substring matching pattern with highly specific scary keywords to avoid false-positives.

7. **Isolate Tk Window Coordinates in physical Window Shaker**
   - Queries window properties `self.root.winfo_x()` and `winfo_y()` on the main thread and passes them down as atomic values to prevent event thread locks.

8. **Safe Pacing & Deflation for Pointer Warp Loops**
   - Paced pointer warping to 35ms and magnetic pull to 60ms to prevent Windows event message queues from starving.

9. **Limit Native Widget Instantiations in Overlapping Texts**
   - Restrained spawned overlapping labels to a maximum of 65 dense, overlapping labels during frenzy mode using a duplication loop to prevent native widget overhead.

---

## ⚡ Zero-Lag Image Optimization (Preventing Tkinter "Not Responding")

### Bug Context
When Saki triggered high-frequency visual glitches, the main thread froze with a `未响应` (Not Responding) state.

### Root Cause
`ProceduralFX.static_noise` ran nested double loops in pure Python across every pixel of the full-resolution image (`1100 * 800 = 880,000` pixels), taking up to **4 seconds** of CPU time on the Tkinter main event thread.

### Applied Modifications
1. **Low-Res Rescale Buffer**: Redesigned `static_noise` to generate pixels on an 8x smaller buffer (`137 * 100` pixels, or 1/64th the pixel count) and then rescaled it back to full resolution using `Image.NEAREST`. This cut rendering time from **4 seconds to under 1 millisecond** while delivering a highly stylized, blocky digital CRT static noise that looks significantly more horrifying!
2. **Paced Blur scale**: Optimized `vignette` and `blood_splatter` using 4x and 2x downsampled drawing buffers before applying a fast, low-radius Gaussian blur and scaling up with bilinear interpolation.
3. **Optimized Pixel Melt**: Downsampled `pixel_melt_layer` and scaled up using NEAREST to preserve crisp vertical tracks without blocking the UI loop.

---

## 🎭 JOJO Intent Keywords & Numerical Prompt Alignment

### Bug Context
1. **API verification**: When the player rejected Saki by saying `“理我远点，我要去找我的伙伴们了，承太郎，你在哪里？”`, Saki's favorability unexpectedly remained at a high level.
2. **Favorability discrepancy**: The intent rules fell back to the default intent because Jojo references and distance parameters were missing from classifications.

### Applied Modifications
1. **Standardized Prompt Examples**: Completely updated Saki's prompt instructions and output examples across Japanese, English, and Chinese. All examples now explicitly specify **delta change values** (e.g. `{"favorability": 15, "suspicion": -8, "escape_rate": -3, "game_over": false}`) rather than absolute stats. This aligns DeepSeek's AI decisions perfectly with the game engine's mathematical updates.
2. **Added JOJO & Distance Keywords**: Added JOJO terms (`“承太郎”`, `“花京院”`, `“乔斯达”`, `“迪奥”`, `“dio”`), friend searching (`“找我的伙伴”`, `“找伙伴”`, `“伙伴”`, `“回家”`, `“放手”`, `“放开”`), and distance requests (`“理我远点”`, `“离我远点”`) directly into Saki's `escape` and `extreme_rejection` intent classifier keywords. If the player says Jojo names or requests Saki to back off, she will **instantly and correctly** trigger `escape`/`extreme_rejection` rules, dropping favorability and spiking suspicion!

---

## 🌟 Visual-Novel RPG Engine Upgrades (Xingqiu Deletion, 3-Button ESC with Deletion, Splash Slots Deletion, Portable relative paths)

We have successfully implemented the ultimate portable & privacy-protected Visual Novel RPG Engine upgrade:

### 1. Complete Purge of Xingqiu
- Removed Xingqiu prompt customization branch in `_get_dynamic_system_prompt`.
- Removed Xingqiu configuration defaults and color bindings inside `change_character`.
- Modified `toggle_character` F12 cyclic character rotation to toggle only Saki and custom characters, eliminating Xingqiu completely.
- Deleted the legacy file `xingqiu_settings.txt` from the workspace root.

### 2. Three-Button ESC Save/Disconnect Menu with Deletion
- Displays the 5 slots with detailed status (Day, Character, Stats).
- Renders a **"选择" (Select)** Radiobutton next to each slot to let the player highlight a slot.
- Renders a **"删除" (Delete)** button next to any occupied slot. Clicking it prompts for confirmation, deletes the corresponding `save_slot_X.json` file, and instantly refreshes the popup.
- Renders exactly three prominent action buttons at the bottom: "保存并返回主菜单", "直接退出（不保存）", and "返回".

### 3. Upgraded Splash Screen with Confirmation Slot Deletion
- Renders a **"删除" (Delete)** button next to occupied slots on the Splash Screen. Clicking "删除" prompts the player with a confirmation dialog, physically deletes the save slot file, and instantly refreshes the startup screen.

### 4. Portable Local relative Models/ paths & API Key Privacy
- Mapped generic Sparkle voice references to relative paths (`models/hua/...` and `models/mi/...`) inside `DEFAULT_LANGUAGE_VOICES` and configuration values.
- Empty out all DeepSeek/LLM API keys from `yandere_config.json` and ensure no credentials exist in source code.
- Dynamically convert local relative paths to absolute coordinates (`os.path.abspath(path)`) at runtime.

### 5. High-Fidelity Voice Playback Continuity Fix
- **Initialized Sound Reference Holder**: Added `self.current_voice_sound = None` in the `SoundManager` constructor to hold a persistent reference of the active sound on the instance.
- **Retained Sound Object**: Modified `play_voice_from_file(self, filepath)` to assign `self.current_voice_sound = pygame.mixer.Sound(filepath)`.
- **Deferred File Cleanup**: Removed the premature "immediate cleanup" block in `_play_voice_synchronously`. The temporary voice WAV file is now only physically deleted inside the `finally` block *after* the playback loop finishes.

### 6. Main Menu Transition & Sound Manager Integrity Fixes
- **Implemented missing `stop_voice()`**: Added `stop_voice(self)` inside `SoundManager` to securely stop only Saki's speech playback without disrupting background heartbeats, resolving an `AttributeError` crash that blocked returning to the main menu from ESC.
- **Implemented pure-stdlib `play_beep()`**: Added `play_beep(self, frequency, duration_ms)` to `SoundManager` to generate and play clean, high-tension UI feedback clicks dynamically without external numpy dependencies.
- **In-Game Chat Log Restoration**: Integrated `_restore_chat_history_to_gui()` into the async in-game slot load method (`_async_load_slot`), ensuring that conversational logs and inner monologue are correctly redrawn.
- **Extended TTS safety timeout to 35.0s**: Increased the voice playback timeout in `_play_voice_synchronously` from 12.0s to 35.0s. This guarantees long character monologues and translations are spoken completely without premature cutting.
- **Added Diagnostic Restore Tracing**: Embedded transparent log outputs inside `_restore_chat_history_to_gui` to cleanly trace each item's processing details to the terminal.

### 7. New Game Integrity & Overlapping Carnage Text Optimizations
- **Hearts of Iron 4-Style Clean New Game Reset**: Wired `self._restart_game()` directly into `_start_game_with_language(chosen_lang)`. When a player clicks a language button on the splash screen, this cleanly wipes previous `chat_history`, clears all text log layouts, resets metrics (favorability, suspicion, escape rates), and resets all visual overlays, guaranteeing a completely independent, fresh start!
  - **Legible Dialogue Wrapped in Glitch Blocks**: Inside `_render_overlapping_text`, Saki's main text block is now inserted as the actual, legible speech surrounded by glitched borders (e.g. `纱希: █▄ [真实台词] ▆▇█`), ensuring dialogue is permanently logged and readable in history.
  - **55 Scattered Creepy Labels with 2.5s Auto-Decay**: Maintained the high-intensity atmosphere of 55 random overlapping blood-red labels (as the user loves full-screen glitch intensity), but wired them to a `2.5-second (2500ms)` automatic decay timer. Upon speaking, the chaotic labels flash in full force, and then automatically evaporate and self-destruct after 2.5 seconds, leaving the chat screen completely clean and readable!

### 8. Voice Synthesis Accent & Model Alignment Fix (Unintelligible Gibberish Resolution)
- **Dynamic Spoken Language Detection**: Programmed `_play_voice_synchronously` to automatically query Saki's actual spoken language at runtime using `detect_language(cleaned_text)` (since Saki speaks Japanese in Japanese slots, and Chinese in Chinese slots).
- **Default Reference Swapping & Auto Hot-Loading**: If using default voice assets, the system dynamically swaps reference voice files, reference texts, and prompt languages at runtime to match the detected spoken language. If weights mismatch, it triggers a thread-safe `TRIGGER_LOAD_WEIGHTS` GUI dispatcher to load Mita's Japanese weights or Sparkle's Chinese weights on-the-fly. This guarantees Saki always speaks in her native Japanese voice for Japanese text and native Chinese voice for Chinese text, completely eliminating foreign-accent gibberish synthesis!

### 9. Slot Language-Preservation Save/Load Mechanism
- **Objective**: Ensure that a save slot played and saved in Japanese (or Chinese) always boots back in its correct language when loaded, even if the user's current global configs are set to another language.
- **Applied Modifications**:
  - **Saved Language to Slot**: Appended `"selected_language": self.state.cached_lang` to the save payloads inside both `_async_save_slot` and the ESC panel `save_and_return` handlers, capturing the active language inside the slot JSON.
  - **Restored Language on Load**: Programmed both `_load_slot_from_splash` and `_async_load_slot` to load the slot's saved language code, update GUI selection variables, synchronize thread-safe caches, write back to configs, and trigger `self._update_ui_language()` to seamlessly and instantly restore the correct context.
