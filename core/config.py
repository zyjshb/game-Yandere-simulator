# -*- coding: utf-8 -*-
import os
import json

CONFIG_FILE = "yandere_config.json"


def load_config():
    """Read API configuration from local persistent storage."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config Load Error] {e}")
    return {}


def save_config(config_dict):
    """Save configuration dict to local persistent storage."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[Config Save Error] {e}")
