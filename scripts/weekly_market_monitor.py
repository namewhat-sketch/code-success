#!/usr/bin/env python3
"""Sunday market watch. Public official calendars only; no guessed events."""
import datetime as dt
import html
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
NOW = dt.datetime.now(KST)
START = (NOW + dt.timedelta(days=(7 - NOW.weekday()) % 7 or 7)).date() if NOW.weekday() != 6 else (NOW + dt.timedelta(days=1)).date()
END = START + dt.timedelta(days=6)
OUT = pathlib.Path("reports")
OUT.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "weekly-market-monitor/1.0 (GitHub Actions)", "Accept": "application/json, application/xml, text/xml, */*"}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()

def add_event(events, day, title, source, notes=""):
    if START <= day <= END:
        events.append((day, title, source, notes))

events = []
warnings = []
# Federal Reserve: official machine-readable FOMC calendar (meeting dates).
try:
    data = fetch("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm").decode("utf-8", "replace")
    # FOMC page is human-readable; do not infer dates from unstructured text.
    warnings.append("FOMC: 공식 일정 페이지를 연결했으나 자동 날짜 파싱은 지원하지 않음. 원문 확인 필요")
except Exception as exc:
    warnings.append(f"FOMC 공식 일정 조회 실패: {type(exc).__name__}")
# BLS official calendar ICS: parse DTSTART and SUMMARY (supports folded lines).
try:
    raw = fetch("https://www.bls.gov/schedule/news_release/bls.ics").decode("utf-8-sig", "replace")
    raw = re.sub(r"\r?\n[ \t]", "", raw)
    for block in raw.split("BEGIN:VEVENT")[1:]:
        date_match = re.search(r"(?m)^DTSTART(?:;[^:]*)?:(\d{8})", block)
        summary_match = re.search(r"(?m)^SUMMARY:(.+)$", block)
        if date_match and summary_match:
            day = dt.datetime.strptime(date_match.group(1), "%Y%m%d").date()
            title = summary_match.group(1).strip().replace("\\,", ",")
            add_event(events, day, "미국 BLS: " + title, "https://www.bls.gov/schedule/news_release/", "공식 일정. 발표 시각은 원문 확인")
except Exception as exc:
    warnings.append(f"BLS 일정 수집 실패: {type(exc).__name__}")
# Additional manually verified events: optional tracked JSON; date and source mandatory.
manual = pathlib.Path("config/verified_events.json")
try:
    for item in json.loads(manual.read_text(encoding="utf-8")):
        day = dt.date.fromisoformat(item["date"])
        source = item["source"]
        if not source.startswith("https://"):
            raise ValueError("source must be https URL")
        add_event(events, day, item["title"], source, item.get("notes", ""))
except Exception as exc:
    warnings.append(f"검증 이벤트 파일 오류: {type(exc).__name__}: {exc}")

events = sorted(set(events), key=lambda e: (e[0], e[1]))
lines = [
    f"# 주간 증시 일정: {START.isoformat()} ~ {END.isoformat()} (KST)",
    "",
    f"> 생성 시각: {NOW:%Y-%m-%d %H:%M} KST · 공식 출처 및 수동 검증 항목만 수록",
    "",
    "## 확인된 이벤트",
    "",
    "| 날짜(KST 기준 확인 필요) | 이벤트 | 출처 / 참고 |",
    "|---|---|---|",
]
for day, title, source, notes in events:
    lines.append(f"| {day} | {title.replace('|', '/')} | [원문]({source}) {notes.replace('|', '/')} |")
if not events:
    lines.append("| - | 자동으로 검증된 이벤트 없음 | 아래 공식 캘린더 확인 필요 |")
lines += [
    "",
    "## 반드시 추가 확인할 주요 일정",
    "",
    "- [미국 연준 FOMC](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm): 회의·의사록·연설",
    "- [미국 BLS](https://www.bls.gov/schedule/news_release/): CPI·PPI·고용",
    "- [미국 BEA](https://www.bea.gov/news/schedule): PCE·GDP",
    "- [한국은행](https://www.bok.or.kr): 금융통화위원회·경제지표",
    "- [DART](https://dart.fss.or.kr): 국내 실적·보호예수 관련 공시",
    "- [한국예탁결제원 SEIBro](https://seibro.or.kr): 의무보유등록 해제",
    "- [SEC EDGAR](https://www.sec.gov/edgar/search/): 미국 기업 실적·공시",
    "- [Nasdaq Earnings Calendar](https://www.nasdaq.com/market-activity/earnings): 미국 실적 발표",
    "",
    "## 수집 상태 및 한계",
    "",
]
lines += [f"- {w}" for w in warnings]
lines += [
    "- 기업 실적·금통위·FOMC·락업은 자동 수집을 검증하지 못했으므로 임의로 일정을 생성하지 않습니다.",
    "- BLS ICS의 날짜는 원본 시간대에 따라 한국 날짜와 다를 수 있습니다. 반드시 발표 시각을 확인하세요.",
    "- 이 보고서는 투자 권유가 아니며 이벤트 누락 가능성이 있습니다.",
    "",
]
content = "\n".join(lines)
(OUT / "latest.md").write_text(content, encoding="utf-8")
(OUT / f"{START.isoformat()}.md").write_text(content, encoding="utf-8")
print(content)
