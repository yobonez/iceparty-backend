import os
import sys

default_config_contents = ["// Credentials to icecast admin interface (write like this: user:password)\n",
                           "icecast-admin = user:password\n",
                           "// Credentials to icecast source (write like this: user:password) (do not use dollar signs in passwords, wontfix escaping them)\n",
                           "icecast-source = source:password\n",
                           "// Provide an address for your icecast server, where the audio will be streamed (without mountpoint name)\n",
                           "icecast-address = \n",
                           "// Your root directory for radio mountpoints with songs in them (directory name ends with slash \"/\" too)\n",
                           "radio-root = \n",
                           "// Webiste root directory (directory name ends with slash \"/\" too)\n",
                           "web-root = \n"]


def get_config():
    entries = dict()
    if os.path.exists("./config.txt"):
        config = open("./config.txt", "r")
        lines = config.readlines()

        for line in lines:
            if line.startswith("//"):
                continue;
            else:
                entry = line.split("=")
                key = entry[0].strip()
                value = entry[1].strip()
                entries[key] = value
                
        config.close()
    else:
        config = open("./config.txt", "w+")
        config.writelines(default_config_contents)
        config.close()
        sys.exit("Fill the \"config.txt\" that was created in this directory, and then run the program.")
       
    return entries