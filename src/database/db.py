from sqlmodel import create_engine, Session
from sqlalchemy.sql.selectable import Select
from typing import Any

# TODO: make this url an environment variable 
DATABASE_URL = "sqlite:///src/database/db.sqlite"
        
class DatabaseMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Database(metaclass=DatabaseMeta):
    def __init__(self) -> None:
        self._engine = create_engine(DATABASE_URL, echo=False)
    
    def create(self, data: Any) -> Any:
        with Session(self._engine) as session:
            session.add(data)
            session.commit()
            session.refresh(data)
            return data

    def get(self, statement: Select) -> Any:
        with Session(self._engine) as session:
            results = session.exec(statement)
            result = results.first()
            return result

    def get_all(self, statement: Select) -> Any:
        with Session(self._engine) as session:
            results = session.exec(statement)
            return results        

    def update(self, id: str, stat: Any):
        pass

    def delete(self, statement: Select):
        with Session(self._engine) as session:
            results = session.exec(statement)
            result = results.one() # Ensure that there's exactly one row matching the query

            session.delete(result)
            session.commit()