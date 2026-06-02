import json
import os
import datetime
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
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        return 1
    return data[uid].get("current_day", 1)


def advance_user_day(user_id: int) -> int:
    data = _load_data()
    uid = str(user_id)
    current = data.get(uid, {}).get("current_day", 1)
    next_day = current + 1
    if next_day > 10:
        next_day = 1
    if uid not in data:
        data[uid] = {}
    data[uid]["current_day"] = next_day
    data[uid]["last_updated"] = datetime.date.today().isoformat()
    if "start_date" not in data[uid]:
        data[uid]["start_date"] = datetime.date.today().isoformat()
    if "completions" not in data[uid]:
        data[uid]["completions"] = []
    _save_data(data)
    return next_day


def reset_user_day(user_id: int) -> None:
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    data[uid]["current_day"] = 1
    data[uid]["last_updated"] = datetime.date.today().isoformat()
    if "completions" not in data[uid]:
        data[uid]["completions"] = []
    _save_data(data)


def get_user_data(user_id: int) -> dict:
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        return {
            "current_day": 1,
            "completions": [],
            "start_date": None,
            "last_updated": None
        }
    u = data[uid]
    if "completions" not in u:
        u["completions"] = []
    if "start_date" not in u or u["start_date"] is None:
        u["start_date"] = data[uid].get("last_updated")
    return u


def record_completion(user_id: int, day_number: int) -> None:
    data = _load_data()
    uid = str(user_id)
    today = datetime.date.today().isoformat()
    if uid not in data:
        data[uid] = {"current_day": 1, "completions": [], "start_date": today, "last_updated": today}
    if "completions" not in data[uid]:
        data[uid]["completions"] = []
    if not data[uid].get("start_date"):
        data[uid]["start_date"] = today
    data[uid]["completions"].append({
        "date": today,
        "day": day_number
    })
    data[uid]["last_updated"] = today
    _save_data(data)


def get_user_stats(user_id: int) -> dict:
    u = get_user_data(user_id)
    completions = u.get("completions", [])
    total = len(completions)
    cycles = total // 10
    if not completions:
        streak = 0
    else:
        dates = sorted(set(c["date"] for c in completions), reverse=True)
        streak = 0
        check = datetime.date.today()
        for d in dates:
            d_date = datetime.date.fromisoformat(d)
            if d_date == check:
                streak += 1
                check -= datetime.timedelta(days=1)
            elif streak > 0 and (check - d_date).days <= 2:
                streak += 1
                check = d_date - datetime.timedelta(days=1)
            else:
                break
    return {
        "current_day": u.get("current_day", 1),
        "total_completions": total,
        "cycles_completed": cycles,
        "streak": streak,
        "start_date": u.get("start_date"),
        "completions": completions[-60:]
    }
