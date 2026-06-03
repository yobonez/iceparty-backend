import signal
import time
import requests
import sys
import shutil
import os
from mutagen.id3 import ID3, ID3NoHeaderError
import base64

import radio_config
from radio_main import finish

config = radio_config.get_config()

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

	response = 0
	headers = {'authorization': 'Basic {}'.format(base64_auth)}
	url = "http://{}/admin/metadata.xsl?song={}&mount=%2F{}&mode=updinfo&charset=UTF-8".format(icecast_address, new_title, mountpoint)
	
	while response != 200:
		time.sleep(0.5)
		r = requests.get(url, headers=headers)
		response = r.status_code

	return r

def set_song_cover(file, mountpoint):
	destination_image = "{}img/cover-{}.png".format(web_rootdir, mountpoint)

	try:
		id3_data = ID3(file)

		if "APIC:Album cover" in id3_data:
			cover = id3_data["APIC:Album cover"].data
			with open("{}img/cover-{}.png".format(web_rootdir, mountpoint), "wb") as coverfile:
				coverfile.write(cover)
				coverfile.close()
		else:
			external_cover_file_options = [file.split(".")[0] + ".png", "cover.png", "Cover.png"]

			for possible_cover_file in external_cover_file_options:

				if os.path.exists(possible_cover_file):
					shutil.copy(possible_cover_file, destination_image)
				else:
					shutil.copy("no-cover.png", destination_image)
	except ID3NoHeaderError:
		shutil.copy("no-cover.png", destination_image)

def title_updater_start(files, songs, mountpoint, proc):
	try:
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
					current_song = entry[1]
				else:
					break

				poll = proc.poll()
				time.sleep(1)

			if poll is not None:
				sys.exit("FFmpeg process died")

	except KeyboardInterrupt:
		finish(proc)

