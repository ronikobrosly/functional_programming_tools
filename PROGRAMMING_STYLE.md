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
quick-and-looser.

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
- Use recursion only where it reads more clearly *and* the language makes it safe
  (tail-call optimization or guaranteed-bounded depth). Otherwise prefer fold/iterate
  combinators to avoid stack overflow.
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

- Prefer recursion over mutable loop accumulators for inherently recursive data (trees, graphs), but prefer `map`/`filter`/`reduce` pipelines for linear data.
- Avoid classes that mix data and behaviour; use functions operating on data instead.
- Mark functions that depend on external mutable state as `impure_` by naming convention.
- Write docstrings for every public function; describe *what*, not *how*.
- Use `@functools.cache` or `@functools.lru_cache` to memoize expensive pure functions.

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (0-indexed)."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

---

---------------------------------------------------------------------

---

# Rust — Functional & Strict Programming Style


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
quick-and-looser.

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
- Use recursion only where it reads more clearly *and* the language makes it safe
  (tail-call optimization or guaranteed-bounded depth). Otherwise prefer fold/iterate
  combinators to avoid stack overflow.
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

### 1. First-Class & Higher-Order Functions

- Pass closures (`|args| expr`) and function pointers (`fn(...) -> ...`) freely.
- Use `Fn`, `FnMut`, and `FnOnce` trait bounds to accept callables generically.
- Return closures from functions using `impl Fn(...) -> ...` or `Box<dyn Fn(...)>` when the type is not nameable.

```rust
fn multiply(a: i32, b: i32) -> i32 { a * b }

fn partial_apply<F, A, B, R>(f: F, a: A) -> impl Fn(B) -> R
where
    F: Fn(A, B) -> R,
    A: Copy,
{
    move |b| f(a, b)
}

let double = partial_apply(multiply, 2);
assert_eq!(double(5), 10);
```

### 2. Pure Functions

- A function must be deterministic and free of side effects for the same input.
- Avoid `&mut` parameters; prefer owned values and return new owned values.
- Isolate impure operations (I/O, `std::env`, `SystemTime`, `thread_rng()`) in a small set of `action` modules.

```rust
// Pure
fn add(a: i32, b: i32) -> i32 { a + b }
```

### 3. Iterator Combinators: `map`, `filter`, `fold`

- Use Rust's `Iterator` trait methods (`map`, `filter`, `fold`, `flat_map`, `take_while`, etc.) for all data transformations.
- Never write a `for` loop when an iterator combinator chain expresses the intent.
- Collect into owned collections (`Vec`, `HashMap`, `HashSet`) at the end of the pipeline.

```rust
let nums = vec![1, 2, 3, 4, 5, 6];
let result: i32 = nums
    .iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * 2)
    .fold(0, |acc, x| acc + x);
assert_eq!(result, 24);
```

### 4. Immutability & Copy-on-Write

- Bind with `let`, never `let mut`, unless mutation is strictly required and isolated to an `action`.
- Use `Cow<'_, T>` for copy-on-write semantics when ownership may or may not require allocation.
- Derive `Clone` for value types; prefer `.clone()` over `&mut` in-place mutation.
- Use `Rc` / `Arc` for shared ownership and `RefCell` / `Mutex` only at the action boundary.

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
struct Config {
    host: String,
    port: u16,
}

let old = Config { host: "0.0.0.0".into(), port: 8080 };
let new = Config { port: 9090, ..old.clone() };
```

### 5. Strictness in Typing

- Leverage Rust's algebraic data types: `enum` for sum types, `struct` for product types.
- Use `Option<T>` instead of sentinel values; use `Result<T, E>` for fallible operations.
- Prefer newtypes (`struct Meters(f64);`) over primitive obsession.
- Enable `#![deny(unsafe_code)]` at the crate root unless unavoidable.
- Use exhaustive `match` with no wildcards where the domain is finite; prefer `match` over `if let`.

```rust
pub struct Meters(pub f64);

#[derive(Debug, Clone)]
enum Direction { North, South, East, West }

fn heading(d: Direction) -> f64 {
    match d {
        Direction::North => 0.0,
        Direction::East  => 90.0,
        Direction::South => 180.0,
        Direction::West  => 270.0,
    }
}

fn fetch(id: u64) -> Result<String, Error> {
    // ...
}
```

### 6. Closures (Anonymous Functions)

- Use closures for short, context-capturing callbacks: `iter.map(|x| x * 2)`.
- When the closure body grows beyond a few lines, extract it into a named function.
- Annotate closure parameter and return types only when the compiler cannot infer them.

### 7. Separate Data from Calculations from Actions

- **Data** — `struct` and `enum` definitions, `const` values. Pure data, no behaviour (no `impl` blocks with logic).
- **Calculations** — pure functions implemented on data types via `impl` blocks that contain only pure transformation methods, or free-standing functions in a `calc` module.
- **Actions** — functions that perform I/O, spawn tasks, interact with the operating system, or mutate global state.

```
src/
  data.rs          # struct/enum definitions, consts
  calc.rs          # pure business logic
  action.rs        # I/O, DB, HTTP, spawning
```

```rust
// data.rs
pub struct Order {
    pub items: Vec<Item>,
}

// calc.rs
pub fn order_total(order: &Order) -> f64 {
    order.items.iter().map(|i| i.price * i.qty as f64).sum()
}

// action.rs
pub async fn save_order(db: &Database, order: &Order) -> Result<(), DbError> {
    // ...
}
```

### 8. Minimizing Side Effects

- A function should do *one thing* only. If it reads a file and also parses it, split into two functions: one that reads (action), one that parses (calculation).
- Never mix I/O into a pure calculation function. Calculations must accept their dependencies as arguments.
- Use dependency injection via trait objects: impure functions receive pure functions as generic parameters.
- Avoid logging, metrics, or telemetry inside pure functions — lift those into the calling action layer.
- Mark async functions that perform I/O clearly; pure functions should be synchronous.

```rust
// Impure — mixed concerns
fn load_and_sum(path: &str) -> std::io::Result<i32> {
    let content = std::fs::read_to_string(path)?;
    Ok(content.lines().filter_map(|l| l.parse::<i32>().ok()).sum())
}

// Pure calculation
fn parse_and_sum(lines: &[&str]) -> i32 {
    lines.iter().filter_map(|l| l.parse::<i32>().ok()).sum()
}

// Impure action (thin boundary)
fn read_lines(path: &str) -> std::io::Result<Vec<String>> {
    let content = std::fs::read_to_string(path)?;
    Ok(content.lines().map(String::from).collect())
}
```

### 9. Small, Composable Functions

- Each function should fit on screen — aim for 5–15 lines. If a function exceeds ~20 lines, extract helper functions.
- A 50-line method should be refactored into three or four smaller functions that compose together.
- Name extracted functions clearly so the top-level function reads like a sequence of steps at a single level of abstraction.
- Each extracted function must be independently testable and `#[test]`-able.

```rust
use std::collections::BTreeMap;

// After: small, composable functions
fn filter_valid(orders: &[Order]) -> Vec<Order> {
    orders.iter().filter(|o| o.amount > 0.0).cloned().collect()
}

fn totals_by_category(orders: &[Order]) -> BTreeMap<String, f64> {
    orders.iter().fold(BTreeMap::new(), |mut acc, o| {
        *acc.entry(o.category.clone()).or_default() += o.amount;
        acc
    })
}

fn format_report_lines(totals: &BTreeMap<String, f64>) -> Vec<String> {
    totals
        .iter()
        .map(|(cat, total)| format!("{cat}: ${total:.2}"))
        .collect()
}

fn process_orders(orders: &[Order]) -> Report {
    let valid = filter_valid(orders);
    let totals = totals_by_category(&valid);
    let lines = format_report_lines(&totals);
    Report { title: "Sales".into(), lines }
}
```

### 10. Strict Copy-on-Write Paradigm

- Every "mutating" function must follow this pattern: **(1)** take an owned value or immutable reference, **(2)** create a clone/copy, **(3)** apply the change to the clone, **(4)** return the owned clone.
- Never take `&mut T` in a pure function — use `T` or `&T` and return `T`.
- Use struct update syntax (`Config { port: 9090, ..old }`) for partial copies.
- For nested structures, derive `Clone` and call `.clone()` explicitly; for performance-critical paths use `Cow<'_, T>`.

```rust
fn add_item(cart: Vec<CartItem>, item: CartItem) -> Vec<CartItem> {
    let mut new_cart = cart.clone();
    new_cart.push(item);
    new_cart
}

#[derive(Debug, Clone)]
struct Config {
    host: String,
    port: u16,
    tls: bool,
}

fn set_port(config: &Config, port: u16) -> Config {
    Config { port, ..config.clone() }
}

fn enable_tls(config: &Config) -> Config {
    Config { tls: true, ..config.clone() }
}
```

### 11. Function Composition

- Build complex behaviour by chaining small functions together rather than writing monolithic procedures.
- Since Rust does not have a built-in compose operator, define one when needed or chain via method calls on iterator pipelines.
- Prefer pipelines where the output of one function is piped into the next.

```rust
fn compose<A, B, C>(f: impl Fn(A) -> B, g: impl Fn(B) -> C) -> impl Fn(A) -> C {
    move |x| g(f(x))
}

fn strip_lines(text: &str) -> Vec<&str> {
    text.lines().map(|l| l.trim()).collect()
}

fn drop_empty(lines: Vec<&str>) -> Vec<&str> {
    lines.into_iter().filter(|l| !l.is_empty()).collect()
}

fn to_upper(lines: Vec<&str>) -> Vec<String> {
    lines.into_iter().map(|l| l.to_uppercase()).collect()
}

let normalize = compose(strip_lines, compose(drop_empty, to_upper));
// normalize("  hello\n\nworld  ") -> ["HELLO", "WORLD"]
```

### 12. Expression-Oriented Style

- Everything in Rust is already an expression — lean into it.
- Use `if`/`else` as expressions that produce a value; never assign a mutable variable in each branch when an expression suffices.
- Use blocks `{ ... }` as expressions whose last line (without semicolon) is the block's value.
- Avoid `return` keywords at the end of a function; let the final expression be the return value.
- Every branch in a `match` must produce a value of the same type.

```rust
// Statement-like (avoid)
fn describe(n: i32) -> String {
    if n > 0 {
        return "positive".into();
    } else if n < 0 {
        return "negative".into();
    } else {
        return "zero".into();
    }
}

// Expression-oriented (prefer)
fn describe(n: i32) -> String {
    if n > 0 { "positive" } else if n < 0 { "negative" } else { "zero" }.into()
}
```

### 13. Monadic Error Handling with `Option` / `Result`

- Chain fallible operations with `and_then`, `or_else`, `map`, and `map_err`; avoid early `unwrap()` or `expect()` in pure code.
- Use the `?` operator for concise propagation within functions that return `Result`.
- Never panic in a pure function — return `Result` or `Option` instead.
- Model optional data with `Option<T>`, not `null` sentinels or magic values.

```rust
fn safe_divide(a: i32, b: i32) -> Result<f64, String> {
    if b == 0 {
        Err("division by zero".into())
    } else {
        Ok(a as f64 / b as f64)
    }
}

fn add_one(x: f64) -> Result<f64, String> {
    Ok(x + 1.0)
}

// Chaining without explicit match
let result = safe_divide(10, 2).and_then(add_one); // Ok(6.0)
```

### 14. Pattern Matching

- Use exhaustive `match` for every `enum`. Avoid wildcard `_` arms when the enum is under your control — this ensures a compile error when variants are added.
- Prefer `match` over `if let` / `else` chains for any type with more than two meaningful variants.
- Destructure structs and tuples inline to avoid repeated field access.

```rust
#[derive(Debug, Clone)]
enum Command {
    Move { x: i32, y: i32 },
    Speak(String),
    Sleep(u64),
    Quit,
}

fn execute(cmd: &Command) -> String {
    match cmd {
        Command::Move { x, y } => format!("moving to ({x}, {y})"),
        Command::Speak(msg) => format!("says: {msg}"),
        Command::Sleep(ms) => format!("sleeping {ms}ms"),
        Command::Quit => "quitting".into(),
    }
}
```

### 15. Lazy Evaluation

- Use Rust's `Iterator` trait for lazy computation — no work is done until `collect()`, `for_each()`, `find()`, etc. are called.
- Prefer `iter()` over `into_iter()` when you do not need ownership; prefer `iter().copied()` over `iter().cloned()` for `Copy` types.
- Avoid collecting into a `Vec` or `HashMap` when the consumer only needs the first few elements — use `.take(n)`, `.find()`, `.any()`, `.all()`.
- Use `std::iter::from_fn`, `std::iter::successors`, and `std::iter::repeat_with` for generating lazy sequences.

```rust
fn first_n_even_squares(values: &[i32], n: usize) -> Vec<i32> {
    values
        .iter()
        .filter(|&&x| x % 2 == 0)
        .map(|&x| x * x)
        .take(n)
        .collect()
}
```

### 16. Additional Principles

- Embrace the type system — make illegal states unrepresentable (`enum`, newtypes, exhaustive `match`).
- Prefer `Result` with custom error types over panicking; handle errors explicitly at every layer.
- Avoid interior mutability (`Cell`, `RefCell`, `Mutex`) outside of action modules.
- Use `#[must_use]` on pure functions whose return value should never be silently discarded.
- Prefer `iter().collect()` over manual accumulation; prefer `impl Trait` return types over concrete collections where possible.
- Mark functions that perform I/O with a naming convention like `action_` prefix.
- Write doc comments (`///`) for every public item; explain *what* the function guarantees, not how it works internally.

```rust
/// Returns the running totals of the given slice.
///
/// Each element at index `i` is the sum of `values[0..=i]`.
#[must_use]
pub fn running_totals(values: &[i32]) -> Vec<i32> {
    values
        .iter()
        .scan(0, |acc, &x| {
            *acc += x;
            Some(*acc)
        })
        .collect()
}
```
