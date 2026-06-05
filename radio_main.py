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


logger = logging.getLogger(__name__)
logging.basicConfig(filename='radio.log', level=logging.NOTSET)

config = radio_config.get_config()

radio_rootdir = config["radio-root"]
icecast_source_creds = config["icecast-source"]
icecast_address = config["icecast-address"]
web_root = config["web-root"]

lines = []

mountpoint = sys.argv[1]
mountpoint_path = os.path.join(radio_rootdir, mountpoint)
audiofiles_path = os.path.join(web_root, "audiofiles.txt")
icecast_mountpoint = "icecast://{}@{}/{}".format(icecast_source_creds, icecast_address, mountpoint)

def error_handler(exc_type, exc_value, exc_tb):
    # traceback.format_exception(exc_type, exc_value, exc_tb)
    logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_tb))
sys.excepthook = error_handler

def get_file_length(file):
    return file.info.length

def get_files_and_shuffle(rootdir):
    for root, subdirs, files in os.walk(rootdir):
            for name in files:
                if os.path.splitext(name)[1] == ".mp3":
                    filepath = os.path.join(root, name)
                    lines.append(filepath)

                
    random.shuffle(lines)

def prepare_files(webrootdir):
    ret_songs = []
    global_duration = 0
    
    af = open(os.path.join(webrootdir, "audiofiles.txt"), "a+")

    for filepath in lines:
        filename = os.path.basename(filepath)
        songname = os.path.splitext(filename)[0]
        duration = get_file_length(mutagen.File(filepath))

        ret_songs.append((global_duration, songname))
        af.write("file '{}'\n".format(filepath))

        global_duration += duration

    af.close()

    return ret_songs

def remove_prev_files(rootdir):
    audiofiles = os.path.join(rootdir, "audiofiles.txt")
    if os.path.exists(audiofiles):
        os.remove(audiofiles)

def graceful_shutdown(proc, task):
    logger.info("Shutting down everything...")

    task.cancel()

    if proc.poll() is None:
        logger.info("Cleaning up ffmpeg subprocess...")
        proc.terminate()
        proc.wait()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Preparing songs...")

    remove_prev_files(web_root)
    get_files_and_shuffle(mountpoint_path)
    songs = prepare_files(web_root)

    cmd = [
        "ffmpeg", "-re", "-f", "concat", "-safe", "0", "-i", audiofiles_path,
        "-c:a", "libmp3lame", "-ar", "44100", "-ac", "2", "-vn", "-f", "mp3",
        "-map_metadata", "0", "-content_type", "audio/mpeg", icecast_mountpoint
    ]

    logger.info("Starting ffmpeg...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    logger.info("Starting song updater...")
    updater_task = asyncio.create_task(
        asyncio.to_thread(song_updater.title_updater_start, lines, songs, mountpoint, proc)
    )

    def handle_task_result(task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Song updater task crashed!", exc_info=e)
            graceful_shutdown(proc, updater_task)

    updater_task.add_done_callback(handle_task_result)

    yield

    graceful_shutdown(proc, updater_task)

app = FastAPI(lifespan=lifespan)
app.include_router(router=song_router)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("No endpoint specified")
        exit(1)

    host_ip = icecast_address.split(":")[0]
    uvicorn.run(app, host=host_ip, port=2138)


