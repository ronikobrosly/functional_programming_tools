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