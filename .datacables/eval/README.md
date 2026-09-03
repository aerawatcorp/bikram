# Evaluations

Independent reviews of the `bikram` package. Each evaluation is a point-in-time
assessment pinned to a specific commit, kept here so findings stay attached to
the repository rather than living only in a chat log or an issue tracker.

| Eval | Date | Target | Scope | Findings |
|---|---|---|---|---|
| [`claude-01`](claude-01-findings.md) | 2026-09-03 | `68fec5f` / v2.1.4 | Correctness, API surface, packaging, positioning | 4 critical, 4 high, 5 medium/low |

## Layout

```
.datacables/eval/
├── README.md                    this file
├── claude-01-findings.md        full write-up
└── claude-01-reproduce.py       runnable reproduction of every finding
```

## Running a reproduction script

Reproduction scripts are standalone and require only the package itself plus the
standard library. From the repository root:

```sh
python .datacables/eval/claude-01-reproduce.py
```

They print observed output against the working tree, so they double as a
regression check: once a finding is fixed, the corresponding section changes.

## Conventions

- Every finding cites `file:line` against the target commit.
- Every claim is reproduced against a real checkout; no illustrative or
  hypothetical output.
- Severity reflects blast radius and silence. A wrong answer returned without an
  error ranks above a crash, because the caller has no signal to act on.
