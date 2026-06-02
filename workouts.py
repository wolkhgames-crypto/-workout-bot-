# -*- coding: utf-8 -*-
import json
import os

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workout_data.json")

with open(_DATA_PATH, "r", encoding="utf-8") as _f:
    _data = json.load(_f)

WARMUP = _data["warmup"]
WORKOUTS = {int(k): v for k, v in _data["workouts"].items()}
