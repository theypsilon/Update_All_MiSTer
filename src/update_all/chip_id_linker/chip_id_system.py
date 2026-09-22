import builtins
import fcntl
import mmap
import multiprocessing
import os
import subprocess
import time
from typing import Mapping

from update_all.other import current_update_all_archive_path


class ChipIdSystem:
    def __init__(self, environment: Mapping[str, str]):
        self.environment = environment

    open_file = staticmethod(builtins.open)
    open_device = staticmethod(os.open)
    write = staticmethod(os.write)
    close = staticmethod(os.close)
    ioctl = staticmethod(fcntl.ioctl)
    mmap = staticmethod(mmap.mmap)
    exists = staticmethod(os.path.exists)
    stat = staticmethod(os.stat)
    remove = staticmethod(os.remove)
    makedirs = staticmethod(os.makedirs)
    replace = staticmethod(os.replace)
    chmod = staticmethod(os.chmod)
    run = staticmethod(subprocess.run)
    popen = staticmethod(subprocess.Popen)
    kill = staticmethod(os.kill)
    getpid = staticmethod(os.getpid)
    get_context = staticmethod(multiprocessing.get_context)
    monotonic = staticmethod(time.monotonic)
    sleep = staticmethod(time.sleep)
    print_result = staticmethod(builtins.print)
    current_archive_path = staticmethod(current_update_all_archive_path)
