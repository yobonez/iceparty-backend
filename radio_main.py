import asyncio
from contextlib import asynccontextmanager

import mutagen
import os
import random
import sys
import subprocess

import uvicorn
from fastapi import FastAPI

import song_updater
import radio_config
from router import song_router

import logging

from models.mountpoint import Mountpoint

logger = logging.getLogger(__name__)
logging.basicConfig(filename='radio.log', level=logging.NOTSET)

config = radio_config.get_config()

radio_rootdir = config["radio-root"]
icecast_source_creds = config["icecast-source"]
icecast_address = config["icecast-address"]
cache_dir = config["cache-dir"]

def error_handler(exc_type, exc_value, exc_tb):
    # traceback.format_exception(exc_type, exc_value, exc_tb)
    logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_tb))
sys.excepthook = error_handler


def get_available_endpoints() -> list[Mountpoint]:
    mountpoint_list: list = os.listdir(radio_rootdir)

    mountpoints: list[Mountpoint] = []
    for mountpoint_name in mountpoint_list:
        to_add: Mountpoint = Mountpoint()

        to_add.title = mountpoint_name
        to_add.path = str(os.path.join(radio_rootdir, mountpoint_name))
        to_add.cache_path = str(os.path.join(cache_dir, mountpoint_name))
        to_add.stream_url = "icecast://{}@{}/{}".format(icecast_source_creds, icecast_address, mountpoint_name)

        mountpoints.append(to_add)

    return mountpoints

def get_file_length(file):
    return file.info.length

def get_files_and_shuffle(mountpoint_directory) -> list[str]:
    lines:list[str] = []
    for root, subdirs, files in os.walk(mountpoint_directory):
            for name in files:
                if os.path.splitext(name)[1] in [".mp3", ".flac"]:
                    filepath = os.path.join(root, name)
                    lines.append(filepath)

                
    random.shuffle(lines)

    return lines

def prepare_files(cache_directory, lines: list[str]):
    ret_songs = []
    global_duration = 0

    if not os.path.exists(cache_directory):
        os.mkdir(cache_directory)

    af = open(os.path.join(cache_directory, "audiofiles.txt"), "a+")

    for filepath in lines:
        filename = os.path.basename(filepath)
        songname = os.path.splitext(filename)[0]
        duration = get_file_length(mutagen.File(filepath))

        ret_songs.append((global_duration, songname))
        af.write("file '{}'\n".format(filepath))

        global_duration += duration

    af.close()

    return ret_songs

def remove_prev_files(cache_directory):
    audiofiles = os.path.join(cache_directory, "audiofiles.txt")
    if os.path.exists(audiofiles):
        os.remove(audiofiles)

def graceful_shutdown(proc, task, mountpoint_name, ffmpeg_log):
    logger.info("Shutting down everything...")

    task.cancel()

    if proc.poll() is None:
        logger.info(f"[{mountpoint_name}] Cleaning up ffmpeg subprocess...")
        proc.terminate()
        proc.wait()

    if ffmpeg_log and not ffmpeg_log.closed:
        logger.info(f"[{mountpoint_name}] Closing ffmpeg log handle...")
        ffmpeg_log.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Preparing endpoints...")
    mountpoints: list[Mountpoint] = get_available_endpoints()

    for mountpoint in mountpoints:
        logger.info(f"[{mountpoint.title}] Preparing songs...")

        remove_prev_files(mountpoint.cache_path)
        lines = get_files_and_shuffle(mountpoint.path)
        songs = prepare_files(mountpoint.cache_path, lines)

        audiofiles_path = str(os.path.join(mountpoint.cache_path, "audiofiles.txt"))

        # cmd = [
        #     "ffmpeg", "-re", "-f", "concat", "-safe", "0", "-i", audiofiles_path,
        #     "-c:a", "libmp3lame", "-ar", "44100", "-ac", "2", "-vn", "-f", "mp3",
        #     "-map_metadata", "0", "-content_type", "audio/mpeg", mountpoint.stream_url
        # ]
        cmd = [
            "ffmpeg", "-re", "-f", "concat", "-safe", "0", "-i", audiofiles_path,
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            "-vn",
            "-f", "adts",
            "-map_metadata", "0",
            "-content_type", "audio/aac",
            mountpoint.stream_url
        ]

        logger.info(f"[{mountpoint.title}] Starting ffmpeg...")
        mountpoint.ffmpeg_log = open(f"ffmpeg-{mountpoint.title}.log", "a+", encoding="utf-8")

        mountpoint.process = subprocess.Popen(cmd, stdout=mountpoint.ffmpeg_log, stderr=mountpoint.ffmpeg_log)

        logger.info(f"[{mountpoint.title}] Starting song updater...")
        mountpoint.updater_task = asyncio.create_task(
            asyncio.to_thread(song_updater.title_updater_start, lines, songs, mountpoint.title, mountpoint.process)
        )

        def handle_task_result(task):
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error("Server crashed:", exc_info=e)
                graceful_shutdown(mountpoint.process, mountpoint.updater_task, mountpoint.title)

        mountpoint.updater_task.add_done_callback(handle_task_result)

    yield

    for mountpoint in mountpoints:
        graceful_shutdown(mountpoint.process, mountpoint.updater_task, mountpoint.title)

app = FastAPI(lifespan=lifespan)
app.include_router(router=song_router)

if __name__ == "__main__":
    host_ip = icecast_address.split(":")[0]
    uvicorn.run(app, host=host_ip, port=2138)


