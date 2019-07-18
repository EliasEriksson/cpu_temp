from apscheduler.schedulers.blocking import BlockingScheduler
from typing import Iterable
from socket import gethostname
from pathlib import Path
from time import sleep
from manager import Manager
import exceptions
import argparse

PROJECT_ROOT = Path(__file__).absolute().parent
DATABASE_ADRESS = f'sqlite:////{str(PROJECT_ROOT.joinpath("db.db"))}'


def read_file(path: Path) -> str:
    with open(str(path)) as file:
        return file.readline().strip()


def get_temp(need_sleep) -> Iterable:
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
            return zip([read_file(label) for label in labels], [int(read_file(temp)) for temp in temps])


def store_temp(need_sleep=False):
    with Manager(DATABASE_ADRESS) as manager:
        for temps in get_temp(need_sleep=need_sleep):
            manager.add_temp(gethostname(), *temps)


def schedule(parsed_args: argparse.Namespace):
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


def view(args: argparse.Namespace):
    print("Not yet supported.")


def handle():
    parser = argparse.ArgumentParser(description="Logs and views a systems cpu temperature.")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--view", action="store_true")
    parser.add_argument("--job_type", help="valid values 'cron', 'interval'", type=str)
    parser.add_argument("--year", "--years", type=int)
    parser.add_argument("--month", "--months", type=int)
    parser.add_argument("--week", "--weeks", type=int)
    parser.add_argument("--day", "--days", type=int)
    parser.add_argument("--hour", "--hours", type=int)
    parser.add_argument("--minute", "--minutes", type=int)
    parser.add_argument("--second", "--seconds", type=int)
    parser.add_argument(
        "--misfire",
        help="If system is unavaileble to execute at desired run time "
             "how long in seconds is it allow to execute past set time.",
        type=int
    )
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

