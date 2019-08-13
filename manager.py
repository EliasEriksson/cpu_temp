from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.orm.exc as exceptions
from datetime import datetime
from db import Client, Processor, tables


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


if __name__ == '__main__':
    import statistics
    from socket import gethostname

    with Manager() as cursor:
        cursor.add_client(gethostname())
        # cursor.add_cpu(gethostname(), )
        # c: Client = cursor.session.query(Client).filter_by().first()
        # processors = cursor.session.query(Processor).filter(
        #     datetime(2019, 7, 22) <= Processor.time
        # ).filter(
        #     Processor.time < datetime(2019, 7, 23)
        # ).all()
    # print(len(processors))
    #     c: Client = cursor.session.query(Client).first()
        # temperatures = [temp.temperature for temp in c.processors]
        # print(c.processors)

    # d = {temp.core: [value for value in c.processors] for temp in c.processors}
    # print(d)
    # print(f"Systems mean CPU temperature                         {statistics.mean(temperatures) / 1000} C")
    # print(f"Systems median CPU temperature                       {statistics.median(temperatures) / 1000} C")
    # print(f"Systems standard deviation from mean CPU temperature {statistics.stdev(temperatures) / 1000} C")
    # print(f"Systems Max temperature                              {max(temperatures) / 1000} C")
    # print(f"Systems Min temperature                              {min(temperatures) / 1000} C")
    # for core, processors in d.items():
    #     print(f"System {core} avarage temperature is {statistics.mean(processors)}")

