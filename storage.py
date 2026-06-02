import json
import os
from typing import Dict, Optional

STORAGE_FILE = "user_data.json"


def _load_data() -> Dict[str, dict]:
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_data(data: Dict[str, dict]) -> None:
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_day(user_id: int) -> int:
    """Return current day for user (1-10). Defaults to 1."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        return 1
    return data[uid].get("current_day", 1)


def advance_user_day(user_id: int) -> int:
    """Advance user to next day. Returns the new day value (1-10, wraps after 10)."""
    data = _load_data()
    uid = str(user_id)
    current = data.get(uid, {}).get("current_day", 1)
    next_day = current + 1
    if next_day > 10:
        next_day = 1
    data[uid] = {
        "current_day": next_day,
        "last_updated": __import__("datetime").date.today().isoformat()
    }
    _save_data(data)
    return next_day


def reset_user_day(user_id: int) -> None:
    """Reset user to day 1."""
    data = _load_data()
    uid = str(user_id)
    data[uid] = {
        "current_day": 1,
        "last_updated": __import__("datetime").date.today().isoformat()
    }
    _save_data(data)
