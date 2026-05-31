import yt_dlp
import subprocess
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DEVICE=os.getenv("DEVICE")

path = os.getenv("MAIN_FOLDER")

temp_folder_mp3 = os.getenv("TEMP_FOLDER_MP3")
temp_folder = os.getenv("TEMP_FOLDER")


def transfer():
    for i in os.listdir(temp_folder):
        song = os.path.join(temp_folder,i)
        subprocess.run(["gdbus" , "call" , "--session" , "--dest" , "org.gnome.Shell.Extensions.GSConnect" , "--object-path" , DEVICE , "--method" , "org.gtk.Actions.Activate" , "shareFile" , f"[<('file://{song}' , false)>]" , "{}"])
        subprocess.run(["mv" , song ,  path])
    
    

def isconnected():
    task = subprocess.run(["gdbus" , "call" , "--session" , "--dest" , "org.gnome.Shell.Extensions.GSConnect" , "--object-path" , DEVICE , "--method" , "org.freedesktop.DBus.Properties.Get", "org.gnome.Shell.Extensions.GSConnect.Device" , "Connected"], capture_output=True, text=True)
    print(task.stdout)
    if "<true>" in task.stdout:
        print("Connected")
        return True
    else:
        print("Device not connected")
        return False


with open('urls.txt', 'r') as file:
    content = file.readlines()
    for i in content:
        print(i.strip())
        subprocess.run(["yt-dlp" , "-x" , "--audio-format", "mp3" ,  "--yes-playlist" ,  "--audio-quality" , "0" , "-o", temp_folder_mp3, "--download-archive" , "archive.txt", i])


files = os.listdir(temp_folder)

if files:
    const = isconnected()
    if const:
        transfer()
    else:
        with open ('log.txt', 'a') as file:
            file.write(f"Failed to transfer because of connection at {datetime.now()}")
         
         
