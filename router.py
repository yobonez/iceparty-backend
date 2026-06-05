import os

from fastapi import APIRouter
from starlette.responses import FileResponse

from radio_config import get_config

song_router = APIRouter(tags=["SongDetailGetter"])

config = get_config()
song_router.cache_dir = config["cache-dir"]

@song_router.get(
    "/radio/{mountpoint_name}/cover",
    summary="Get song cover image.",
    responses= {
        200: {
            "content": {"image/png": {}}
        }
    }
)
async def get_song_cover(mountpoint_name: str):
    file_path = os.path.join(song_router.cache_dir, mountpoint_name, "cover.png")

    return FileResponse(path=file_path, media_type="image/png")
