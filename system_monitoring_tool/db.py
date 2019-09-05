from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
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
    processors = relationship("Processor", back_populates="client")

    def __init__(self, identifier: str):
        super(Client, self).__init__()
        self.identifier = identifier

    def __repr__(self):
        return f"{self.__class__.__name__}(identifier={self.identifier})"

    @classmethod
    def create(cls, engine):
        cls.metadata.create_all(engine)


class Processor(Base):
    __tablename__ = "processors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates=__tablename__)

    core = Column(Integer)
    processor = Column(Integer)
    processor_usage = Column(Float)
    heaviest_process = Column(String)
    heaviest_process_usage = Column(Float)
    temperature = Column(Integer)
    time = Column(DateTime)

    def __init__(self, core: int, cpu: int, process: str, cpu_usage: float,
                 process_usage: float, temperature: int, time: datetime):
        super(Processor, self).__init__()
        self.core = core
        self.processor = cpu
        self.processor_usage = cpu_usage
        self.heaviest_process = process
        self.heaviest_process_usage = process_usage
        self.temperature = temperature
        self.time = time

    def __str__(self):
        return f"{self.core} reached temperature {self.temperature} @ {self.time}"

    def __repr__(self):
        return f"{self.__class__.__name__}(client_id={self.client_id}, core={self.core}," \
            f"temperature={self.temperature}, time={self.time.__repr__()})"

    def __lt__(self, other: "Processor"):
        return self.temperature < other.temperature

    def __gt__(self, other: "Processor"):
        return self.temperature > other.temperature

    def __eq__(self, other: "Processor"):
        return self.temperature == other.temperature

    @classmethod
    def create(cls, engine):
        cls.metadata.create_all(engine)


# add tables above
tables = [table for name, table in list(globals().items())
          if not name.startswith("__") and name not in {"initial"}.union(initial)]
