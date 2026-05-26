# -*- coding: utf-8 -*-
if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    import tkinter as tk
    from ui.main_window import MainWindow
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
