"""SQLAlchemy ORM models.

Concrete domain models (locations, observations, forecasts, users) are added by
later WBS tasks — most notably 1.2.1 "Design database schema". This package exists
so ``app.core.database.init_db`` can import and register model metadata.
"""
