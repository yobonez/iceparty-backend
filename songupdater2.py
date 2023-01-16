import time
import requests
import sys

if len(sys.argv) < 2:
	print("No mountpoint specified")
	exit(1)

mountpoint = sys.argv[1]

def get_stream_time():
	return float(time.time()) - stream_start

def update_stream_title(new_title):
	headers = {'authorization': 'Basic YWRtaW46JGljZWFkbWluJA=='}
	url = "http://192.168.1.2:2139/admin/metadata.xsl?song={}&mount=%2F{}&mode=updinfo&charset=UTF-8".format(new_title, mountpoint)

	r = requests.get(url, headers=headers)

	return r

songs = []
stream_start = None

with open("/home/bonzo/share/priv_files/radio/{}/start_timestamp".format(mountpoint), "r") as f:
	stream_start = int(f.readline())
	print("Start timestamp: ", stream_start)
	f.close()

with open("/home/bonzo/share/priv_files/radio/{}/entries.txt".format(mountpoint), "r") as f:
	entries = f.readlines()
	for line in entries:
		song = line.strip("\n").split(",")
		songs.append((song[0], song[1]))
	print("Songs loaded.")
	f.close()

indexx = 0
songs.sort(reverse=False, key=lambda x: int(x[0]))

current_song = None

for entry in songs:
	indexx += 1 # ahead

	current_time_seconds = get_stream_time()

	curr_song_start = int(songs[indexx - 1][0])
	next_song_start = int(songs[indexx][0])

	donotsend = False
	while True:
		current_time_seconds = get_stream_time()
		if entry[1] == current_song:
			donotsend = True
		if current_time_seconds <= next_song_start:
			if not donotsend:
				#print("Current song: ", entry)
				req = update_stream_title(entry[1])
#				print(req)
			current_song = entry[1]
		else:
			break
		time.sleep(5)

