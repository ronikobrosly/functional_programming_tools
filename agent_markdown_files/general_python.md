# Python — Functional & Strict Programming Style

This file governs how you write and modify code in this repository. These rules are
**not stylistic preferences**; treat them as constraints. 

## Operating principles

When a requested change can be implemented functionally, implement it functionally —
do not ask permission first. When a requested change *appears* to require violating
these rules:

1. First, restructure so the violation disappears (this is almost always possible).
2. If it cannot be removed, **isolate it at the imperative shell** (see below), never
   in the functional core.
3. If you must write impure or mutating code, mark it with a comment explaining why the
   functional version was not possible. Silent violations are the only forbidden move.

Never weaken these rules just to finish faster. Prefer correct-and-stricter over
quick-and-looser (with the exception of recursion, which we want to avoid).

## Specific principles

### 1. Architecture: functional core, imperative shell

- The **core** holds all business logic and is 100% pure: no I/O, no mutation observable
  outside a function, no time, no randomness, no network, no environment access.
- The **shell** is a thin outer layer that performs effects (reads input, writes output,
  calls services) and hands plain data to the core. Keep it as small as possible.
- Data flows: shell gathers inputs → core computes a result (pure) → shell performs the
  effects the result describes. The core *decides*; the shell *acts*.
- A reader should be able to test the entire core with no mocks, fakes, or setup —
  only plain inputs and asserted outputs. If a test for core logic needs a mock, the
  boundary is in the wrong place.

### 2. Purity

- Every function in the core is **pure**: same inputs always produce the same output,
  and it has no observable side effects.
- A core function never reads or writes mutable global/module state, the clock, the
  random source, the filesystem, the network, the environment, or stdout/stderr.
- A function that returns nothing (`void`/unit) in the core is a red flag — it can only
  be doing a side effect. Core functions return values.
- **Referential transparency:** any call must be replaceable by its result without
  changing program behavior.

### 3. Immutability

- Never mutate a value after creation. Produce a new value instead.
- No in-place updates to arrays, maps, sets, records, or objects passed as arguments.
  A function must not modify its inputs.
- Prefer your language's immutable/persistent data structures or immutable bindings.
  Where the language only offers mutable structures, treat them as immutable by
  convention: copy-on-write, never edit in place.
- No reassignment of bindings for control flow. Bind once; derive new bindings.

### 4. Data modeling

- Model the domain with **algebraic data types** (records/products for "and", tagged
  unions/sum types for "or"). Use your language's closest equivalent.
- **Make illegal states unrepresentable.** If two fields can't both be set, don't model
  them as two optional fields — model the valid combinations as a sum type.
- **Parse, don't validate.** Validate untrusted input once at the shell boundary and
  convert it into a precise type. The core then receives already-valid data and never
  re-checks it.
- **No null / nil / undefined** as a stand-in for "maybe". Use an Option/Maybe type.
- Keep data and behavior separate. Data is plain and inert; transformations are
  free functions. Avoid objects that bundle mutable state with methods that mutate it.

### 5. Functions and composition

- Functions are first-class values: pass them, return them, compose them.
- Build behavior by **composing small, single-purpose functions** into pipelines rather
  than writing large procedures.
- Prefer composition over inheritance. Do not reach for class hierarchies to share
  behavior; share functions.
- Take **all dependencies as explicit parameters.** No hidden singletons, ambient
  context, service locators, or global config reads inside the core. If a function needs
  the clock, a logger, or an ID generator, it receives it as an argument.
- Keep functions **total**: defined for every input of their declared type. Do not write
  partial functions that throw on some inputs (e.g. `head` on an empty list). Either
  narrow the input type (e.g. a non-empty type) or return an Option.

### 6. Control flow

- Prefer **expressions over statements**: everything evaluates to a value, including
  conditionals.
- Replace imperative loops that accumulate into a mutable variable with `map` / `filter`
  / `reduce` / `fold` or equivalent higher-order operations.
- Generally, try to avoid recursion.
- Pattern-match **exhaustively** on sum types. Do not use a wildcard/`default` case to
  swallow unhandled variants — let the absence of a case be a compile error or explicit
  failure, so adding a new variant forces you to handle it everywhere.

### 7. Error handling

- **No exceptions for control flow.** Expected failures (not found, invalid input,
  conflict) are return values, not thrown.
- Represent fallible operations with a **Result/Either type** (success or typed error).
  Represent absence with **Option/Maybe**.
- Propagate and combine errors through the type, not by throwing across layers.
- Reserve thrown exceptions / panics for truly unrecoverable programmer errors
  (broken invariants), and only at the shell. The core does not throw for ordinary
  failure cases.
- Make error types meaningful (a sum type of failure cases), not a single opaque string.

### 8. Effects

- Effects (I/O, time, randomness, persistence, network) live in the shell and are
  performed at the edges of the program.
- Where the language supports it, represent effects as **descriptions/values** that the
  shell executes, or at minimum **inject effectful functions** as parameters so the core
  stays pure and testable.
- Time, randomness, and unique IDs are inputs, never grabbed implicitly inside logic.
  Pass `now`, the random value, or the generated ID in.
- Sequencing of effects belongs to the shell. The core may return a *plan* of effects;
  it does not run them.

### 9. Forbidden patterns (quick reference)

- Mutating an argument.
- Reading/writing global mutable state.
- `null` for optional values.
- Throwing for expected failures.
- Imperative accumulation loops in the core.
- Wildcard pattern cases that hide unhandled variants.
- Hidden dependencies (singletons, globals, ambient clock/RNG) inside core functions.
- Classes that pair mutable state with mutating methods.
- Void-returning functions in the core.

### 10. Permitted exceptions (escape hatches)

These are the *only* allowed deviations, and each requires a justification comment:

- **Encapsulated local mutation:** a function may use a local mutable variable for
  performance *if and only if* that mutation never escapes the function and the function
  remains pure and referentially transparent from the outside. Default to declarative;
  reach for this only when measured performance demands it.
- **Shell-level effects:** the imperative shell performs real effects by definition.
  This is expected, not an exception — but keep the shell thin.
- **Foreign/interop boundaries:** when calling a mutable or exception-throwing library,
  wrap it at the shell and convert immediately to immutable data and Result types so the
  impurity does not leak inward.

If a deviation does not fit one of these three, it is not allowed — restructure instead.

### 11. Self-review before finalizing any code

Answer these before considering a change complete:

- Is every core function pure and total? Could I replace each call with its result?
- Does any function mutate its input or any shared state? (Must be no.)
- Are all dependencies — including clock, randomness, IDs, I/O — passed in explicitly?
- Are optional values Option types and fallible operations Result types, with no `null`
  and no exceptions for expected failures?
- Is every sum type matched exhaustively, with no variant-swallowing wildcard?
- Could the core be tested with plain inputs and outputs and zero mocks?
- Is every deviation from these rules isolated at the shell and justified in a comment?

If any answer is unsatisfactory, revise before returning the code.


## Specific examples


### 0. Avoid recursion

For example, if we're trying to make a function to sum all numbers up to `n`, but only among the numbers that are divisible by 3 or 5, avoid the following:

```python
from collections.abc import Sequence, Callable
def until(
    limit: int,
    filter_func: Callable[[int], bool],
    v: int
) -> list[int]:
    if v == limit:
        return []
    elif filter_func(v):
        return [v] + until(limit, filter_func, v + 1)
    else:
        return until(limit, filter_func, v + 1)

def mult_3_5(x: int) -> bool:
    return x % 3 == 0 or x % 5 == 0

def sum_functional(limit: int = 10) -> int:
    return sumr(until(limit, mult_3_5, 0))
```

...and instead use the simpler (and mostly functional):

```python
def sum_divisible_by_3_or_5(n):
    return sum(x for x in range(1, n + 1) if x % 3 == 0 or x % 5 == 0)
```


### 1. First-Class & Higher-Order Functions

- Treat functions as values: assign them to variables, pass them as arguments, return them from other functions.
- Use `functools.partial` to create partially-applied functions when appropriate.
- Prefer higher-order abstractions over manual loops.

```python
from functools import partial

def multiply(a: int, b: int) -> int:
    return a * b

double = partial(multiply, 2)
# double(5) -> 10
```

### 2. Pure Functions

- A function must always return the same output for the same input.
- A function must produce no side effects (no mutation of external state, no I/O).
- Keep the majority of your codebase pure; push I/O and side effects to the edges.

```python
# Pure
def add(a: int, b: int) -> int:
    return a + b

# Impure — isolate this at the boundary
def read_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)
```

### 3. Built-in Functional Methods: `map`, `filter`, `reduce`

- Prefer `map`, `filter`, and `functools.reduce` over explicit `for` loops for data transformation pipelines.
- Use list/dict/set comprehensions when they improve readability, but prefer the functional forms for clear data-flow pipelines.
- Chain operations from left to right so the reader can follow the transformation step by step.

```python
from functools import reduce

nums = [1, 2, 3, 4, 5, 6]
result = reduce(
    lambda acc, x: acc + x,
    map(lambda x: x * 2, filter(lambda x: x % 2 == 0, nums)),
    0,
)
# Equivalently readable with comprehensions:
result = sum(x * 2 for x in nums if x % 2 == 0)
```

### 4. Immutability & Copy-on-Write

- Never mutate a data structure in place; always return a new copy.
- Use `tuple` instead of `list` wherever the collection should not change.
- Use `frozenset` instead of `set` for constant membership.
- Prefer `dataclasses(frozen=True)` or `NamedTuple` for value objects.
- When a "mutation" is needed, create a copy with the change applied (e.g., `dataclasses.replace`).

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Config:
    host: str
    port: int

old = Config(host="0.0.0.0", port=8080)
new = replace(old, port=9090)
```

### 5. Strictness in Typing

- Annotate every function signature with complete type hints.
- Annotate all public module-level variables and class attributes.
- Enable `mypy` with `--strict` and aim for zero errors.
- Use `TypeAlias`, `Literal`, `Final`, `Protocol`, and `TypedDict` where appropriate.
- Prefer sum types via `Union` or `|` over implicit `None` returns.

```python
from typing import Protocol, Final

MAX_RETRIES: Final = 3

class Runner(Protocol):
    def run(self, cmd: str) -> int: ...

def execute(impl: Runner, commands: list[str]) -> list[int]:
    return [impl.run(c) for c in commands]
```

### 6. Anonymous Functions (`lambda`)

- Use `lambda` for short, single-expression callbacks passed to `map`, `filter`, `sorted(key=...)`, etc.
- If the logic spans multiple lines, extract it into a named function.
- Keep lambdas expression-only — no statements, no assignments.

### 7. Separate Data from Calculations from Actions

- **Data** — plain immutable structures (`tuple`, `frozenset`, `NamedTuple`, frozen `dataclass`). No behaviour.
- **Calculations** — pure functions that transform data into new data.
- **Actions** — impure functions that perform I/O, mutate external state, or depend on the current time/randomness.
- Organise modules so that data, calculations, and actions live in distinct layers. Calculations never import actions.

```
project/
  data.py        # type definitions, constants
  calculations.py # pure business logic
  actions.py      # I/O, DB, HTTP
```

### 8. Minimizing Side Effects

- A function should do *one thing* only. If it reads a file and also parses it, split into two functions: one that reads (action), one that parses (calculation).
- Never mix I/O into a pure calculation function. Calculations must accept their dependencies as arguments rather than reaching out to the world.
- Use dependency injection: impure functions receive pure functions as arguments, not the other way around.
- Avoid logging, metrics, or telemetry inside pure functions — lift those concerns into the calling action layer.

```python
# Impure — mixed concerns
def load_and_sum(path: str) -> int:
    with open(path) as f:
        return sum(int(line) for line in f)

# Pure calculation
def parse_and_sum(lines: tuple[str, ...]) -> int:
    return sum(int(line) for line in lines)

# Impure action (thin boundary)
def read_lines(path: str) -> tuple[str, ...]:
    with open(path) as f:
        return tuple(line.strip() for line in f)
```

### 9. Small, Composable Functions

- Each function should fit on screen — aim for 5–15 lines. If a function exceeds ~20 lines, extract helper functions.
- A 50-line method should be refactored into three or four smaller functions that compose together.
- Name extracted functions clearly so the top-level function reads like a sequence of steps at a single level of abstraction.
- Each extracted function must be independently testable and reusable.

```python
# Before: one large function
def process_orders(orders: tuple[Order, ...]) -> Report:
    valid: list[Order] = []
    for o in orders:
        if o.amount > 0:
            valid.append(o)
    totals: dict[str, float] = {}
    for o in valid:
        totals[o.category] = totals.get(o.category, 0.0) + o.amount
    lines: list[str] = []
    for cat, total in sorted(totals.items()):
        lines.append(f"{cat}: ${total:.2f}")
    return Report(title="Sales", lines=tuple(lines))

# After: small, composable functions
def filter_valid(orders: tuple[Order, ...]) -> tuple[Order, ...]:
    return tuple(o for o in orders if o.amount > 0)

def totals_by_category(orders: tuple[Order, ...]) -> dict[str, float]:
    return reduce(
        lambda acc, o: {**acc, o.category: acc.get(o.category, 0.0) + o.amount},
        orders,
        {},
    )

def format_report_lines(totals: dict[str, float]) -> tuple[str, ...]:
    return tuple(f"{cat}: ${total:.2f}" for cat, total in sorted(totals.items()))

def process_orders(orders: tuple[Order, ...]) -> Report:
    valid = filter_valid(orders)
    totals = totals_by_category(valid)
    lines = format_report_lines(totals)
    return Report(title="Sales", lines=lines)
```

### 10. Strict Copy-on-Write Paradigm

- Every "mutating" function must follow this pattern: **(1)** take an immutable input, **(2)** create a shallow or deep copy, **(3)** apply the change to the copy, **(4)** return the copy.
- Never call `list.append()`, `dict.update()`, `set.add()`, or `self.attr = value` on a passed-in argument. Always work on a fresh copy.
- Use `dataclasses.replace()`, `copy()`, dict unpacking `{**d, key: val}`, and tuple/list comprehensions to produce new values.
- The caller retains the original value unchanged; the callee has no side effects.

```python
from copy import deepcopy

def add_item(cart: tuple[CartItem, ...], item: CartItem) -> tuple[CartItem, ...]:
    """Return a new cart with item appended. Original cart is unchanged."""
    return (*cart, item)

def set_config(config: Config, **overrides: Any) -> Config:
    """Return a new Config with the given fields replaced."""
    return replace(config, **overrides)

def update_nested(state: AppState, path: str, value: str) -> AppState:
    """Deep copy, modify nested field, return new state."""
    new_state = deepcopy(state)
    new_state.settings[path] = value
    return new_state
```

### 11. Function Composition

- Build complex behaviour by chaining small functions together rather than writing monolithic procedures.
- Use `functools.reduce` for left-to-right composition of multiple functions.
- Prefer pipelines where the output of one function becomes the input of the next.

```python
from functools import reduce

def compose(*funcs):
    """Compose functions left-to-right: compose(f, g, h)(x) == h(g(f(x)))"""
    def identity(x): return x
    return reduce(lambda f, g: lambda x: g(f(x)), funcs, identity)

def strip_lines(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines())

def drop_empty(lines: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line for line in lines if line)

def to_upper(lines: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line.upper() for line in lines)

normalize = compose(strip_lines, drop_empty, to_upper)
# normalize("  hello\n\nworld  ") -> ("HELLO", "WORLD")
```

### 12. Expression-Oriented Style

- Prefer expressions that evaluate to a value over statements that perform an action.
- Use ternary expressions (`x if cond else y`) instead of `if`/`else` blocks that assign to a variable.
- Use comprehensions and generator expressions over loops that `.append()`.
- Avoid bare `return` or `return None` — return a meaningful value (e.g., an empty tuple, `0`, or an explicit `Result` type).
- Every branch of a function should contribute to the return value; dead-end branches are a smell.

```python
# Statement-oriented (avoid)
def describe(n: int) -> str:
    if n > 0:
        return "positive"
    elif n < 0:
        return "negative"
    else:
        return "zero"

# Expression-oriented (prefer — already fine here, but contrast with multi-step)
def describe(n: int) -> str:
    return "positive" if n > 0 else "negative" if n < 0 else "zero"

# Against building a list imperatively:
def evens(nums: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(x for x in nums if x % 2 == 0)
```

### 13. Monadic Error Handling

- Never `raise` or `except` across pure function boundaries. Pure functions must return success or failure as data.
- Model fallible pure operations as returning an explicit `Result` type (e.g., a union or a simple `tuple[bool, T]`).
- Chain fallible operations with `and_then` / `or_else` patterns rather than `try`/`except`.
- If using a library, prefer `returns.Result` or a hand-rolled equivalent.

```python
from typing import TypeAlias

Result: TypeAlias = tuple[bool, object]  # (True, value) | (False, error)

def success(value): return (True, value)
def failure(error): return (False, error)

def safe_divide(a: int, b: int) -> Result:
    return failure("division by zero") if b == 0 else success(a / b)

def add_one(x: float) -> Result:
    return success(x + 1)

def and_then(result: Result, f) -> Result:
    return f(result[1]) if result[0] else result

# Chaining without try/except
result = and_then(safe_divide(10, 2), add_one)  # (True, 6.0)
```

### 14. Lazy Evaluation

- Use generators (`yield`) and generator expressions (`(...)`) for sequences that may not need to be fully realised.
- Use `itertools` (e.g., `islice`, `takewhile`, `dropwhile`) to process only what is needed.
- Avoid materialising an entire collection into a `list` or `tuple` when the consumer only inspects the first few elements.
- Prefer `any()` and `all()` with generator expressions for early-exit predicates.

```python
from itertools import islice

def read_large_file(path: str):
    """Generator: yields lines one at a time, never loads the whole file."""
    with open(path) as f:
        yield from f

def first_n_lines(path: str, n: int) -> tuple[str, ...]:
    return tuple(islice(read_large_file(path), n))
```

### 15. Additional Principles

- Avoid classes that mix data and behaviour; use functions operating on data instead.
- Mark functions that depend on external mutable state as `impure_` by naming convention.
- Write docstrings for every public function; describe *what*, not *how*.
- Use `@functools.cache` or `@functools.lru_cache` to memoize expensive pure functions.


