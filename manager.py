from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.orm.exc as exceptions
from datetime import datetime
from db import Client, Temp, tables


class Manager:
    def __init__(self, engine_adress="sqlite:///db.db"):
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

    def add_client(self, identifier: str, commit=True):
        self.session.add(Client(identifier))
        if commit:
            self.session.commit()

    def add_temp(self, client_identifier: str, cpu_identifier: str, temperature: int, commit=True):
        try:
            client: Client = self.session.query(Client).filter_by(identifier=client_identifier).one()
        except exceptions.NoResultFound:
            client = Client(client_identifier)
        client.temps.append(Temp(identifier=cpu_identifier, temperature=temperature, time=datetime.now()))
        self.session.add(client)
        if commit:
            self.session.commit()


if __name__ == '__main__':
    with Manager() as cursor:
        clients = cursor.session.query(Client).all()

