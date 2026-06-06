# Music Pipeline

## What does this project do?

Personlaize music pipeline

- Takes Youtube URL make sure its public
- Uses yt_dlp to download the mp3
- Transfer it to your phone via GSConnect / KDEConnect

## What problem does it solve?

This project is for solving the headache to copy paste urls from youtube and downlaoding it via third party website of youtube to mp3 and then sending it to pc via telegram or whatsapp since i use linux-ubuntu i have option of KDE connect and i can transfer

**I want to Automate this process**

## What stack does it use?

- yt_dlp : to convert youtube urls to mp3
- I run commands using subprocess library 

## Setup for python
- create a folder and clone this repo.
- create virtual environment of python (.venv) (google how to create one its simple two commands)
- python3 -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt.
- create your correct urls.txt and .env file as per instruction in urls.example.txt and .env.example.
- python run now "python self.py".
- if any error use AI to figure it out or email me.

## Setup for Automatic script running

We use cron_jobs for this part

**Steps**
- run "EDITOR="code --wait" crontab -e" to write the corn commands i prefer running this command in vscode terminal since editing the code is easy
- write something like this in end "*/5 * * * * cd /your/project/path && /your/project/path/.venv/bin/python self.py" 
- why "*/5 * * * * cd path of your directory where you clone the repo && write the path of python file with its .venv file"
- save ctrl + s and close the app now the scrpit will run every 5min in your device when the device is up
- for more information google this "What is a cron job and how do you set one up on Ubuntu?"

## Known Issues (V1)
- Songs stay in temp folder if phone is disconnected during cron run
- Workaround: run `python self.py` manually when phone is reconnected

**Made with sense by Dakshinde**
