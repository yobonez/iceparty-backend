import time
import requests
import sys
import shutil
import os
from mutagen.id3 import ID3


stream_start = float(time.time())

def get_stream_time():
	return float(time.time()) - stream_start

def update_stream_title(new_title, mountpoint):
	response = 0
	headers = {'authorization': 'Basic UR_KEY'}
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
		with open("/home/bonzo/radiosite/img/cover-{}.png".format(mountpoint), "wb") as coverfile:
			coverfile.write(cover)
			coverfile.close()
	else:
		external_cover_file = file.split(".")[0] + ".jpg"
		destination_image = "/home/bonzo/radiosite/img/cover-{}.png".format(mountpoint)
		if os.path.exists(external_cover_file):
			shutil.copy(external_cover_file, destination_image)
		else:
			shutil.copy("no-cover.png", destination_image)

		

def title_updater_start(files, songs, mountpoint):
	indexx = 0
	songs.sort(reverse=False, key=lambda x: int(x[0]))

	current_song = None

	for entry in songs:
		indexx += 1 # ahead

		current_time_seconds = get_stream_time()

		curr_song_start = float(songs[indexx - 1][0])
		next_song_start = float(songs[indexx][0])

		donotsend = False
		while True:
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
			time.sleep(1)

