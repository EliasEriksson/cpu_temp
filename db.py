from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()
initial = {i for i in globals().keys()}
# add tables bellow


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String)
    temps = relationship("Temp", back_populates="client")

    def __init__(self, identifier: str):
        super(Client, self).__init__()
        self.identifier = identifier

    def __repr__(self):
        return f"{self.__class__.__name__}(identifier={self.identifier})"

    @classmethod
    def create(cls, engine):
        cls.metadata.create_all(engine)


class Temp(Base):
    __tablename__ = "temps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates=__tablename__)

    identifier = Column(String)
    temperature = Column(Integer)
    time = Column(DateTime)

    def __init__(self, identifier: str, temperature: int, time: datetime):
        super(Temp, self).__init__()
        self.identifier = identifier
        self.temperature = temperature
        self.time = time

    def __str__(self):
        return f"{self.identifier} reached temperature {self.temperature} @ {self.time}"

    def __repr__(self):
        return f"{self.__class__.__name__}(client_id={self.client_id}, identifier={self.identifier}," \
            f"temperature={self.temperature}, time={self.time.__repr__()})"

    @classmethod
    def create(cls, engine):
        cls.metadata.create_all(engine)


# add tables above
tables = [table for name, table in list(globals().items())
          if not name.startswith("__") and name not in {"initial"}.union(initial)]
