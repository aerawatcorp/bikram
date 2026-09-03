# Eval `claude-01` — bikram 2.1.4

**Target**: `aerawatcorp/bikram` @ `68fec5f`, version 2.1.4
**Environment**: CPython 3.11.15, Linux, `TZ=UTC`
**Date**: 2026-09-03
**Scope**: correctness, API surface, packaging, product positioning

Reproduce with:

```sh
python .datacables/eval/claude-01-reproduce.py
```

---

## Summary

| Metric | Value |
|---|---|
| Round-trip failures (BS → AD → BS) | **365** of 32,874 dates in the declared range |
| Data-invariant violations | **1** (BS 2087 totals 367 days) |
| Actually-correct BS range | **2001 – 2086** (declared: 2000 – 2090) |
| Existing test suite | 22 tests, **all passing** with every finding below present |
| Runtime dependencies | 0 |

The API design is the strongest of the comparable Python packages, and the
core conversion range is accurate — every Baisakh 1 from BS 2075 to 2083 matches
published Nepali New Year dates. The defects are concentrated at the range
boundaries and in the comparison/parsing/formatting layers, and they are
predominantly *silent*: wrong values returned without an exception.

That all 22 tests pass alongside four critical bugs is itself the primary
finding. The suite tests the paths that work.

---

## Critical

### C1 — BS 2087 is 367 days long, corrupting every later date

`bikram/constants.py:231`

A Bikram Samwat year tracks the solar year and is always 365 or 366 days. The
shipped table gives BS 2087 twelve months summing to **367**. Nothing validates
this, so the surplus propagates into every subsequent conversion.

```
BS 2087-01-01 → 2030-04-14   plausible
BS 2088-01-01 → 2031-04-16   WRONG — Nepali New Year is only ever Apr 13 or 14
BS 2089-01-01 → 2032-04-15   shifted
```

Two further signals that the tail of the table is estimated rather than
gazetted: BS 2087 contains six consecutive 30-day months, and years 2084–2090
all end `…30, 30, 30` — a pattern that appears nowhere in the sourced portion of
the table. Commit `2db23e4` ("Updating total month days for 2082, 2083, 2084 and
2085") shows the far years have already required correction once.

**Fix**: correct the arithmetic error, then re-derive 2084 onward from the Nepal
Gazette (राजपत्र). Add the invariant test in [Recommendations](#recommendations).

---

### C2 — All 365 days of BS 2000 convert to the wrong AD date, silently

`bikram/bikram.py:498`

The anchor pair is `AD 1944-01-01 ⟷ BS 2000-09-17`. In `convert_bs_to_ad` the
accumulation loop is:

```python
year = date_in_bs.year - 1
while year >= BS_SCALE.year:      # BS_SCALE.year == 2000
```

For any date in BS 2000 the start value is 1999, so **the loop body never
executes**. The function then simply adds the day-of-year to the anchor instead
of walking back to it.

```
samwat(2000, 9, 17).ad  →  1944-09-20   WRONG — this is the anchor, must be 1944-01-01
samwat(2000, 1,  1).ad  →  1944-01-02   WRONG — must be ~1943-04-13
samwat(2001, 1,  1).ad  →  1944-04-13   correct; first valid date in the table
```

The anchor date does not round-trip through its own converter. Because
`samwat(2000, …)` constructs successfully and `.ad` returns a plausible-looking
`datetime.date`, this is silent data corruption rather than a crash.

**The real supported floor is BS 2001, not BS 2000.**

**Fix**: handle the same-year-as-anchor case, or set the floor at BS 2001 and
raise for earlier dates.

---

### C3 — `__lt__` uses `<=` when comparing against a `date`

`bikram/bikram.py:285`

```python
def __lt__(self, other):
    if isinstance(other, date):
        return self.ad <= other      # should be <
```

Because `@total_ordering` derives `>=`, `>` and `<=` from `__lt__`, the slip
makes the entire ordering relation incoherent with equality:

```python
s = samwat(2073, 7, 28); d = date(2016, 11, 13)   # the same day
s == d   →  True
s <  d   →  True     # should be False
s >= d   →  False    # should be True
s >  d   →  False
```

Any code writing `if bs_date >= deadline` against a `date` takes the wrong branch
on the boundary day — precisely the day a deadline matters.

The existing test asserts `samwat(2073,7,27) < date(2016,11,13)`, which passes
for the wrong reason and would continue to pass after the fix. A same-day
assertion is needed.

---

### C4 — `__eq__` raises `TypeError` instead of returning `NotImplemented`

`bikram/bikram.py:280` (and `__lt__` at `:288`)

Python's data model requires rich-comparison methods to return `NotImplemented`
for unhandled types so the interpreter can fall back to identity comparison.
Raising instead breaks ordinary container operations unrelated to dates:

```python
s == None        → TypeError: Cannot compare bikram.samwat with NoneType
s in [1, 2, 3]   → TypeError
[s] == [1]       → TypeError
```

`x == None` raising is the sharpest edge — it is idiomatic Python that no caller
expects to fail, and it makes `samwat` unusable as an optional field on a
dataclass, ORM model, or serializer.

**Fix**: `return NotImplemented` in both methods. Python raises an appropriate
`TypeError` for `<` on its own, and correctly yields `False` for `==`.

---

## High

### H1 — `parse()` treats every literal in the format as a wildcard

`bikram/bikram.py:341`

`_get_pattern_from_codes` joins field patterns with `r"."` — the regex
any-character metacharacter — discarding the literal text of the format string
entirely. It then uses `pattern.match` rather than `fullmatch`.

```python
samwat.parse("2073X07Q28", "%Y-%m-%d")         → samwat(2073, 7, 28)   wrong separators accepted
samwat.parse("2073-07-28GARBAGE", "%Y-%m-%d")  → samwat(2073, 7, 28)   trailing junk ignored
samwat.from_iso("2073.07;28")                  → samwat(2073, 7, 28)   not ISO at all
samwat.parse("2073 - 07 - 28", "%Y - %m - %d") → ValueError            valid format rejected
```

Permissive where it should be strict, strict where it should be permissive. For
a library whose main job is ingesting user-entered Nepali dates, `from_iso`
accepting non-ISO input is a validation hole — callers reasonably treat it as a
validator.

**Fix**: `re.escape` the literal segments between codes; use `fullmatch`.

---

### H2 — `strftime()` corrupts output through sequential `str.replace`

`bikram/bikram.py:227`

Codes are substituted one at a time with `str.replace` across the whole string,
in match order. Shorter codes that prefix longer ones destroy them, and every
occurrence is replaced rather than the matched span.

```python
samwat(2076,1,4).strftime("%d and %dne")   → '04 and 04ne'     %dne mangled by the %d pass
samwat(2076,1,4).strftime("%Y%% literal")  → '2076%% literal'  no %% escape
```

**Fix**: single `re.sub` with a callback, so each match is replaced exactly once
in place. Add `%%` as a literal-percent escape.

---

### H3 — Month abbreviation `Ash` is ambiguous; Ashadh is unreachable

`bikram/constants.py:74`

Both Ashadh (month 3) and Ashwin (month 6) abbreviate to `Ash`.
`month_name_to_numbers` is built by looping over name lists and assigning into
one flat dict, so the later entry wins unconditionally.

```python
month_name_to_numbers['Ash']             → 6                    Ashwin
samwat.parse("2073,Ash,28", "%Y,%B,%d")  → samwat(2073, 6, 28)  Ashadh unreachable
```

**Fix**: use four-letter forms (`Asha` / `Ashw`), or drop three-letter
abbreviations for these two months and raise on ambiguity rather than guessing.

---

### H4 — `today()` reads the host timezone, not Asia/Kathmandu

`bikram/bikram.py:296`

`samwat.today()` delegates to `date.today()`, which returns the *server's* local
date. Nepal is UTC+05:45. On a UTC-configured host — the default for essentially
every container and CI runner — the Nepali date is already tomorrow from 18:15
UTC onward, so roughly a quarter of every day returns the wrong answer on a
default deployment.

```
# this container, TZ=UTC
date.today()    → 2026-09-03
samwat.today()  → 2083-05-18    correct only until 18:15 UTC
```

**Fix**: `datetime.now(timezone(timedelta(hours=5, minutes=45))).date()`. No
dependency required — Nepal has observed no DST and no offset change since 1986.

---

## Medium / Low

### M1 — Range constants are misnamed and contradict the shipped data

`bikram/constants.py:238`, `bikram/bikram.py:463`, `bikram/bikram.py:492`

`FIRST_AD_YEAR` and `LAST_AD_YEAR` hold **2000 and 2090 — Bikram Samwat years,
not AD**. They are used to validate BS input (semantically right, name badly
wrong), while the two converters carry separately hardcoded bounds that disagree
with both the names and the table.

| Bound | Declared | Actually correct | Effect |
|---|---|---|---|
| BS lower | 2000 | 2001 | BS 2000 silently wrong (C2) |
| BS upper | 2089 | 2086 | BS 2090 data shipped but unreachable; 2087+ corrupt (C1) |
| AD upper | 2033 | — | Cuts off ~4 months of otherwise-valid BS 2090 |

**Fix**: derive all bounds from the data table at import time; rename to
`FIRST_BS_YEAR` / `LAST_BS_YEAR`. Delete the unused `_FIRST_AD_DATE` /
`_LAST_BS_DATE` dicts at `bikram.py:40-41`.

---

### M2 — Type validation accepts `bool`; `replace()` swallows falsy arguments

`bikram/bikram.py:46`, `bikram/bikram.py:205`

```python
samwat(2073, True, True)           → 2073-True-True    bool is an int subclass
samwat(2073,7,28).replace(day=0)   → 2073-7-28         `day or self.day` eats the 0
```

The `x or self.x` idiom cannot distinguish "not supplied" from "supplied as
falsy", so an invalid `0` passes through as a no-op instead of raising.

**Fix**: sentinel default in `replace`; explicit `type(value) is not int` check
in `_check_int_value`.

---

### M3 — Instances are mutable despite `__slots__` and a defined `__hash__`

`bikram/bikram.py:131`

`datetime.date` is immutable, which is what makes it safe as a dict key.
`samwat` derives `__hash__` from its fields but leaves them writable, so a key
mutated in place is lost inside any dict or set holding it.

```python
y = samwat(2073,7,28); hash(y)   → 4148514807028171473
y.year = 2074       ; hash(y)    → 9055858182141804255
```

**Fix**: `__setattr__` that raises `AttributeError`, using `object.__setattr__`
internally for construction and the `_ad` cache write.

---

### L1 — `datetime.datetime` input fails with an opaque error

`bikram/bikram.py:466`

```
convert_ad_to_bs(datetime(2016,11,13,15,30))
TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'datetime.date'
```

`datetime` is a subclass of `date`, so passing one is a natural mistake and the
error should name the real problem.

**Fix**: normalize with `.date()`, or reject with a message that says so.

---

### L2 — Conversion is O(years) and recomputed on every call

`bikram/bikram.py:495`

`convert_bs_to_ad` re-sums month tuples for every year between the target and the
1944 anchor. Cost grows with distance from the anchor — it is slowest for the
dates people actually use.

```
BS 2001  →   1.3 µs/call
BS 2089  →  18.3 µs/call    ~14× spread
```

(One reference run; absolute numbers are machine-dependent and the observed
spread ranged from 14× to 24× across runs. The shape — cost proportional to
distance from the anchor — is the stable result.)

**Fix**: a module-level cumulative day-offset table plus `bisect` makes both
directions O(log n) at constant cost. ~90 entries; also enables `toordinal` /
`fromordinal` for free.

---

## API surface gaps

The package positions itself as native-`datetime`-style integration. The parts
that exist are well judged — `__slots__`, a cached `.ad`, a compiled-pattern
cache, `@total_ordering`, operator support against `date` and `timedelta`. The
gap is coverage, and one omission is disproportionately important.

**The weekday gap.** There is no `weekday()`, no `isoweekday()`, and no
`%a`/`%A` format code. Nepal's working week runs Sunday to Friday with
**Saturday as the only weekly holiday**, so nearly every real business
calculation — settlement dates, SLA windows, payroll cutoffs, working-day counts
— needs weekday awareness. Today every consumer reaches through to
`.ad.weekday()` and reimplements the Nepali week, which is exactly the spaghetti
the usage guide promises to eliminate.

| Missing | Why it matters | Priority |
|---|---|---|
| `weekday()`, `isoweekday()` | Business-day arithmetic; Saturday weekend | High |
| `isoformat()` | JSON/API serialisation. `str()` emits unpadded `2073-7-28`, which is not ISO and does not sort lexically | High |
| `__format__` | `f"{bs:%Y-%B-%d}"` raises today; must route to `strftime` | High |
| `py.typed` marker | Type hints exist but mypy/pyright ignore the package without it | High |
| `min`, `max`, `resolution` | Range introspection without reading source | Medium |
| `toordinal()`, `fromordinal()` | Free once a cumulative table exists (L2) | Medium |
| `strptime` alias | `parse()` is the odd name out; alias for discoverability | Low |
| `timetuple()`, `ctime()` | Duck-typing against stdlib consumers | Low |

---

## Packaging and repository hygiene

- **`setup.py` uses `authors=` (plural)**, which is not a setuptools keyword. It
  emits `UserWarning: Unknown distribution option: 'authors'` and the author
  metadata is *dropped from the published package entirely*. Should be `author=`.
- **No `pyproject.toml`.** Still setup.py-only with `test_suite` /
  `tests_require`, both long deprecated. Move to PEP 621 metadata.
- **Stale metadata.** Classifiers claim Python 3.6 only; no `python_requires`;
  `tox.ini` lists py27 and py35; `.travis.yml` is fully commented out; README
  badges point at `travis-ci.org` and the old `poudel/bikram` path — all dead
  links on the PyPI page, which is the first thing an evaluating developer sees.
- **CI runs on `master` pushes only** — not on pull requests, so a contributor's
  changes are never tested before merge. Coverage is computed then discarded
  (the upload step is commented out).
- **No test matrix.** A single Python 3.10 job; nothing verifies 3.9–3.13.
- **`constants.__all__` is inconsistent** — exports `month_number_dev` and
  `ENG_TO_DEV_DIGITS` but omits `month_name_abbr`,
  `month_number_month_name_abbr_map`, and the range constants callers most need.

### Worth keeping as-is

Zero runtime dependencies, the MIT relicence, `__slots__`, the `.ad`
memoisation, doctest-style docstrings, Devanagari *and* Punjabi Shahmukhi month
names (a genuinely thoughtful touch for cross-border users), and the gazette
scans committed under `.project/supporting_assets/`. These are the bones of a
good library; they need the correctness layer underneath them.

---

## Recommendations

### The cheapest high-value change

A test asserting the invariants the data must satisfy:

- every year totals 365 or 366 days;
- every month is 29–32 days;
- 366-day years never occur twice consecutively;
- BS → AD → BS round-trips for all ~33,000 dates in range;
- a fixture of known Baisakh 1 correspondences.

That single file catches C1 and C2 immediately and prevents reintroduction.

### Mark the boundary honestly

Ship `LAST_VERIFIED_BS_YEAR` alongside `LAST_BS_YEAR`, and have conversions past
it emit a warning rather than a confident wrong answer. Users running 20-year
loan amortisation need to know which side of the line they are on. State plainly
in the README which years are gazetted and which are projected.

---

## Positioning

Reading the use cases below, a pattern emerges: **almost nobody is blocked on
date conversion.** Six or seven PyPI packages already do it. Users are blocked on
the layer above it, which is unclaimed.

| Sector | Need | Blocked by |
|---|---|---|
| Banking & fintech | Fiscal year (Shrawan 1 – Ashadh end), statements, NRB returns | No weekday support → no settlement/business-day arithmetic; no fiscal-year helpers |
| Government & e-services | Tax filing, licence expiry, land records; "within 35 days of Ashadh end" | C3 — deadline comparisons wrong on the boundary day |
| HR & payroll | Salary cycles on 29–32-day BS months; leave, probation, gratuity | No month arithmetic — cannot add a BS month or get its last day |
| Education | Academic sessions, exam schedules, results | No date-range or iteration support |
| Commerce & logistics | Dashain/Tihar demand; IRD-compliant invoicing | No holiday calendar |
| Health & civil registry | Birth dates, immunisation, pension eligibility | Range starts at BS 2001 (AD 1944) — earlier births unrepresentable |

### Four moves, in order of leverage

1. **Own the data, not just the code.** Every Nepali-calendar library in every
   language retypes the same month-length table from the same gazette, and each
   carries its own transcription errors — as this one does (C1). Publish the
   table as a separately versioned JSON/CSV artifact with per-year Rajpatra
   citations, a schema, and the invariant suite that validates it. Invite the
   JavaScript, Go, PHP, Java and Dart implementations to consume it. A library
   gets adopted; *a reference dataset gets depended on*, making this repository
   the upstream of an ecosystem rather than one competitor within it.

2. **Make correctness legible.** A developer evaluating this package cannot
   currently tell it is more trustworthy than any alternative — and today it is
   not. Publish a coverage badge, an explicit verified range, the round-trip
   property test, and a documented sourcing policy. For a calendar library, a
   published verification methodology *is* the marketing, and it is the first
   thing a bank's engineer asks for.

3. **Ship the business-rules layer.** `weekday()` with Nepali day names; a
   maintained public-holiday calendar (Dashain, Tihar, the annual government
   notice); business-day arithmetic that knows Saturday is the weekend;
   fiscal-year helpers; month-end and add-months operations; iterable BS date
   ranges. Conversion is commodity — *"how many working days until Ashadh end,
   excluding the holiday notice"* is not, and nothing on PyPI answers it.

4. **Meet developers inside their stack.** Nobody adopts a date type in the
   abstract. Ship thin optional integrations behind extras: a Django
   `BikramDateField` plus form widget, a DRF serializer field, a Pydantic v2 type
   with JSON-schema output, pandas helpers. Keep the core zero-dependency — that
   property is genuinely valuable — and gate every integration behind
   `pip install bikram[django]`. The Django field alone is likely the
   highest-traffic entry point, given Django's use across Nepal's government and
   fintech sectors.

### Sequencing

**Phase 1 — Earn the trust back** (v2.2, blocking)
Fix C1, C2, C3, C4. Add the invariant + full round-trip suite. Derive range
bounds from the data table. Publish the verified range in the README.

**Phase 2 — Close the API gaps** (v2.3)
`weekday`/`isoweekday` with `%a`/`%A`; single-pass `strftime` with `%%`;
`__format__`; strict `parse` and real `from_iso` validation; `isoformat`,
`toordinal`/`fromordinal`, `min`/`max`, immutability, `py.typed`; Nepal-time
`today()`; O(1) conversion. `pyproject.toml`, 3.9–3.13 matrix, PR-triggered CI,
published coverage.

**Phase 3 — Build the moat** (v3.0)
Holiday calendar + business-day arithmetic. Fiscal-year helpers, month
arithmetic, iterable ranges. Extend range backwards toward BS 1970. Split the
month-length table into a standalone versioned dataset with citations.

**Phase 4 — Distribute** (ongoing)
Django / DRF / Pydantic extras. Offer the dataset upstream to the JS, Go, PHP and
Dart implementations. Rewrite the README around verified range and data
provenance rather than feature bullets.

### Strategic read

This package's competitors are not better than it — the API design here is the
best of the group. What none of them have, including this one today, is
*demonstrable correctness with cited provenance*. A team choosing a calendar
library for a banking product cannot verify any of the options, so they usually
vendor their own table and move on. Be the one that publishes its sources and its
proofs, and that decision gets made for you.

Phase 1 is not optional groundwork before the interesting work — **it is the
differentiator**. Everything after it compounds on top.

### Caveats on the roadmap

Two items carry real cost and should be weighed rather than assumed:

- **Extending the range back toward BS 1970** depends on source availability for
  pre-1944 gazette records, which may not be uniformly obtainable.
- **The holiday calendar requires annual maintenance** against the government
  holiday notice. That is a recurring commitment, not a one-time feature, and it
  should only be taken on if someone owns it each year.
