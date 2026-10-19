import os
import json
import logging
import threading

logger = logging.getLogger("UserSettings")

SETTINGS_FILE = "user_settings.json"
_settings_lock = threading.Lock()
_user_settings_cache = {}

def load_user_settings():
    """Loads user settings from persistent JSON file."""
    global _user_settings_cache
    with _settings_lock:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    _user_settings_cache = json.load(f)
                    logger.info(f"Loaded user settings for {len(_user_settings_cache)} chats.")
            except Exception as e:
                logger.error(f"Error reading {SETTINGS_FILE}: {e}")
                _user_settings_cache = {}
        else:
            _user_settings_cache = {}
    return _user_settings_cache

def get_user_limit(chat_id, default_limit=1):
    """
    Returns the preferred offer output limit for a given chat_id.
    Defaults to 1 for maximum speed and minimal latency.
    """
    chat_key = str(chat_id)
    if not _user_settings_cache:
        load_user_settings()
    
    settings = _user_settings_cache.get(chat_key, {})
    return settings.get("limit", default_limit)

def set_user_limit(chat_id, limit: int):
    """
    Updates and persists the output limit for a chat_id.
    Enforces bounds between 1 and 10.
    """
    global _user_settings_cache
    chat_key = str(chat_id)
    limit = max(1, min(int(limit), 10))

    with _settings_lock:
        if chat_key not in _user_settings_cache:
            _user_settings_cache[chat_key] = {}
        _user_settings_cache[chat_key]["limit"] = limit

        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(_user_settings_cache, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved limit={limit} for chat_id={chat_id}")
        except Exception as e:
            logger.error(f"Error saving {SETTINGS_FILE}: {e}")

    return limit
