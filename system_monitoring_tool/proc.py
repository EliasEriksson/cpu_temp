from typing import List, Tuple, Union
from operator import itemgetter
from pathlib import Path
from time import sleep
import re


def read_proc_pid_cmdline(pid: Union[int, str]) -> str:
    """
    reads /proc/pid/cmdline

    finds the command that was executed to start the process

    :param pid: Union[int, str], process id (pid)
    :return: str, executed command
    """
    return Path(f"/proc/{pid}/cmdline").read_text().replace("\x00", " ")


def read_proc_stat() -> str:
    """
    reads /proc/stat

    reads /proc/stat to get the cumulative cpu time of each core
    this is further processed in 'parse_proc_stat()'

    :return: str, content on /proc/stat to be processed
    """
    return Path("/proc/stat").read_text()


def parse_proc_stat(stat: str) -> List[int]:
    """
    parses the content from /proc/stat for cumulative cpu time

    searches through the content of /proc/stat for each processor in the system and
    summarizes the processors jiffies.

    :param stat: str, content from 'read_proc_stat()'
    :return: List[int], list of each processors jiffes
    """
    return [sum([int(cpu_time) for cpu_time in line.strip().split(" ")[1:]])
            for line in stat.split("\n")
            if re.search(r"^cpu\d", line)]


def new_parse_proc_stat(stat: str) -> List[Tuple[int, int]]:
    """

    :param stat:
    :return: list of each processors total jiffies and used jiffies
    """
    lst = []
    for line in stat.split("\n"):
        if re.search(r"^cpu\d", line):
            jiffies = [int(x) for x in line.strip().split(" ")[1:]]
            total_jiffies = sum(jiffies)
            used_jiffies = total_jiffies - sum(itemgetter(2, 3)(jiffies))
            lst.append((total_jiffies, used_jiffies))
    return lst


def read_proc_pids_stat() -> List[str]:
    """
    reads all pid folders in /proc

    reads /proc/pid/stat of each pid currently on the system
    this is furhter processed in 'parse_proc_pids_stat()'
    :return: List[str], list of all the content in each /proc/pid/stat
    """
    path = Path("/proc")
    return [pid.joinpath("stat").read_text() for pid in path.iterdir()
            if pid.match("*[0-9]")]


def parse_proc_pids_stat(pids: List[str]) -> List[Tuple[int]]:
    """
    parses the content from /proc/pid/stat for process cpu time usage

    reads the content from /proc/pid/stat provided from 'read_proc_pids_stat()' to find
    the pid, processor id, utime, stime (read man page of /proc/pid/stat 1, 14, 15, 39)

    :param pids: List[str], content from 'read_proc_pids_stat()'
    :return: List[Tuple[int]], list of process id, processor id, utime, stime
    """
    return [tuple(int(s) for s in itemgetter(0, 38, 13, 14)(process.split(" "))) for process in pids]


def get_cpu_usage(time: float = 1) -> Tuple[List[float], List[Tuple[int, float, str]]]:
    """
    calculates the cpu usage of each process on the system

    calculates the cpu usage of each process and what command that issued the process to beguin with.
    the calculation followed the instructions from stackoverflow user: caf
    https://stackoverflow.com/questions/1420426/how-to-calculate-the-cpu-usage-of-a-process-by-pid-in-linux-from-c/1424556#1424556
    the difference being that the processes are compared to the process id they ended on

    /proc/stat and each /proc/pid/stat is being read before the program sleeps for given ammount of seconds
    after the sleep is over both /proc/stat and /proc/pid/stat is read again and then results from before
    and after the sleep are being processed.

    :param time: float, the time the program should wait before getting a second measurign point
    :return: List[Tuple[pid, processor id, processor usage, executed command]]
    """
    cpu_stats_t0 = read_proc_stat()
    pid_stats_t0 = read_proc_pids_stat()
    sleep(time)
    cpu_time_t1 = read_proc_stat()
    pid_stats_t1 = read_proc_pids_stat()

    cpu_clock_ticks = [
        (tot_c - tot_i, used_c - used_i)
        for (tot_i, used_i), (tot_c, used_c)
        in zip(new_parse_proc_stat(cpu_stats_t0), new_parse_proc_stat(cpu_time_t1))]

    process_clock_ticks_used = [
        (pid, p_t1, u_t1 - u_t0, s_t1 - s_t0)
        for (_, p_t0, u_t0, s_t0), (pid, p_t1, u_t1, s_t1)
        in zip(parse_proc_pids_stat(pid_stats_t0), parse_proc_pids_stat(pid_stats_t1))
        if pid == _]

    processor_usage = [used / total * 100 for total, used in cpu_clock_ticks]

    process_usage = [
        (processor, ((utime + stime) / cpu_clock_ticks[processor][0]) * 100, read_proc_pid_cmdline(pid))
        for pid, processor, utime, stime
        in process_clock_ticks_used]

    return processor_usage, process_usage


if __name__ == '__main__':
    get_cpu_usage(3)
