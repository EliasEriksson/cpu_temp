from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.orm.exc as exceptions
from datetime import datetime
from system_monitoring_tool.db import Client, Processor, tables


def create_database(engine_adress: str):
    engine = create_engine(engine_adress)
    for table in tables:
        table.create(engine)


class Manager:
    def __init__(self, engine_adress: str):
        self.engine = create_engine(engine_adress)
        for table in tables:
            table.create(self.engine)

    def __enter__(self):
        session = sessionmaker()
        session.configure(bind=self.engine)
        self.session = session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_client(self, client_identifier: str) -> Client:
        try:
            client: Client = self.session.query(Client).filter_by(identifier=client_identifier).one()
        except exceptions.NoResultFound:
            client: Client = Client(client_identifier)
        return client

    def add_client(self, identifier: str, commit=True):
        self.session.add(Client(identifier))
        if commit:
            self.session.commit()

    def add_cpu(self, client: Client, core: int, cpu: int, cpu_usage: float, process: str,
                process_usage: float, temperature: int, time: datetime, commit=True):
        client.processors.append(Processor(
            core=core, cpu=cpu, cpu_usage=cpu_usage, process=process,
            process_usage=process_usage, temperature=temperature, time=time))
        self.session.add(client)
        if commit:
            self.session.commit()
