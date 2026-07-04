"""Pure core: transforms and decisions only. No I/O, no mutation.

Every module in this package imports **only** the standard library and other
`core` modules. It must never import from `app.shell` or touch the network,
filesystem, clock, or database. That invariant is what makes the core
exhaustively unit-testable without mocks.
"""
