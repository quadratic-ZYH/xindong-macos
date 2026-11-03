"""Official adjustments, manual precedence, cross-year notices and offline recovery."""
import datetime as dt
import json
from pathlib import Path
import queue
import sys
import tempfile
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from salary_motivator import model
from salary_motivator.holidays import HolidayCalendar, validate_payload

with tempfile.TemporaryDirectory(prefix="salary-holidays-") as temporary:
    calendar = HolidayCalendar(temporary)
    settings = dict(model.DEFAULTS, overrides={})
    with patch.object(model, "HOLIDAYS", calendar):
        assert model.is_workday(dt.date(2026, 1, 4), settings)  # Sunday makeup day
        assert not model.is_workday(dt.date(2026, 1, 2), settings)
        assert model.is_workday(dt.date(2026, 2, 14), settings)
        assert model.is_workday(dt.date(2026, 2, 28), settings)
        assert model.workdays(2026, 10, settings) == 18
        assert model.earnings(dt.datetime(2026, 10, 1, 13), settings).amount == 0
        settings["overrides"] = {"2026-10-01": True, "2026-10-10": False}
        assert model.is_workday(dt.date(2026, 10, 1), settings)
        assert not model.is_workday(dt.date(2026, 10, 10), settings)
        settings = dict(model.DEFAULTS, overrides={}, auto_holidays=False)
        assert model.workdays(2026, 10, settings) == 22

    payload = calendar.years[2026]
    calendar.accept(("calendar", 2026, payload, None, 1234567890))
    assert (Path(temporary) / "2026.json").exists()
    restored = HolidayCalendar(temporary)
    events = queue.Queue()
    with patch("salary_motivator.holidays.urlopen", side_effect=URLError("offline")):
        restored._fetch(2026, events)
    restored.accept(events.get_nowait())
    assert restored.workday(dt.date(2026, 10, 10)) is True
    assert "已缓存" in restored.status(2026)
    # A subsequent year's notice can override the preceding December.
    future = {"year": 2027, "papers": ["https://www.gov.cn/test-notice"],
              "days": [{"date": "2026-12-31", "name": "测试元旦", "isOffDay": True}]}
    restored.accept(("calendar", 2027, validate_payload(future, 2027), None, 1234567891))
    assert restored.workday(dt.date(2026, 12, 31)) is False
    for invalid in (
        {"year": 2027, "papers": [], "days": []},
        dict(future, year=2028),
        dict(future, days=[dict(future["days"][0], isOffDay="false")]),
    ):
        try:
            validate_payload(invalid, 2027)
            raise AssertionError("Invalid holiday response was accepted")
        except (ValueError, TypeError):
            pass
    # A damaged local cache must fall back to bundled data.
    (Path(temporary) / "2026.json").write_text("broken json")
    assert HolidayCalendar(temporary).workday(dt.date(2026, 10, 10)) is True
    print("PASS: China holidays/makeup workdays, October workday count, manual precedence, "
          "disable switch, cache/reload, offline fallback, cross-year notice, invalid data rejection")
