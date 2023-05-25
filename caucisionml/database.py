from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def repository_method(func):
    def wrapper(*args, **kwargs):
        with Session.begin() as session:
            return func(session, *args, **kwargs)

    return wrapper
