from asyncio import Task
from subprocess import Popen

from typing_extensions import Any


class Mountpoint:
    title: str
    path: str
    cache_path: str
    stream_url: str
    stream_process: Popen[bytes]
    updater_process: Task[Any]
