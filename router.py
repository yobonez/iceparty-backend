import os

from fastapi import APIRouter
from starlette.responses import FileResponse

from radio_config import get_config

song_router = APIRouter(tags=["SongDetailGetter"])

config = get_config()
song_router.cache_dir = config["cache-dir"]

@song_router.get(
    "/radio/{mountpoint}/cover",
    summary="Get song cover image.",
    responses= {
        200: {
            "content": {"image/png": {}}
        }
    }
)
async def get_song_cover(mountpoint: str):
    file_path = os.path.join(song_router.cache_dir, "img", "cover-{}.png".format(mountpoint))

    return FileResponse(path=file_path, media_type="image/png")
