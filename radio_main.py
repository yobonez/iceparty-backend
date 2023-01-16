import mutagen
import os
import random
import sys

radio_rootdir = "/home/bonzo/share/priv_files/radio/"
mountpoint = ""
mountpoint_path = ""

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
    global_duration = 0
    
    ent = open(os.path.join(rootdir, "PYentries.txt"), "a+")
    af = open(os.path.join(rootdir, "PYaudiofiles.txt"), "a+")

    for filepath in lines:
        filename = os.path.basename(filepath)
        songname = os.path.splitext(filename)[0]
        duration = get_file_length(mutagen.File(filepath))

        ent.write("{},{}\n".format(global_duration, songname))
        af.write("file '{}'\n".format(filepath))

        global_duration += duration


    ent.close()
    af.close()

def remove_prev_files(rootdir):
    entries = os.path.join(rootdir, "PYentries.txt")
    audiofiles = os.path.join(rootdir, "PYaudiofiles.txt")
    if os.path.exists(entries):
        os.remove(entries)
        os.remove(audiofiles)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No endpoint specified")
        exit(1)
    mountpoint = sys.argv[1]
    mountpoint_path = os.path.join(radio_rootdir, mountpoint)

    remove_prev_files(mountpoint_path)
    get_files_and_shuffle(mountpoint_path)
    prepare_files(mountpoint_path)

    

