import glob
import time
import requests
import sys
import shutil
import os
from mutagen.id3 import ID3, ID3NoHeaderError
import base64

import radio_config

import logging

config = radio_config.get_config()

logger = logging.getLogger(__name__)

web_rootdir = config["web-root"]
icecast_admin_creds = config["icecast-admin"]
icecast_address = config["icecast-address"]

stream_start = float(time.time())

def get_stream_time():
	return float(time.time()) - stream_start

def update_stream_title(new_title, mountpoint):
	creds_bytes = icecast_admin_creds.encode('ascii')
	base64_auth_enc = base64.b64encode(creds_bytes)
	base64_auth = base64_auth_enc.decode('ascii')

	retry_val = 0

	status_code = 0
	headers = {'authorization': 'Basic {}'.format(base64_auth)}
	url = "http://{}/admin/metadata.xsl?song={}&mount=%2F{}&mode=updinfo&charset=UTF-8".format(icecast_address, new_title, mountpoint)

	while status_code != 200:
		if retry_val > 0:
			logger.info("Couldn't update the song info.")
		if 0 < retry_val <= 5:
			logger.info("Retries: {}/5".format(retry_val))
			retry_val = retry_val + 1

		time.sleep(0.5)
		r = requests.get(url, headers=headers)
		status_code = r.status_code

		if status_code == 200:
			logger.info("Successfully updated stream title.")
			break

def search_and_apply_external_cover(file, mountpoint):
	found = False
	destination_image = "{}img/cover-{}.png".format(web_rootdir, mountpoint)

	possible_cover_names = [file.split(".")[0] + ".png"] # songside cover

	for extension in ["*.png", "*.jpg", "*.jpeg"]:
		full_path = file.split("/")
		full_path.remove(full_path[-1])

		album_path = os.path.join(*full_path)
		album_path = "/" + str(album_path)

		file_names = glob.glob(pathname=extension, root_dir=album_path)

		if len(file_names) == 0:
			continue

		possible_cover_names.append(str(os.path.join(album_path, file_names[0])))

	for file_name in possible_cover_names:
		logger.info("Trying {}".format(file_name))
		if os.path.exists(file_name):
			logger.info("[external] Found external image cover for the song.")
			shutil.copy(file_name, destination_image)
			found = True
			break

	if not found:
		shutil.copy("no-cover.png", destination_image)
		logger.info("[external] Couldn't find the image cover")


def set_song_cover(file, mountpoint):
	destination_image = "{}img/cover-{}.png".format(web_rootdir, mountpoint)

	try:
		id3_data = ID3(file)

		if "APIC:Album cover" in id3_data:
			logger.info("Found ID3 image cover for the song.")
			cover = id3_data["APIC:Album cover"].data
			with open(destination_image, "wb") as coverfile:
				coverfile.write(cover)
				coverfile.close()
		else:
			logger.info("[ID3] Couldn't find the image cover.")
			search_and_apply_external_cover(file, mountpoint)


	except ID3NoHeaderError:
		logger.info("[ID3-Exception] Couldn't find the image cover.")
		search_and_apply_external_cover(file, mountpoint)

def title_updater_start(files, songs, mountpoint, proc):

	indexx = 0
	songs.sort(reverse=False, key=lambda x: int(x[0]))

	current_song = None

	for entry in songs:
		indexx += 1 # ahead

		next_song_start = float(songs[indexx][0])
		# ^ TODO: fix IndexError when trying to get last (or before last?) song

		donotsend = False

		poll = proc.poll()

		while poll is None:
			current_time_seconds = get_stream_time()
			if entry[1] == current_song:
				donotsend = True
			if current_time_seconds <= next_song_start:
				if not donotsend:
					update_stream_title(entry[1], mountpoint)
					set_song_cover(files[indexx - 1], mountpoint)

					current_song = entry[1] #idented test
					logger.info("Current song {}".format(current_song))
			else:
				break

			poll = proc.poll()
			time.sleep(1)

		if poll is not None:
			sys.exit("FFmpeg process died")

