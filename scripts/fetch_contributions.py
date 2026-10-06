#!/usr/bin/env python3
"""Fetch a public GitHub contribution calendar — no token needed.

GitHub serves the same calendar fragment the profile page uses at
    https://github.com/users/<username>/contributions
We parse the day cells and write data/contributions.json with the raw days plus
derived stats (current streak, longest streak, best day, monthly totals).

Usage:
    python scripts/fetch_contributions.py --user SandiRidwan
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://github.com/users/{user}/contributions"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html",
}


def parse_level(td) -> int:
    """Contribution level (0-4) from data-level, or the legacy level-N class."""
    if td.get("data-level") is not None:
        try:
            return int(td["data-level"])
        except (TypeError, ValueError):
            pass
    for cls in td.get("class", []):
        if cls.startswith("level-"):
            try:
                return int(cls.split("-")[1])
            except ValueError:
                pass
    return 0


def cell_id(td) -> str:
    return td.get("id", "")


def parse_count_from_tooltip(soup, td) -> int:
    """GitHub puts the human text in a <tool-tip for="<cell id>"> sibling."""
    cid = cell_id(td)
    if cid:
        tip = soup.find("tool-tip", attrs={"for": cid})
        if tip:
            text = tip.get_text(" ", strip=True)
            if "No contributions" in text:
                return 0
            # "3 contributions on ...", "1 contribution on ..."
            for tok in text.replace(",", " ").split():
                if tok.isdigit():
                    return int(tok)
    return parse_count(td)


def parse_count(td) -> int:
    text = td.get_text(" ", strip=True)
    for tok in text.replace(",", " ").split():
        if tok.isdigit():
            return int(tok)
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="SandiRidwan")
    ap.add_argument("-o", "--output", default="data/contributions.json")
    args = ap.parse_args()

    resp = requests.get(URL.format(user=args.user), headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days: list[dict] = []
    cells = soup.select("td.ContributionCalendar-day, td[data-date]")
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        days.append({
            "date": date,
            "count": parse_count_from_tooltip(soup, td),
            "level": parse_level(td),
        })
    days.sort(key=lambda d: d["date"])

    if not days:
        raise SystemExit("No contribution cells parsed — GitHub markup may have changed")

    def d(s: str) -> dt.date:
        return dt.date.fromisoformat(s)

    # streaks
    longest = current = 0
    best = (0, "")
    prev = None
    for day in days:
        c, ds = day["count"], day["date"]
        if c > best[0]:
            best = (c, ds)
        if c > 0:
            if prev and (d(ds) - d(prev)).days == 1:
                current += 1
            else:
                current = 1
            longest = max(longest, current)
        else:
            current = 0
        prev = ds

    # current streak counting back from the most recent day
    cur_streak = 0
    for day in reversed(days):
        if day["count"] > 0:
            cur_streak += 1
        else:
            break

    # date range of the calendar fragment
    try:
        start = d(days[0]["date"])
        end = d(days[-1]["date"])
    except Exception:
        start = end = dt.date.today()

    monthly: dict[str, int] = {}
    for day in days:
        monthly[day["date"][:7]] = monthly.get(day["date"][:7], 0) + day["count"]

    total = sum(day["count"] for day in days)
    stats = {
        "total": total,
        "current_streak": cur_streak,
        "longest_streak": longest,
        "best_day": {"count": best[0], "date": best[1]},
        "start": start.isoformat(),
        "end": end.isoformat(),
        "months": dict(sorted(monthly.items())),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps({"user": args.user, "days": days, "stats": stats}, indent=2),
        encoding="utf-8",
    )
    print(f"[fetch] {len(days)} days · total={total} · "
          f"cur={cur_streak} · longest={longest} -> {args.output}")


if __name__ == "__main__":
    main()
