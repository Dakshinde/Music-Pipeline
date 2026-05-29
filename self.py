import yt_dlp
import subprocess
path = "/home/dakshhinde/Downloads/Music and Video/%(title)s.mp3"
with open('urls.txt', 'r') as file:
    content = file.readlines()
    for i in content:
        print(i.strip())

        subprocess.run(["yt-dlp" , "-x" , "--audio-format", "mp3" ,  "--yes-playlist" ,  "--audio-quality" , "0" , "-o", path, "--download-archive" , "archive.txt", i])