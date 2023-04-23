from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import settings


def get_engine() -> Engine:
    engine = create_engine(settings.DB_CONN_URL)
    return engine
