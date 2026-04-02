#!/opt/anaconda3/bin/python3
"""get_current_parasha.py

Determine this week's parasha (diaspora, Saturday reading) using Hebrew calendar
and return the matching filename from ~/clawd/knowledge/maimonides/.

Outputs:
- Prints the parasha name and the resolved markdown filename.
- Exits non-zero if it cannot map to an existing file.

Assumptions:
- Files are named like: Beshalach.md, Vayetzei.md, Ki_Tisa.md, Acharei_Mot.md, etc.
- Uses hdate library.

Usage:
  /opt/anaconda3/bin/python3 ~/clawd/tools/get_current_parasha.py
  /opt/anaconda3/bin/python3 ~/clawd/tools/get_current_parasha.py --date 2026-04-01
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from hdate.date_info import HDateInfo
from hdate.parasha import Parasha


MAIMONIDES_DIR = Path("/Users/igorsilva/clawd/knowledge/maimonides")


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _canon_filename(parasha: str) -> str:
    # hdate returns names like "Tazria-Metzora" sometimes; map to our filenames.
    # Our corpus seems to have single-parasha files; keep first part if split.
    name = parasha.strip()
    name = name.replace("-", " ")
    parts = name.split()
    # TitleCase with underscores between words
    return "_".join([p[:1].upper() + p[1:].lower() for p in parts]) + ".md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (defaults to today)")
    ap.add_argument("--israel", action="store_true", help="Use Israel schedule (default: diaspora)")
    args = ap.parse_args()

    d = _parse_date(args.date) if args.date else date.today()

    # HDateInfo returns the parasha for that specific date if it's Shabbat.
    # For weekdays, we want the *upcoming* Shabbat parasha.
    weekday = d.weekday()  # Mon=0 ... Sun=6
    # hdate's parasha lookup is keyed to Saturday/Sunday boundary in some locales;
    # empirically (diaspora), Sunday returns the upcoming Shabbat parasha.
    # So for any date, jump to the upcoming Sunday.
    days_until_sunday = (6 - weekday) % 7
    shabbat = d if days_until_sunday == 0 else (d.fromordinal(d.toordinal() + days_until_sunday))

    info = HDateInfo(shabbat, diaspora=not args.israel)
    parasha_he = info.parasha
    if not parasha_he or parasha_he == str(Parasha.NONE):
        print(f"No parasha found for Shabbat {shabbat.isoformat()}")
        return 2

    # Map Hebrew display name back to enum, then to enum.name.
    parasha_enum = None
    for p in Parasha:
        if str(p) == parasha_he:
            parasha_enum = p
            break
    if parasha_enum is None or parasha_enum == Parasha.NONE:
        print(f"Unmapped parasha: {parasha_he}")
        return 2

    parasha = parasha_enum.name  # e.g. 'TZAV', 'BESHALACH', 'ACHREI_MOT'
    filename = _canon_filename(parasha)
    path = MAIMONIDES_DIR / filename

    # Corpus spelling normalisation (e.g. SHMINI -> Shemini.md)
    if not path.exists() and parasha.upper() == "SHMINI":
        filename = "Shemini.md"
        path = MAIMONIDES_DIR / filename

    # Fallback: try exact as-is with underscores
    if not path.exists():
        alt = parasha.strip().replace(" ", "_") + ".md"
        path2 = MAIMONIDES_DIR / alt
        if path2.exists():
            filename = alt
            path = path2

    if not path.exists():
        print(f"Parasha: {parasha}")
        print(f"Expected file: {path}")
        return 3

    print(f"Parasha: {parasha}")
    print(f"File: {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
