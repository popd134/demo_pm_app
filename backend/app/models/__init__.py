"""SQLAlchemy ORM models.

Importing the models here registers their metadata on ``Base`` so
``app.core.database.init_db`` (and the test schema setup) can create the tables.
"""

from app.models.weather import Location, Observation

__all__ = ["Location", "Observation"]
