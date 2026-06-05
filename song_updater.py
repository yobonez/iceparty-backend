import glob
import time

import mutagen
import requests
import sys
import shutil
import os
import base64

import radio_config

import logging

config = radio_config.get_config()

logger = logging.getLogger(__name__)

cache_dir = config["cache-dir"]
icecast_admin_creds = config["icecast-admin"]
icecast_address = config["icecast-address"]

stream_start = float(time.time())

def get_stream_time():
	return float(time.time()) - stream_start

def update_stream_title(new_title, mountpoint_name):
	creds_bytes = icecast_admin_creds.encode('ascii')
	base64_auth_enc = base64.b64encode(creds_bytes)
	base64_auth = base64_auth_enc.decode('ascii')

	retry_val = 0

	status_code = 0
	headers = {'authorization': 'Basic {}'.format(base64_auth)}
	url = "http://{}/admin/metadata.xsl?song={}&mount=%2F{}&mode=updinfo&charset=UTF-8".format(icecast_address, new_title, mountpoint_name)

	while status_code != 200:
		if retry_val > 0:
			logger.info(f"[{mountpoint_name}] Couldn't update the song info.")
		if 0 < retry_val <= 5:
			logger.info("Retries: {}/5".format(retry_val))
			retry_val = retry_val + 1

		time.sleep(0.5)
		r = requests.get(url, headers=headers)
		status_code = r.status_code

		if status_code == 200:
			logger.info(f"[{mountpoint_name}] Successfully updated stream title.")
			break

def search_and_apply_external_cover(file, mountpoint_name):
	found = False
	destination_image = str(os.path.join(cache_dir, mountpoint_name, "cover.png"))

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
			logger.info(f"[external ({mountpoint_name})] Found external image cover for the song.")
			shutil.copy(file_name, destination_image)
			found = True
			break

	if not found:
		shutil.copy("no-cover.png", destination_image)
		logger.info(f"[external({mountpoint_name})] Couldn't find the image cover")


def set_song_cover(file, mountpoint_name):
	destination_image = str(os.path.join(cache_dir, mountpoint_name, "cover.png"))

	try:
		audio = mutagen.File(file)

		if audio is None:
			logger.error(f"Unsupported or corrupted audio file: {file}")

		cover_data = None

		if hasattr(audio, 'pictures') and audio.pictures:
			logger.info(f"[flac Pictures ({mountpoint_name})] Found FLAC Picture block.")
			cover_data = audio.pictures[0].data

		elif hasattr(audio, 'tags') and audio.tags:
			for key in audio.tags.keys():
				if key.startswith("APIC:"):
					logger.info(f"[mp3 APIC ({mountpoint_name})] Found image cover under key: {key}")
					cover_data = audio.tags[key].data
					break

		if cover_data:
			with open(destination_image, "wb") as coverfile:
				coverfile.write(cover_data)
				coverfile.close()
			logger.info(f"[{mountpoint_name}] Successfully changed cover art to {destination_image}")

		else:
			logger.info(f"[flac Pictures / mp3 APIC ({mountpoint_name})] Couldn't find the image cover.")
			search_and_apply_external_cover(file, mountpoint_name)


	except:
		logger.info(f"[flac Pictures / mp3 APIC ({mountpoint_name})] Couldn't find the image cover.")
		search_and_apply_external_cover(file, mountpoint_name)

def title_updater_start(files, songs, mountpoint_name, proc):

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
					update_stream_title(entry[1], mountpoint_name)
					set_song_cover(files[indexx - 1], mountpoint_name)

					current_song = entry[1] #idented test
					logger.info("Current song {}".format(current_song))
			else:
				break

			poll = proc.poll()
			time.sleep(1)

		if poll is not None:
			sys.exit("FFmpeg process died")

