from typing import Iterable
from socket import gethostname
from pathlib import Path
from time import sleep
from manager import Manager
from db import Client


def read_file(path: Path) -> str:
    with open(str(path)) as file:
        return file.readline().strip()


def get_temp() -> Iterable:
    base = Path("/sys/class/hwmon/")
    for hwmon in base.iterdir():
        name = read_file(hwmon.joinpath("name").absolute())
        if name.lower() == "coretemp":
            labels = [file for file in hwmon.iterdir()
                      if file.stem.endswith("_label")
                      and "core" in read_file(file.absolute()).lower()]
            temps = [hwmon.joinpath(label.stem.replace("label", "input"))
                     for label in labels]
            sleep(3)  # needed for the processor to cool down from the heat generated to launch python
            return zip([read_file(label) for label in labels], [int(read_file(temp)) for temp in temps])


def store_temp(client_identifier: str, temps: Iterable):
    with Manager() as manager:
        for identifier, temp in temps:
            manager.add_temp(client_identifier, identifier, temp)


def check_temps(client_identifier: str):
    with Manager() as manager:
        client: Client = manager.session.query(Client).filter_by(identifier=client_identifier).one()
        for temp in client.temps:
            print(temp)


if __name__ == '__main__':
    # store_temp(gethostname(), get_temp())
    check_temps(gethostname())
