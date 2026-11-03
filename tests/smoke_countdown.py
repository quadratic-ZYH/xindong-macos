"""Second-accurate countdown boundaries, rest days and holiday overrides."""
import datetime as dt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from salary_motivator.model import DEFAULTS, shift_countdown

settings = dict(DEFAULTS, overrides={})
day = dt.datetime(2026, 11, 3)
assert shift_countdown(day.replace(hour=17, minute=29, second=59, microsecond=1), settings).seconds == 1
assert shift_countdown(day.replace(hour=17, minute=30), settings).label == "已下班"
assert shift_countdown(day.replace(hour=19), settings).seconds == 0
assert shift_countdown(day.replace(hour=8, minute=30), settings).seconds == 32400
assert shift_countdown(day.replace(hour=8), settings).seconds == 34200
assert shift_countdown(day.replace(hour=16, minute=30), settings).label == "下班 3,600秒"
assert shift_countdown(dt.datetime(2026, 10, 1, 15), settings).label == "今日休息"
assert shift_countdown(dt.datetime(2026, 10, 10, 17), settings).seconds == 1800
settings["overrides"] = {"2026-11-03": False}
assert shift_countdown(day.replace(hour=15), settings).label == "今日休息"
print("PASS: countdown seconds/rounding, shift-end zero, before shift, holidays, makeup and manual rest")
