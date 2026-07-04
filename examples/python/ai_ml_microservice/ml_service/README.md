# toy ML prediction service — functional core / imperative shell

A small but realistically-structured ML prediction API, organised so that
**purity is an architectural boundary, not a file boundary**. The dependency
arrow always points *inward*: the pure core imports nothing effectful, and the
shell imports the core.

## Layout

```
ml_service/
├── app/
│   ├── core/                 # PURE — stdlib only; imports nothing below
│   │   ├── types.py          # immutable values: Config, Model, Prediction, Result…
│   │   ├── validation.py     # bytes -> Result[ParsedRequest]      (1st half of sandwich)
│   │   ├── features.py       # (payload + db value) -> feature vector
│   │   ├── prediction.py     # (model + features) -> Prediction
│   │   └── handle.py         # featurize+predict+shape           (2nd half of sandwich)
│   ├── shell/                # IMPURE — one adapter per external system
│   │   ├── config.py         # read YAML  -> Config
│   │   ├── model_store.py    # read pickle -> Model
│   │   ├── db.py             # Postgres query -> Optional[float]  (+ in-memory fake)
│   │   └── http.py           # server: bytes in, bytes out
│   ├── model_training.py     # offline: synthetic data -> fit -> pickle
│   ├── wiring.py             # the pure/impure/pure sandwich, dependencies injected
│   └── main.py               # composition root: load config, wire, serve
├── scripts/train_model.py    # CLI: build the model artifact
├── tests/test_core.py        # core tests — note: no mocks
├── config.yaml
├── requirements.txt
└── .importlinter             # CI rule: core may not import shell
```

## How your original (OOP) layout maps here

| Your file        | Becomes                                                             |
|------------------|--------------------------------------------------------------------|
| `main.py`        | `shell/config.py` (YAML) + `shell/http.py` (server) + `app/main.py` (wiring) |
| `model.py`       | `shell/model_store.py` (load pickle) **+** `core/prediction.py` (predict) |
| `feature_eng.py` | `core/features.py` (DB call removed — value passed in as an argument) |
| `database.py`    | `shell/db.py` (returns a plain `float`, not an ORM object)          |
| `utilities.py`   | split by purity: pure helpers → `core`, effectful ones → `shell`   |

The two files that **split** (`model.py`, `utilities.py`) are the whole point:
each originally mixed a pure calculation with an effect.

## The "effect in the middle" — fetching a DB feature mid-prediction

Handled as a **pure/impure/pure sandwich** in `app/wiring.py`:

```
parse_request     (PURE)   decide validity + which applicant_id to fetch
fetch_attendance  (IMPURE) the single database read
complete          (PURE)   featurize → predict → shape response
```

The core never learns Postgres exists; the fetched value simply arrives as an
argument to `complete`.

## Enforcing the boundary

The layering is only a convention until it's mechanised. `.importlinter`
declares a `forbidden` contract so CI fails the moment any `app.core` module
imports the shell:

```
lint-imports          # passes only while the core stays pure
```

## Run it

```bash
pip install -r requirements.txt
python -m scripts.train_model      # writes artifacts/model.pkl  (optional; main auto-trains)
python -m app.main                 # serves on 127.0.0.1:8000

# elsewhere:
curl -s http://127.0.0.1:8000/
curl -s -X POST http://127.0.0.1:8000/ \
     -d '{"applicant_id": "stu-001", "hours_studied": 6, "prior_score": 0.7}'
```

`applicant_id`s `stu-001`…`stu-004` exist in the in-memory feature store; any
other id falls back to `features.default_attendance`. Switch
`database.mode` to `postgres` (and set `dsn`) to use the real driver.
