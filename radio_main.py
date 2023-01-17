import songupdater2
import mutagen
import os
import random
import sys
import subprocess
import time

radio_rootdir = "/home/bonzo/share/priv_files/radio/"
mountpoint = ""
mountpoint_path = ""
icecast_mountpoint = ""

lines = []

def get_file_length(file):
    return file.info.length

def get_files_and_shuffle(rootdir):
    for root, subdirs, files in os.walk(rootdir):
            for name in files:
                if os.path.splitext(name)[1] == ".mp3":
                    filepath = os.path.join(root, name)
                    lines.append(filepath)
                
    random.shuffle(lines)

def prepare_files(rootdir):
    ret_songs = []
    global_duration = 0
    
    af = open(os.path.join(rootdir, "audiofiles.txt"), "a+")

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No endpoint specified")
        exit(1)

    
    mountpoint = sys.argv[1]
    mountpoint_path = os.path.join(radio_rootdir, mountpoint)
    audiofiles_path = os.path.join(mountpoint_path, "audiofiles.txt")

    icecast_mountpoint = "icecast://source:\$icesource\$@192.168.1.2:2139/{}".format(mountpoint)

    remove_prev_files(mountpoint_path)
    get_files_and_shuffle(mountpoint_path)
    songs = prepare_files(mountpoint_path)

    #os.system("ffmpeg -re -f concat -safe 0 -i {} -c:a libmp3lame -ar 44100 -ac 2 -vn -f mp3 -map_metadata 0 -content_type 'audio/mpeg' {} &".format(audiofiles_path, icecast_mountpoint))

    subprocess.Popen("ffmpeg -re -f concat -safe 0 -i {} -c:a libmp3lame -ar 44100 -ac 2 -vn -f mp3 -map_metadata 0 -content_type 'audio/mpeg' {}".format(audiofiles_path, icecast_mountpoint), shell=True, start_new_session=True, stderr=subprocess.STDOUT)
    time.sleep(4)
    songupdater2.title_updater_start(songs, mountpoint)

    

