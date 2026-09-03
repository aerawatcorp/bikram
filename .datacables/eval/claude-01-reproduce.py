#!/usr/bin/env python
"""
Reproduction script for eval `claude-01` (see claude-01-findings.md).

Runs every finding against the working tree and prints the observed behaviour.
Requires only the `bikram` package and the standard library.

    python .datacables/eval/claude-01-reproduce.py

Exits 1 if any finding still reproduces, 0 once they are all fixed, so this
doubles as a regression check.
"""

import os
import sys
import time
from datetime import date, datetime, timedelta

# Running this file directly puts its own directory on sys.path, not the repo
# root, so make the checkout importable regardless of how it was invoked.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from bikram import samwat, convert_ad_to_bs, convert_bs_to_ad  # noqa: E402
from bikram.constants import BS_YEAR_TO_MONTHS, month_name_to_numbers

reproduced = []


def section(tag, title):
    print(f"\n{'=' * 72}\n{tag} — {title}\n{'=' * 72}")


def check(tag, condition, note):
    """Record whether a finding still reproduces."""
    status = "REPRODUCES" if condition else "fixed"
    if condition:
        reproduced.append(tag)
    print(f"  [{status}] {note}")


# --------------------------------------------------------------------------
section("C1", "BS 2087 is 367 days long")

lengths = {y: sum(v[1:]) for y, v in BS_YEAR_TO_MONTHS.items()}
bad_years = {y: n for y, n in lengths.items() if n not in (365, 366)}
print("  A Bikram Samwat year tracks the solar year: always 365 or 366 days.")
print(f"  Years violating that invariant: {bad_years or 'none'}")

bad_months = [
    (y, i, d)
    for y, v in BS_YEAR_TO_MONTHS.items()
    for i, d in enumerate(v[1:], 1)
    if not 29 <= d <= 32
]
print(f"  Months outside 29-32 days: {bad_months or 'none'}")
print("\n  Downstream effect (Nepali New Year is only ever Apr 13 or 14):")
for y in (2087, 2088, 2089):
    try:
        print(f"    BS {y}-01-01 -> {samwat(y, 1, 1).ad}")
    except ValueError as err:
        print(f"    BS {y}-01-01 -> ValueError: {err}")
check("C1", bool(bad_years), f"impossible year lengths present: {bad_years}")


# --------------------------------------------------------------------------
section("C2", "All of BS 2000 converts wrong, silently")

print("  Anchor pair: AD 1944-01-01 <-> BS 2000-09-17")
print(f"    samwat(2000, 9, 17).ad = {samwat(2000, 9, 17).ad}   (must be 1944-01-01)")
print(f"    samwat(2000, 1,  1).ad = {samwat(2000, 1, 1).ad}   (must be ~1943-04-13)")
print(f"    samwat(2001, 1,  1).ad = {samwat(2001, 1, 1).ad}   (correct)")

mismatches = 0
total = 0
for y, months in BS_YEAR_TO_MONTHS.items():
    for m in range(1, 13):
        for d in range(1, months[m] + 1):
            try:
                bs = samwat(y, m, d)
                if convert_ad_to_bs(convert_bs_to_ad(bs)).as_tuple() != (y, m, d):
                    mismatches += 1
            except ValueError:
                continue
            total += 1
print(f"\n  Full round-trip sweep: {mismatches} of {total} dates fail BS -> AD -> BS")
check("C2", samwat(2000, 9, 17).ad != date(1944, 1, 1),
      "the anchor date does not round-trip through its own converter")


# --------------------------------------------------------------------------
section("C3", "__lt__ uses <= when comparing against a date")

s, d = samwat(2073, 7, 28), date(2016, 11, 13)
print("  s = samwat(2073, 7, 28); d = date(2016, 11, 13)   # the same day")
print(f"    s == d  -> {s == d}")
print(f"    s <  d  -> {s < d}      (should be False)")
print(f"    s >= d  -> {s >= d}      (should be True)")
print(f"    s >  d  -> {s > d}")
check("C3", (s == d) and (s < d), "equality and ordering disagree on the same day")


# --------------------------------------------------------------------------
section("C4", "__eq__ raises instead of returning NotImplemented")

raised = False
for expr, fn in [
    ("s == None", lambda: s == None),          # noqa: E711 - the point of the test
    ("s in [1, 2, 3]", lambda: s in [1, 2, 3]),
    ("[s] == [1]", lambda: [s] == [1]),
]:
    try:
        print(f"    {expr:<18} -> {fn()}")
    except TypeError as err:
        raised = True
        print(f"    {expr:<18} -> TypeError: {err}")
check("C4", raised,
      "comparison against unrelated types raises rather than returning False")


# --------------------------------------------------------------------------
section("H1", "parse() treats format literals as wildcards")

cases = [
    ("2073X07Q28", "%Y-%m-%d", "wrong separators should be rejected"),
    ("2073-07-28GARBAGE", "%Y-%m-%d", "trailing junk should be rejected"),
    ("2073 - 07 - 28", "%Y - %m - %d", "valid multi-char separators should parse"),
]
loose = False
for datestr, fmt, note in cases:
    try:
        got = samwat.parse(datestr, fmt)
        print(f"    parse({datestr!r}, {fmt!r})\n      -> {got}    ({note})")
        if "rejected" in note:
            loose = True
    except ValueError as err:
        print(f"    parse({datestr!r}, {fmt!r})\n      -> ValueError: {err}    ({note})")
try:
    got_iso = samwat.from_iso("2073.07;28")
    print(f"    from_iso('2073.07;28')  -> {got_iso}    (not ISO at all)")
    loose = True
except ValueError:
    print("    from_iso('2073.07;28')  -> ValueError")
check("H1", loose, "malformed input is silently accepted")


# --------------------------------------------------------------------------
section("H2", "strftime() corrupts output via sequential str.replace")

f = samwat(2076, 1, 4)
collide = f.strftime("%d and %dne")
print(f"    strftime('%d and %dne')   -> {collide!r}    (expected '04 and ०४')")
try:
    pct = f.strftime("%Y%% literal")
    print(f"    strftime('%Y%% literal')  -> {pct!r}    (expected '2076% literal')")
except ValueError as err:
    pct = None
    print(f"    strftime('%Y%% literal')  -> ValueError: {err}")
check("H2", collide == "04 and 04ne",
      "a shorter code corrupts a longer one sharing its prefix")


# --------------------------------------------------------------------------
section("H3", "Month abbreviation 'Ash' is ambiguous")

print("  Ashadh (month 3) and Ashwin (month 6) share the abbreviation 'Ash'.")
print(f"    month_name_to_numbers['Ash']            -> {month_name_to_numbers['Ash']}")
_ash = samwat.parse("2073,Ash,28", "%Y,%B,%d")
print(f"    parse('2073,Ash,28', '%Y,%B,%d')        -> {_ash}")
check("H3", month_name_to_numbers["Ash"] == 6,
      "Ashwin silently wins; Ashadh's abbreviation is unreachable")


# --------------------------------------------------------------------------
section("H4", "today() reads the host timezone, not Asia/Kathmandu")

import bikram.bikram as _bikram_mod  # noqa: E402
from datetime import timezone  # noqa: E402

NPT = timezone(timedelta(hours=5, minutes=45))

# Pin a UTC instant at which Nepal has already rolled over to the next day, so
# this check is deterministic rather than dependent on when the script runs.
INSTANT = datetime(2026, 9, 3, 18, 30, tzinfo=timezone.utc)
host_date = INSTANT.astimezone(timezone.utc).date()
nepal_date = INSTANT.astimezone(NPT).date()


class _FrozenDate(date):
    """Stands in for the module's clock so today() is reproducible."""

    @classmethod
    def today(cls):
        return host_date


print(f"    instant             : {INSTANT.isoformat()}")
print(f"    date on a UTC host  : {host_date}")
print(f"    date in Nepal       : {nepal_date}  (UTC+05:45)")

_orig_date = _bikram_mod.date
_bikram_mod.date = _FrozenDate
try:
    got = samwat.today().ad
finally:
    _bikram_mod.date = _orig_date

print(f"    samwat.today().ad   : {got}  <- follows the host, not Nepal")
check("H4", got != nepal_date,
      "today() applies no UTC+05:45 offset; wrong from 18:15 UTC onward")


# --------------------------------------------------------------------------
section("M1", "Range constants are misnamed and contradict the data")

from bikram.constants import FIRST_AD_YEAR, LAST_AD_YEAR  # noqa: E402

print(f"    FIRST_AD_YEAR = {FIRST_AD_YEAR}, LAST_AD_YEAR = {LAST_AD_YEAR}")
print("    ...but these are Bikram Samwat years, not AD years.")
try:
    convert_bs_to_ad(samwat(2090, 1, 1))
    print("    samwat(2090, 1, 1).ad -> reachable")
    unreachable = False
except ValueError as err:
    unreachable = True
    print(f"    samwat(2090, 1, 1).ad -> ValueError: {err}"
          "   (data ships but is unreachable)")
check("M1", unreachable or FIRST_AD_YEAR == 2000,
      "declared bounds disagree with the shipped table")


# --------------------------------------------------------------------------
section("M2", "bool accepted as int; replace() swallows falsy arguments")

try:
    b = samwat(2073, True, True)
    print(f"    samwat(2073, True, True)          -> {b}")
    bool_ok = True
except TypeError as err:
    bool_ok = False
    print(f"    samwat(2073, True, True)          -> TypeError: {err}")
r = samwat(2073, 7, 28).replace(day=0)
print(f"    samwat(2073,7,28).replace(day=0)  -> {r}   (day=0 is invalid, not a no-op)")
check("M2", bool_ok or r.day == 28, "invalid values pass validation silently")


# --------------------------------------------------------------------------
section("M3", "Instances are mutable despite __slots__ and __hash__")

y = samwat(2073, 7, 28)
h1 = hash(y)
try:
    y.year = 2074
    mutable = True
    print(f"    hash before y.year = 2074 : {h1}")
    print(f"    hash after                : {hash(y)}   (key lost in any dict/set)")
except AttributeError as err:
    mutable = False
    print(f"    y.year = 2074 -> AttributeError: {err}")
check("M3", mutable, "field assignment changes the hash of a live object")


# --------------------------------------------------------------------------
section("L1", "datetime.datetime input fails opaquely")

try:
    got = convert_ad_to_bs(datetime(2016, 11, 13, 15, 30))
    print(f"    convert_ad_to_bs(datetime(...)) -> {got}")
    opaque = False
except TypeError as err:
    opaque = "unsupported operand" in str(err)
    print(f"    convert_ad_to_bs(datetime(...)) -> TypeError: {err}")
check("L1", opaque, "error message does not name the real problem")


# --------------------------------------------------------------------------
section("L2", "Conversion is O(years), recomputed per call")

N = 20000
near, far = samwat(2001, 1, 1), samwat(2089, 12, 29)
t0 = time.perf_counter()
for _ in range(N):
    convert_bs_to_ad(far)
t1 = time.perf_counter()
for _ in range(N):
    convert_bs_to_ad(near)
t2 = time.perf_counter()
far_us, near_us = (t1 - t0) / N * 1e6, (t2 - t1) / N * 1e6
spread = far_us / near_us
print(f"    BS 2001 : {near_us:6.1f} us/call")
print(f"    BS 2089 : {far_us:6.1f} us/call   ({spread:.1f}x spread)")
check("L2", spread > 3, "cost scales with distance from the 1944 anchor")


# --------------------------------------------------------------------------
section("API", "Missing datetime.date surface")

want = [
    "weekday", "isoweekday", "isoformat", "toordinal", "fromordinal",
    "timetuple", "ctime", "min", "max", "resolution", "isocalendar",
]
missing = [w for w in want if not hasattr(samwat, w)]
print(f"    missing attributes: {missing}")
try:
    print(f"    f-string format   : {format(samwat(2076, 1, 4), '%Y-%B-%d')!r}")
    fmt_ok = True
except TypeError as err:
    fmt_ok = False
    print(f"    f-string format   : TypeError: {err}")
check("API", bool(missing) or not fmt_ok,
      f"{len(missing)} stdlib members absent; __format__ not wired")


# --------------------------------------------------------------------------
print(f"\n{'=' * 72}")
if reproduced:
    print(f"{len(reproduced)} finding(s) still reproduce: {', '.join(reproduced)}")
    sys.exit(1)
print("No findings reproduce against this working tree.")
sys.exit(0)
