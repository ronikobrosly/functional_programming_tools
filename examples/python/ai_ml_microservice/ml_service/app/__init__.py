"""Application layer: training, wiring, and the entry point.

`app.core` is pure; `app.shell` holds the adapters; this top level does the
impure *composition* -- building adapters, injecting them into the pure core,
and starting the server.
"""
