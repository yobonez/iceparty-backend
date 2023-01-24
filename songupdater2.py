import time
import requests
import sys
import shutil
import os
from mutagen.id3 import ID3
import base64

import radio_config

config = radio_config.get_config()

web_rootdir = config["web-root"]
icecast_admin_creds = config["icecast-admin"]

stream_start = float(time.time())

def get_stream_time():
	return float(time.time()) - stream_start

def update_stream_title(new_title, mountpoint):
	creds_bytes = icecast_admin_creds.encode('ascii')
	base64_auth_enc = base64.b64encode(creds_bytes)
	base64_auth = base64_auth_enc.decode('ascii')

	response = 0
	headers = {'authorization': 'Basic {}'.format(base64_auth)}
	url = "http://192.168.1.2:2139/admin/metadata.xsl?song={}&mount=%2F{}&mode=updinfo&charset=UTF-8".format(new_title, mountpoint)
	
	while response != 200:
		time.sleep(0.5)
		r = requests.get(url, headers=headers)
		response = r.status_code

	return r

def set_song_cover(file, mountpoint):
	id3_data = ID3(file)

	if "APIC:Album cover" in id3_data:
		cover = id3_data["APIC:Album cover"].data
		with open("{}img/cover-{}.png".format(web_rootdir, mountpoint), "wb") as coverfile:
			coverfile.write(cover)
			coverfile.close()
	else:
		external_cover_file = file.split(".")[0] + ".jpg"
		destination_image = "{}img/cover-{}.png".format(web_rootdir, mountpoint)
		if os.path.exists(external_cover_file):
			shutil.copy(external_cover_file, destination_image)
		else:
			shutil.copy("no-cover.png", destination_image)

		

def title_updater_start(files, songs, mountpoint, proc, config):
	indexx = 0
	songs.sort(reverse=False, key=lambda x: int(x[0]))

	current_song = None

	poll = None

	for entry in songs:
		indexx += 1 # ahead

		current_time_seconds = get_stream_time()

		curr_song_start = float(songs[indexx - 1][0])
		next_song_start = float(songs[indexx][0])

		donotsend = False

		poll = proc.poll()
		if poll is not None:
			sys.exit("FFmpeg process died")

		while poll is None:
			current_time_seconds = get_stream_time()
			if entry[1] == current_song:
				donotsend = True
			if current_time_seconds <= next_song_start:
				if not donotsend:
					req = update_stream_title(entry[1], mountpoint)
					set_song_cover(files[indexx - 1], mountpoint)
				current_song = entry[1]
			else:
				break

			poll = proc.poll()
			if poll is not None:
				sys.exit("FFmpeg process died")
			time.sleep(1)

