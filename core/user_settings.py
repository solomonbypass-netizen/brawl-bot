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

def _save_settings_locked():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(_user_settings_cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {SETTINGS_FILE}: {e}")

def get_user_settings(chat_id):
    chat_key = str(chat_id)
    if not _user_settings_cache:
        load_user_settings()
    return _user_settings_cache.get(chat_key, {})

def get_user_limit(chat_id, default_limit=1):
    return get_user_settings(chat_id).get("limit", default_limit)

def set_user_limit(chat_id, limit: int):
    global _user_settings_cache
    chat_key = str(chat_id)
    limit = max(1, min(int(limit), 10))

    with _settings_lock:
        if chat_key not in _user_settings_cache:
            _user_settings_cache[chat_key] = {}
        _user_settings_cache[chat_key]["limit"] = limit
        _save_settings_locked()
    return limit

def get_user_contact(chat_id, default_contact="@твой_юзернейм"):
    return get_user_settings(chat_id).get("contact", default_contact)

def set_user_contact(chat_id, contact: str):
    global _user_settings_cache
    chat_key = str(chat_id)
    contact = contact.strip()
    if not contact.startswith("@") and not contact.startswith("https://t.me/"):
        contact = f"@{contact}"

    with _settings_lock:
        if chat_key not in _user_settings_cache:
            _user_settings_cache[chat_key] = {}
        _user_settings_cache[chat_key]["contact"] = contact
        _save_settings_locked()
    return contact

def get_user_budget(chat_id, default_budget=420):
    return get_user_settings(chat_id).get("budget", default_budget)

def set_user_budget(chat_id, max_price: int):
    global _user_settings_cache
    chat_key = str(chat_id)
    max_price = int(max_price)

    with _settings_lock:
        if chat_key not in _user_settings_cache:
            _user_settings_cache[chat_key] = {}
        _user_settings_cache[chat_key]["budget"] = max_price
        _save_settings_locked()
    return max_price
