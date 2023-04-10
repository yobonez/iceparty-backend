# Iceparty-backend

This program requires setting up your own [icecast](https://icecast.org/) server.

## Usage 

`python3 radio_main.py mountpoint-name`

Arguments:
- `mountpoint-name` you can use whatever name you want, but it must match your song folder's name specififed in `radio-root` directory.

## Config

When you run this program for the first time, it will generate this config:

```// Credentials to icecast admin interface (user:password)
icecast-admin = myadmin:password
// Credentials to icecast source (do not use dollar signs in passwords, wontfix escaping them)
icecast-source = mysource:password
// Provide an address for your icecast server, where the audio will be streamed (without http:// and /mountpoint_name)
icecast-address = 192.168.0.1:2137  //example address
// Your root directory for radio mountpoints with songs in them (directory name must end with slash)
radio-root = /your/dir/with/songs/
// Webiste root directory (directory name must end with slash)
web-root = /your/dir/iceparty/
```

If your web-root path is custom (for example its your home folder), you must link it inside
/usr/share/icecast2/web/
Example: 
`sudo ln -s /home/someuser/iceparty /usr/share/icecast2/web/iceparty`

## How does it work?

When program is running, it will reach for your songs folder named after ```mountpoint-name``` (specified in ```radio-root``` in config),
then create a playlist and fire up an icecast mountpoint, then start updating titles and thumbnails for the website.

## Covers of songs downloaded from spotify

To download spotify songs, you can use [Savify](https://github.com/LaurenceRawlings/savify) or some other tool available online.
Songs downloaded from Spotify already have cover images inside them. 

## Thumbnails for songs downloaded from youtube

For youtube you can use yt-dlp, but with extra option that will additionally download a
youtube thumbnail with the same filename as the song (but as image).

Example:

Song with thumbnail

```yt-dlp --extract-audio --audio-format mp3 --write-thumbnail https://www.youtube.com/watch?v=zSwcTiurwwk```

Just thumbnail

```yt-dlp --write-thumbnail --skip-download https://www.youtube.com/watch?v=zSwcTiurwwk```
