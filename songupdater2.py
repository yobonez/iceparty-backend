import time
import requests
import sys

stream_start = float(time.time())

def get_stream_time():
	return float(time.time()) - stream_start

def update_stream_title(new_title, mountpoint):
	headers = {'authorization': 'Basic YWRtaW46JGljZWFkbWluJA=='}
	url = "http://192.168.1.2:2139/admin/metadata.xsl?song={}&mount=%2F{}&mode=updinfo&charset=UTF-8".format(new_title, mountpoint)
	r = requests.get(url, headers=headers)

	return r

def title_updater_start(songs, mountpoint):
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
				current_song = entry[1]
			else:
				break
			time.sleep(1)

