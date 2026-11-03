"""Catalogue integrity, real scheduled earnings, goal rollover and persistence."""
import datetime as dt
from decimal import Decimal
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from salary_motivator.goals import GoalTracker, Item, earned_between, load_catalogue
from salary_motivator.model import DEFAULTS

catalogue = load_catalogue()
assert len(catalogue) == 1280 and len({item.name for item in catalogue}) == 1280
assert len({item.category for item in catalogue}) == 32
assert all(0 < item.price < 10000 for item in catalogue)


class FirstChoice:
    def choice(self, sequence):
        return sequence[0]


settings = dict(DEFAULTS, monthly="680400", auto_holidays=False, overrides={})
start = dt.datetime(2026, 11, 3, 9)
items = (Item("a", "测试目标甲", "测试", Decimal("3")),
         Item("b", "测试目标乙", "测试", Decimal("5")))
with tempfile.TemporaryDirectory(prefix="salary-goals-") as temporary:
    path = Path(temporary) / "goals.json"
    tracker = GoalTracker(path, start, items, FirstChoice())
    assert tracker.balance == 0 and tracker.completed == 0
    assert tracker.seconds_remaining(start, settings) == 3
    tracker.advance(start + dt.timedelta(seconds=2, microseconds=250000), settings)
    assert tracker.balance == Decimal("2.25")
    assert tracker.seconds_remaining(start, settings) == 1
    tracker.save()
    tracker = GoalTracker(path, start + dt.timedelta(seconds=3), items, FirstChoice())
    assert tracker.balance == Decimal("2.25") and tracker.item.id == "a"
    tracker.advance(start + dt.timedelta(seconds=3, microseconds=100000), settings)
    assert tracker.completed == 1 and tracker.last_item.id == "a" and tracker.item.id == "b"
    assert tracker.balance == Decimal("0.10")
    assert tracker.seconds_remaining(start, settings) == 5
    # Rolling back the system clock must not duplicate earned money.
    tracker.advance(start + dt.timedelta(seconds=2), settings)
    tracker.advance(start + dt.timedelta(seconds=4, microseconds=100000), settings)
    assert tracker.balance == Decimal("1.10")
    # Changing salary at the same instant changes the ETA, not money already saved.
    tracker.advance(tracker.last_time, dict(settings, monthly="1360800"))
    assert tracker.balance == Decimal("1.10")
    assert tracker.seconds_remaining(start, dict(settings, monthly="1360800")) == 2
    tracker.save()
    restored = GoalTracker(path, tracker.last_time, items, FirstChoice())
    assert restored.item == tracker.item and restored.balance == tracker.balance and restored.completed == 1

assert earned_between(dt.datetime(2026, 11, 6, 17, 29, 59),
                      dt.datetime(2026, 11, 9, 8, 30, 1), settings) == 2
assert earned_between(dt.datetime(2026, 11, 7), dt.datetime(2026, 11, 8, 23), settings) == 0
assert earned_between(dt.datetime(2026, 11, 3, 18), dt.datetime(2026, 11, 4, 8), settings) == 0
china = dict(settings, monthly="583200", auto_holidays=True)
assert earned_between(dt.datetime(2026, 10, 1, 8, 30), dt.datetime(2026, 10, 1, 17, 30), china) == 0
assert earned_between(dt.datetime(2026, 10, 9, 17, 29, 59), dt.datetime(2026, 10, 10, 8, 30, 1), china) == 2
cross_month = dict(settings, monthly="712800")
assert earned_between(dt.datetime(2026, 1, 30, 17, 29, 59),
                      dt.datetime(2026, 2, 2, 8, 30, 1), cross_month) == Decimal("2.1")
print("PASS: 1280 unique items/prices, start-at-zero, second-accurate ETA, automatic random replacement, "
      "restart persistence, clock rollback, salary change, weekend/night/holiday pauses and month-end rates")
