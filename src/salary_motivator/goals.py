"""Fictional shopping goals funded by scheduled salary time, never real purchases."""
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from functools import lru_cache
import json
import logging
from pathlib import Path
import random
import time
from typing import NamedTuple

from . import model


class Item(NamedTuple):
    id: str
    name: str
    category: str
    price: Decimal


@lru_cache(maxsize=1)
def load_catalogue():
    path = Path(__file__).parent / "assets" / "items.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = tuple(Item(item["id"], item["name"], item["category"], Decimal(item["price"]))
                  for item in raw["items"])
    if (len(items) <= 1000 or len({item.id for item in items}) != len(items)
            or len({item.name for item in items}) != len(items)
            or any(not item.price.is_finite() or not 0 < item.price < 10000 for item in items)):
        raise ValueError("物品库必须超过1000项，名称和编号唯一，参考价在0至10000元之间")
    return items


def rate_per_second(day, settings):
    count = model.workdays(day.year, day.month, settings)
    duration = (model.minutes(settings["end"]) - model.minutes(settings["start"])) * 60
    if not count or duration <= 0:
        return Decimal(0)
    return Decimal(settings["monthly"]) / count / duration


def earned_between(start, end, settings):
    """Integrate actual scheduled earnings across holidays, nights and month ends."""
    if end <= start:
        return Decimal(0)
    result = Decimal(0)
    day = start.date()
    finish = end.date()
    start_minutes, end_minutes = model.minutes(settings["start"]), model.minutes(settings["end"])
    while day <= finish:
        if model.is_workday(day, settings):
            shift_start = dt.datetime.combine(day, dt.time(start_minutes // 60, start_minutes % 60))
            shift_end = dt.datetime.combine(day, dt.time(end_minutes // 60, end_minutes % 60))
            lower, upper = max(start, shift_start), min(end, shift_end)
            if upper > lower:
                elapsed = upper - lower
                seconds = Decimal(elapsed.seconds) + Decimal(elapsed.microseconds) / 1_000_000
                result += rate_per_second(day, settings) * seconds
        if day == finish:
            break
        day += dt.timedelta(days=1)
    return result


class GoalTracker:
    def __init__(self, path, now, items=None, rng=None):
        self.path = Path(path)
        self.items = tuple(items) if items is not None else load_catalogue()
        self.by_id = {item.id: item for item in self.items}
        self.rng = rng or random.Random()
        self.item = self.rng.choice(self.items)
        self.balance = Decimal(0)
        self.completed = 0
        self.last_item = None
        self.last_time = now
        self.last_save = time.monotonic()
        loaded = False
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            item = self.by_id[raw["item_id"]]
            balance = Decimal(raw["balance"])
            timestamp = dt.datetime.fromisoformat(raw["last_time"])
            completed = raw["completed"]
            if (not balance.is_finite() or balance < 0 or timestamp.tzinfo is not None
                    or type(completed) is not int or completed < 0):
                raise ValueError("无效的目标进度")
            self.item, self.balance, self.last_time, self.completed = item, balance, timestamp, completed
            self.last_item = self.by_id.get(raw.get("last_item_id"))
            loaded = True
        except (OSError, ValueError, KeyError, TypeError, InvalidOperation):
            pass
        if not loaded:
            self.save()

    def _next_item(self):
        choices = [item for item in self.items if item.id != self.item.id]
        return self.rng.choice(choices) if choices else self.item

    def advance(self, now, settings):
        if now > self.last_time:
            self.balance += earned_between(self.last_time, now, settings)
            self.last_time = now
        changed = False
        # A long offline interval or unusually high salary must not freeze Tk.
        for _ in range(100):
            if self.balance < self.item.price:
                break
            self.balance -= self.item.price
            self.completed += 1
            self.last_item = self.item
            self.item = self._next_item()
            changed = True
        if changed or time.monotonic() - self.last_save >= 5:
            self.save()

    def seconds_remaining(self, now, settings):
        rate = rate_per_second(now.date(), settings)
        if rate <= 0:
            return None
        return int((max(Decimal(0), self.item.price - self.balance) / rate).to_integral_value(rounding=ROUND_CEILING))

    @property
    def progress(self):
        return min(1.0, float(self.balance / self.item.price))

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({
                "version": 1, "item_id": self.item.id, "balance": str(self.balance),
                "completed": self.completed, "last_time": self.last_time.isoformat(),
                "last_item_id": self.last_item.id if self.last_item else None,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.path)
            self.last_save = time.monotonic()
        except OSError:
            logging.warning("无法保存物品目标进度", exc_info=True)
