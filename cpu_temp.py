from typing import Dict, Union, Tuple, Pattern, List
from apscheduler.schedulers.blocking import BlockingScheduler
from socket import gethostname
from pathlib import Path
from time import sleep
from manager import Manager
from datetime import datetime
from datetime import timedelta
import exceptions
import argparse
import subprocess
import re


PROJECT_ROOT = Path(__file__).absolute().parent
DATABASE_ADRESS = f'sqlite:////{str(PROJECT_ROOT.joinpath("db.db"))}'


def read_file(path: Path) -> str:
    """
    open a file and read its first line

    reads the first line of a file

    :param path: Path, path to the file
    :return: str, the first line of a file
    """
    with open(str(path)) as file:
        return file.readline().strip()


def parse_ps(row: str, regex: Pattern) -> Tuple[int, float, str]:
    """
    parses text with given regex pattern

    used to parse the output of the ps command where 3 columns are expected
    index 0: processor id
    index 1: process processor_usage
    index 2: command

    :param row: str, one row output of the ps command
    :param regex: Pattern, a regex pattern from re.compile
    :return: tuple(thread_id: int, process_usage: float, command: str)
    """
    match = regex.search(row)
    if match:
        processor_id, usage, command = match.groups()
        try:
            executable, script, *_ = command.split(" ")
            if "/" in executable and "/" in script:
                executable = f"{executable} {script}"
            else:
                raise exceptions.NoScript(f"{script} is not a script")
        except (ValueError, exceptions.NoScript):
            executable, *_ = command.split(" ")

        return int(processor_id), float(usage), str(executable)


def get_processes() -> Dict[int, dict]:
    """
    finds the heaviest processes in the system for each processor

    searches the full list of processes in the system and maps the heaviest process,
    the command to the heaviest process aswell as the full processor usage.
    keys: 'process_usage', 'command' and 'processor_usage'

    :return: dict(processor_id: int) -> dict
    """
    process = subprocess.run("ps -Ao psr,pcpu,command, --no-headers".split(),
                             stdout=subprocess.PIPE, universal_newlines=True)
    regex = re.compile(r"(\d)\s+(\d+\.\d+)\s+(.+)")
    processes_table = [parse_ps(row, regex) for row in process.stdout.split("\n") if row]
    processes_table.sort(key=lambda p: p[1])

    processes = {}
    for processor_id, usage, command in processes_table:
        if processor_id not in processes:
            processes.update({processor_id: {"process_usage": usage, "command": command, "processor_usage": usage}})
        else:
            processes[processor_id]["process_usage"] = usage
            processes[processor_id]["command"] = command
            processes[processor_id]["processor_usage"] += usage

    return processes


def get_cpu_map() -> dict:
    """
    maps each systems processor id to its core id

    On multithraded processors there will be 2 processors that bellongs to the same core
    this function creates a map of which processor (their id) bellongs to what core (id)

    :return: dict[processor_id: int] -> core_id: int
    """

    path = Path("/proc/cpuinfo")
    if path.exists():
        process = subprocess.run("cat /proc/cpuinfo".split(), stdout=subprocess.PIPE, universal_newlines=True)
        out = process.stdout.strip("\n")
        cpu_map = {}
        for processor in out.split("\n\n"):
            processor_id = re.search(r"processor.*(\d)+", processor)
            if processor_id:
                thread = int(processor_id.groups()[0])
                core = re.search(r"core id.*(\d)+", processor)
                if core:
                    core = int(core.groups()[0])
                    cpu_map[thread] = core
                else:
                    raise exceptions.CPULoggingNotSupported("Can not find info about core id in /proc/cpuinfo")
            else:
                raise exceptions.CPULoggingNotSupported("Can not find info about processor id in /proc/cpuinfo")
    else:
        raise exceptions.CPULoggingNotSupported("Can not find file /proc/cpuinfo")
    return cpu_map


def get_session_time() -> timedelta:
    """
    looks up the duration of the current session

    :return: timedelta
    """
    process = subprocess.run("last -1".split(), stdout=subprocess.PIPE, universal_newlines=True)
    out = process.stdout.split("\n")
    session_string = ' '.join([b for b in out[0].split(" ") if b][3:7])
    now = datetime.now()
    session_start = datetime.strptime(f"{now.year} {session_string}", "%Y %a %b %d %H:%M")
    return now - session_start


def get_temp(need_sleep: bool) -> dict:
    """
    reads the temperature on each core in the system

    reads the temperature from each core in the system, for production pass need_sleep as True
    if the reading is taken at the same time as python boots up. Booting python ups the temperature
    on the scheduled core by around 2 degrees C

    the temperature is mapped to the physical core the temperature was read on
    as mili degrees C

    :param need_sleep: bool, pass true if python is booted within 3 second of first reading
    :return: dict[core_id: int] -> temperature: int
    """

    base = Path("/sys/class/hwmon/")
    for hwmon in base.iterdir():
        name = read_file(hwmon.joinpath("name").absolute())
        if name.lower() == "coretemp":
            labels = [file for file in hwmon.iterdir()
                      if file.stem.endswith("_label")
                      and "core" in read_file(file.absolute()).lower()]
            temps = [hwmon.joinpath(label.stem.replace("label", "input"))
                     for label in labels]
            if need_sleep:
                sleep(3)  # needed for the processor to cool down from the heat generated to launch python
            temporary = zip([int(re.search(r"(\d)+", read_file(label)).groups()[0]) for label in labels],
                            [int(read_file(temp)) for temp in temps])

            return {core: temp for core, temp in temporary}


def store_temp(need_sleep: bool = False):
    """
    makes a database entry at the current time

    stats is a table where each row stores:
    core: int, processor: int, processor_usage: float, heaviest_process: str, ...
    ... heaviest_process_usage: float, temperature: int

    :param need_sleep: bool, pass True if reading is taken within 3 seconds of python boot
    :return: None
    """

    core_map = get_cpu_map()
    time = datetime.now()
    temperatures = get_temp(need_sleep)
    processes = get_processes()
    stats = [(core_map[cpu], cpu, processes[cpu]["processor_usage"], processes[cpu]["command"],
              processes[cpu]["process_usage"], temperatures[core_map[cpu]])
             for cpu in core_map.keys()]

    with Manager(DATABASE_ADRESS) as manager:
        client = manager.get_client(gethostname())
        for core, cpu, cpu_usage, process, process_usage, temperature in stats:
            manager.add_cpu(client, core, cpu, cpu_usage, process, process_usage, temperature, time)


def schedule(parsed_args: Union[argparse.Namespace, Dict[str, int]]):
    """
    schedules the application to automaticly collect data

    pass a namespace or dict with one or more of the following keys
    do not include () adding s is optional, ie: both 'year' and 'years' is a valid key
    year(s), month(s), week(s), day(s), hour(s), minute(s), second(s)

    :param parsed_args: Union[argparse.Namespace, Dict[str, int]]
    :return: None
    """

    config = {
        "year": parsed_args.year,
        "month": parsed_args.month,
        "week": parsed_args.week,
        "day": parsed_args.day,
        "hour": parsed_args.hour,
        "minute": parsed_args.minute,
        "second": parsed_args.second}

    if parsed_args.job_type == "interval":
        config = {(k + "s"): config[k] for k in config if k not in ["year", "month"] and config[k] is not None}
    else:
        config = {key: value for key, value in config.items() if value is not None}

    scheduler = BlockingScheduler()
    scheduler.add_executor("processpool")
    scheduler.add_job(store_temp, parsed_args.job_type, misfire_grace_time=parsed_args.misfire, **config)
    scheduler.start()


def view(args: Union[argparse.Namespace, Dict[str, int]]):
    pass


def handle():
    """
    parses the system argluments

    parses the given system arguments and proceeds with the program depending
    on what was given
    OBS! --log can always be passed but --view and --schedule can not be passed at the same time

    :return: None
    """

    parser = argparse.ArgumentParser(description="Logs and views a systems cpu temperature.")
    parser.add_argument("--log", action="store_true")

    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--job_type", help="valid values 'cron', 'interval'", type=str)
    parser.add_argument("--year", "--years", type=int)
    parser.add_argument("--month", "--months", type=int)
    parser.add_argument("--week", "--weeks", type=int)
    parser.add_argument("--day", "--days", type=int)
    parser.add_argument("--hour", "--hours", type=int)
    parser.add_argument("--minute", "--minutes", type=int)
    parser.add_argument("--second", "--seconds", type=int)
    parser.add_argument("--misfire", type=int, help="If system is unavaileble to execute at desired run time "
                                                    "how long in seconds is it allow to execute past set time.")
    parser.add_argument("--view", action="store_true")
    parser.add_argument("--host", type=str, help="The hostname of the client to draw data about.")
    parser.add_argument("--start_date", type=str, help="Date to start draw data from.")
    parser.add_argument("--end_date", type=str, help="Date to end draw data from.")
    parser.add_argument("--this_session", action="store_true")
    parser.add_argument("--min_cpu", type=float, help="Minimum required CPU processor processor_usage for drawn data.")
    parser.add_argument("--max_cpu", type=float, help="Maximum limit for CPU processor processor_usage for drawn data.")
    parser.add_argument("--min_temp", type=float, help="Minimum temperature in celsius to use as datapoints.")
    parser.add_argument("--max_temp", type=float, help="Maximum temperature in celcius to use as datapoints.")

    args = parser.parse_args()
    if args.log or args.schedule or args.view:
        if args.log:
            store_temp(need_sleep=True)
        if args.schedule:
            if args.view:
                raise exceptions.ArgumentError("Can not handle both --view and --schedule at the same time.")
            schedule(args)
        elif args.view:
            if args.schedule:
                raise exceptions.ArgumentError("Can not handle both --view and --schedule at the same time.")
            view(args)
    else:
        raise exceptions.NothingToDo("Need to add '--log' '--view' or '--schedule' to args")


if __name__ == '__main__':
    handle()

