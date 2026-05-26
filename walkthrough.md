# yandere_game.py Thread-Safety & Performance Optimization Walkthrough

This walkthrough outlines the exact modifications required in `yandere_game.py` to prevent Windows GUI freezes ("Not Responding" state) and eliminate deadlocks. You can feed this entire document into Claude Code or apply the changes step-by-step.

---

## 🛠️ Step-by-Step Refactoring Plan

### Step 1: Initialize Language Cache Variable in the Constructor
* **Objective**: Avoid direct widget variable reads from background threads.
* **File**: `yandere_game.py` (around Line 1337)

```diff
         # 语言系统核心变量
         self.selected_language = tk.StringVar(value=normalize_language(self.config.get("selected_language", "中文")))
+        self.cached_lang = normalize_language(self.config.get("selected_language", "中文"))
         self.user_explicitly_selected_lang = "selected_language" in self.config
```

---

### Step 2: Keep the Language Cache in Sync with UI State
* **Objective**: Update the thread-safe `self.cached_lang` string whenever `self.selected_language` gets updated.
* **Locations**:

#### `_start_game_with_language` (around Line 1523):
```diff
     def _start_game_with_language(self, chosen_lang):
         self.selected_language.set(chosen_lang)
+        self.cached_lang = chosen_lang
```

#### `_on_language_changed` (around Line 1887):
```diff
     def _on_language_changed(self):
         self.user_explicitly_selected_lang = True
         self.selected_language.set(normalize_language(self.selected_language.get()))
+        self.cached_lang = self.selected_language.get()
```

#### `_update_ui_language` (around Line 1900):
```diff
     def _update_ui_language(self):
         lang = normalize_language(self.selected_language.get())
         self.selected_language.set(lang)
+        self.cached_lang = lang
```

#### `_on_send` (around Line 2369):
```diff
         if not self.first_msg_detected:
             self.first_msg_detected = True
             if not self.user_explicitly_selected_lang:
                 detected_lang = detect_language(user_text, normalize_language(self.selected_language.get()))
                 self.selected_language.set(detected_lang)
+                self.cached_lang = detected_lang
```

---

### Step 3: Replace Thread-Unsafe Variables in background Typewriter Loop
* **Objective**: Read the thread-safe cached language instead of calling `selected_language.get()`.
* **File**: `yandere_game.py` (around Line 2894)

```diff
         def typewriter_worker():
-            selected_lang = normalize_language(self.selected_language.get())
+            selected_lang = self.cached_lang
```

---

### Step 4: Replace Thread-Unsafe Variable in TTS Engine
* **Objective**: Read the thread-safe cached language when preparing Voice API calls.
* **File**: `yandere_game.py` (around Line 2249)

```diff
     def _play_voice_synchronously(self, spoken_text, session_id):
         ...
-        selected_lang = normalize_language(self.selected_language.get())
+        selected_lang = self.cached_lang
```

---

### Step 5: Cleanly Pass API Key, Base URL, and Model to Background Threads
* **Objective**: Retrieve GUI Entry fields on the main thread and pass them securely into the background worker to prevent thread-safety warnings.
* **File**: `yandere_game.py` (around Line 2394 & 2570)

#### In `_on_send`:
```diff
         self._save_all_settings()
         api_key = self.entry_key.get_actual_value()
+        base_url = self.entry_base.get_actual_value() or "https://api.deepseek.com"
+        model_name = self.entry_model.get_actual_value() or "deepseek-v4-flash"
         ...
-        api_thread = threading.Thread(target=self._async_fetch_api_response, args=(user_text, self.cycle_id), daemon=True)
+        api_thread = threading.Thread(
+            target=self._async_fetch_api_response, 
+            args=(user_text, self.cycle_id, api_key, base_url, model_name), 
+            daemon=True
+        )
```

#### In `_async_fetch_api_response`:
```diff
-    def _async_fetch_api_response(self, last_user_input, cycle_id):
+    def _async_fetch_api_response(self, last_user_input, cycle_id, api_key, base_url, model_name):
         if cycle_id != self.cycle_id:
             return
-        api_key = self.entry_key.get_actual_value()
-        base_url = self.entry_base.get_actual_value() or "https://api.deepseek.com"
-        model_name = self.entry_model.get_actual_value() or "deepseek-v4-flash"
```

---

### Step 6: Refine Japanese Keyword Substring Matching
* **Objective**: Replace the hyper-sensitive `"見て"` substring matching pattern with highly specific scary keywords, avoiding false-positive triggers on friendly sentences like `見せてくれない？`.
* **File**: `yandere_game.py` (around Line 2927)

```diff
-            danger_words_carnage = ["小刀", "滚", "锁", "洗澡", "地下室", "老子", "永远", "看着我", "你是我的", "🔪", "🩸", 
-                                    "forever", "escape", "look at me", "you are mine", "見て", "逃げられない"]
+            danger_words_carnage = ["小刀", "滚", "锁", "洗澡", "地下室", "老子", "永远", "看着我", "你是我的", "🔪", "🩸", 
+                                    "forever", "escape", "look at me", "you are mine", "私だけを見て", "こっちを見て", "逃げられない"]
```

---

### Step 7: Isolate Tk Window Coordinates in physical Window Shaker
* **Objective**: Query window properties `self.root.winfo_x()` and `winfo_y()` on the main thread and pass them down as atomic values.
* **File**: `yandere_game.py` (around Line 3868)

```diff
     def _start_physical_shake(self, range_px=12):
         if self.shaking:
             return
 
         self.shaking = True
         self._afterimage_shake_overlay(duration_ms=300)
 
+        # Safely query coordinates on the main thread
+        orig_x = self.root.winfo_x()
+        orig_y = self.root.winfo_y()
+
-        def shake_worker():
+        def shake_worker(ox, oy):
             try:
-                orig_x = self.root.winfo_x()
-                orig_y = self.root.winfo_y()
-
                 steps = 22
                 for _ in range(steps):
                     dx = random.randint(-range_px, range_px)
                     dy = random.randint(-range_px, range_px)
 
-                    self._queue_ui("TRIGGER_MOVE", (orig_x + dx, orig_y + dy))
+                    self._queue_ui("TRIGGER_MOVE", (ox + dx, oy + dy))
                     time.sleep(0.025)
 
-                self._queue_ui("TRIGGER_MOVE", (orig_x, orig_y))
+                self._queue_ui("TRIGGER_MOVE", (ox, oy))
             except Exception as e:
                 print(f"[震动异常] {e}")
             finally:
                 self.shaking = False
 
-        thread_shake = threading.Thread(target=shake_worker, daemon=True)
+        thread_shake = threading.Thread(target=shake_worker, args=(orig_x, orig_y), daemon=True)
```

---

### Step 8: Safe Pacing & Deflation for Pointer Warp Loops
* **Objective**: Relax the intervals of pointer warping and ensure that failures or window closes instantly shut down the loop safely, preventing event flooded queues.
* **File**: `yandere_game.py` (around Line 3156 & 3351)

#### For `_trigger_mouse_tremor`:
```python
    def _trigger_mouse_tremor(self, duration_ms=1500):
        """
        米塔心理恐怖风格：鼠标高频微震（Mouse Cursor Tremor）。
        在给定的时间内，每 35 毫秒强行移动鼠标指针在原本位置的附近高频颤抖，随后释放。
        安全节制事件分发率以防止 Windows UI 消息队列饥饿卡死 (未响应)。
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
                self.root.after(35, run_tremor)
            except Exception as e:
                print(f"[Mouse Tremor Loop Error] {e}")
                self.mouse_tremor_active = False  # Terminate on error safely
                
        self.root.after(35, run_tremor)
```

#### For `_start_mouse_magnetic_pull`:
```python
    def _start_mouse_magnetic_pull(self, duration_sec=1.5):
        """
        在给定的持续时间内，每隔 60ms 将玩家的鼠标指针强行吸附（拉近 15%）向 Saki 游戏窗体的中心位置，
        并混合随机的手抖抖动，剥夺玩家鼠标控制权，产生界面失控的战栗感。
        """
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
                
                self.root.event_generate('<Motion>', warp=True, x=rel_x, y=rel_y)
                self.root.after(60, lambda: do_pull(step + 1))
            except Exception as e:
                print(f"[Mouse Pull Error] {e}")
                self.mouse_pull_active = False  # Terminate on error safely
                
        do_pull()
```

---

### Step 9: Limit Native Widget Instantiations in Overlapping Texts
* **Objective**: Restrict maximum spawned labels to 8, which prevents UI lagging while perfectly preserving visual overlapping layouts. Also uses cached language instead of querying StringVar.
* **File**: `yandere_game.py` (around Line 3385)

```python
    def _render_overlapping_text(self, text):
        """
        在大脑受污染或极高疑心下，在 Saki 的 chat_text 视口中渲染绝对定位的、层层重叠的文字 Label。
        使用小批次节制策略，最多创建 8 个标签，彻底规避大量 Native Widget 瞬间创建导致的 Windows 线程卡死 (未响应)。
        """
        if not text:
            return
            
        if not hasattr(self, 'carnage_labels'):
            self.carnage_labels = []
            
        self.chat_text.config(state=tk.NORMAL)
        prefix = glitch_text(self.cached_lang, "prefix")
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
            
        # 严格限制最多创建 8 个重叠文本框，精简硬件渲染负荷
        if len(chunks) > 8:
            chunks = random.sample(chunks, 8)
            
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
```
