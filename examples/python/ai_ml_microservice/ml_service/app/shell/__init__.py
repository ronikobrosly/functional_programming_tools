"""Impure shell: adapters to the outside world.

Each module here wraps exactly one external system (config file, model store,
database, HTTP) and does one narrow effect, returning **plain immutable data**
to the core -- never ORM objects, open handles, or business logic. The shell
may import from `app.core` (for its value types); the core never imports the
shell. The dependency arrow points inward.
"""
