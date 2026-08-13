"""SQLAlchemy ORM models.

Importing the models here registers their metadata on ``Base`` so
``app.core.database.init_db`` (and the test schema setup) can create the tables.
"""

from app.models.alert import Alert
from app.models.forecast import Forecast, ForecastPoint
from app.models.preferences import SavedLocation, UserPreferences
from app.models.user import User, UserRole
from app.models.weather import Location, Observation

__all__ = [
    "Location",
    "Observation",
    "Forecast",
    "ForecastPoint",
    "User",
    "UserRole",
    "Alert",
    "UserPreferences",
    "SavedLocation",
]
