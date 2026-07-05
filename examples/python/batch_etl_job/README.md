# Batch ETL Job — Functional Programming Demo

A toy ETL (Extract, Transform, Load) application demonstrating how a
typical batch data pipeline can be built using **functional programming**
principles in Python. The app fetches data from public REST APIs,
transforms it with pure, side-effect-free functions, and writes the results
to an in-memory SQLite database.

## Design

The code follows a **functional core, imperative shell** architecture:

```
┌──────────────────────────────────────────┐
│  run.py          (shell: CLI, print)     │
│  json_fetcher.py (shell: HTTP, JSON)     │
│  sqlite_saver.py (shell: SQLite I/O)     │
├──────────────────────────────────────────┤
│  orchestrate.py    (core: routing)       │
│  user_transformer.py (core: Polars)      │
│  post_transformer.py (core: pure Python) │
│  domain_types.py     (core: data types)  │
└──────────────────────────────────────────┘
```

- **Core** modules contain only pure functions — no I/O, no mutation, no
  randomness, no network. Every function returns a value and can be tested
  with plain inputs and expected outputs.
- **Shell** modules perform effects (HTTP, CLI, database) at the edges and
  hand clean, typed data to the core. They are marked with an `impure_`
  prefix by convention.

## How it works

1. **Fetch** — downloads JSON from a public API (both jobs use
   [JSONPlaceholder](https://jsonplaceholder.typicode.com/))
2. **Parse** — validates raw JSON into immutable `frozen dataclass`
   records at the shell boundary
3. **Transform** — pure functions aggregate the records (one pipeline
   uses Polars, the other uses only the Python standard library)
4. **Save** — writes aggregate results to an in-memory SQLite table
5. **Verify** — reads back rows from SQLite to confirm the data landed

Both pipelines return a `Result[T]` type throughout — errors are data, not
thrown exceptions. The flow reads like a railway: each step either
produces a value or short-circuits with a descriptive error.

## Job types

| Command            | API                        | Transformer | SQLite table        |
|--------------------|----------------------------|-------------|---------------------|
| `python run.py users` | `/users`                   | Polars      | `user_stats_by_city` |
| `python run.py posts` | `/posts`                   | pure Python | `post_stats_by_user` |

### Users

Groups user records by city and counts how many users live in each city.

### Posts

Groups post records by user ID and computes post count plus average body
length per user.

## Project structure

```
batch_etl_job/
  run.py               Shell: CLI entry point, orchestrates the ETL pipeline
  domain_types.py       Core: frozen dataclasses, Result/Either type, JobType
  orchestrate.py        Core: maps JobType → JobConfig (API URL, table name)
  json_fetcher.py       Shell: HTTP requests, JSON parsing, record validation
  user_transformer.py   Core: Polars pipeline (users → city aggregates)
  post_transformer.py   Core: pure-Python pipeline (posts → per-user stats)
  sqlite_saver.py       Shell: in-memory SQLite table creation and upserts
  FUNC_PROG_GUIDE.md    Reference: the functional programming rules used here
  AGENTS.md             Instructions for AI agents working on this project
  requirements.txt      Python dependencies
```

## Requirements

- Python 3.12+
- polars >= 1.0.0 (for the users pipeline)
- mypy >= 1.0.0 (for type checking)

```bash
pip install -r requirements.txt
```

## Running

```bash
# Users
python run.py users

# Posts
python run.py posts
```

## Type checking

```bash
mypy --strict *.py
```

A clean run produces zero errors.

## FP highlights

- **Immutable data**: all domain types use `@dataclass(frozen=True)` and methods never mutate their inputs.
- **No null**: optional/fallible values use `Result[T]` (a hand-rolled Either type).
- **No exceptions for control flow**: errors are `Result` values; exceptions are reserved for unrecoverable programmer errors.
- **Functional fold over imperative loops**: batch parsing uses `functools.reduce` with copy-on-write tuple accumulation (no `list.append()`).
- **Declarative pipelines**: core transformations compose small, single-purpose functions rather than writing large procedures.
- **Explicit dependencies**: the database connection, clock, and other effectful resources are passed as arguments, never accessed from globals.
- **Separate data from behaviour**: data types hold values; behaviour lives in free functions.
