"""Chinese holiday data, validated locally and refreshed without blocking Tk."""
import datetime as dt
import json
from pathlib import Path
import ssl
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

SOURCES = (
    "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json",
    "https://cdn.jsdelivr.net/gh/NateScarlet/holiday-cn@master/{year}.json",
)


def validate_payload(payload, year):
    if not isinstance(payload, dict) or type(payload.get("year")) is not int or payload["year"] != year:
        raise ValueError("节假日数据年份不匹配")
    papers, days = payload.get("papers"), payload.get("days")
    if not isinstance(papers, list) or not isinstance(days, list) or len(days) > 400:
        raise ValueError("节假日数据格式无效")
    if not papers or not days:
        raise ValueError(f"{year} 年安排尚未公布或数据不完整")
    if not all(isinstance(p, str) and p.startswith("https://www.gov.cn/") for p in papers):
        raise ValueError("节假日数据缺少国务院公告依据")
    checked, seen = [], set()
    for item in days:
        day = dt.date.fromisoformat(item["date"])
        if day.year not in (year - 1, year) or type(item.get("isOffDay")) is not bool:
            raise ValueError("节假日日期或班休标记无效")
        if not isinstance(item.get("name"), str) or not 0 < len(item["name"]) <= 40 or day in seen:
            raise ValueError("节假日名称或重复日期无效")
        seen.add(day)
        checked.append({"date": day.isoformat(), "name": item["name"], "isOffDay": item["isOffDay"]})
    return {"year": year, "papers": papers, "days": checked}


class HolidayCalendar:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.years = {}
        self.dates = {}
        self.checked = {}
        self.errors = {}
        self.inflight = set()
        self.revision = 0
        bundled = Path(__file__).parent / "assets" / "holidays"
        for directory in (bundled, self.cache_dir):
            for path in sorted(directory.glob("[0-9][0-9][0-9][0-9].json")):
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    year = int(path.stem)
                    self.years[year] = validate_payload(raw, year)
                    if directory == self.cache_dir:
                        self.checked[year] = float(raw.get("_checked_at", 0))
                except (OSError, ValueError, KeyError, TypeError):
                    continue
        self._rebuild()

    def _rebuild(self):
        self.dates = {item["date"]: item for year in sorted(self.years)
                      for item in self.years[year]["days"]}
        self.revision += 1

    def workday(self, day):
        item = self.dates.get(day.isoformat())
        return None if item is None else not item["isOffDay"]

    def description(self, day):
        item = self.dates.get(day.isoformat())
        if item is None:
            return ""
        return item["name"] + (" · 放假" if item["isOffDay"] else " · 调休上班")

    def status(self, year):
        if year in self.inflight:
            return f"正在更新 {year} 年调休…"
        if year in self.years:
            if year in self.errors:
                return f"{year} 年安排已缓存 · 联网失败，稍后重试"
            stamp = self.checked.get(year)
            suffix = dt.datetime.fromtimestamp(stamp).strftime("%m-%d %H:%M 更新") if stamp else "内置离线数据"
            return f"{year} 年中国节假日已就绪 · {suffix}"
        return f"{year} 年暂无已公布数据 · 暂按单双休计算"

    def request(self, year, events, force=False):
        # The following year's notice can change the preceding December.
        for requested in (year, year + 1):
            if requested in self.inflight:
                continue
            interval = 1800 if requested in self.errors else 86400
            if not force and time.time() - self.checked.get(requested, 0) < interval:
                continue
            self.inflight.add(requested)
            threading.Thread(target=self._fetch, args=(requested, events), daemon=True).start()

    @staticmethod
    def _fetch(year, events):
        error = "暂时无法连接数据源"
        context = ssl.create_default_context(cafile=certifi.where())
        for template in SOURCES:
            try:
                request = Request(template.format(year=year), headers={"User-Agent": "SalaryMotivator/1.3.0"})
                with urlopen(request, timeout=5, context=context) as response:
                    raw = response.read(256_001)
                if len(raw) > 256_000:
                    raise ValueError("节假日数据超过限制")
                payload = validate_payload(json.loads(raw), year)
                events.put(("calendar", year, payload, None, time.time()))
                return
            except (OSError, ValueError, KeyError, TypeError, HTTPError, URLError) as exc:
                error = str(exc)
        events.put(("calendar", year, None, error, time.time()))

    def accept(self, event):
        _, year, payload, error, checked_at = event
        self.inflight.discard(year)
        self.checked[year] = checked_at
        if error:
            self.errors[year] = error
            return
        self.errors.pop(year, None)
        self.years[year] = payload
        self._rebuild()
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path = self.cache_dir / f"{year}.json"
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(dict(payload, _checked_at=checked_at), ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            # Keep the validated in-memory data even if the cache is unwritable.
            pass
