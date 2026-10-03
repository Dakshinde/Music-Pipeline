import os
import json
import tempfile
import static_ffmpeg
from flask import Flask, jsonify, request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import yt_dlp

# Automatically download & expose static ffmpeg binaries on boot
static_ffmpeg.add_paths()

app = Flask(__name__)

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable missing")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build("drive", "v3", credentials=creds)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Music Pipeline V2 API is live!"}), 200

@app.route("/test-drive", methods=["GET"])
def test_drive():
    try:
        service = get_drive_service()
        folder_id = os.environ.get("DRIVE_FOLDER_ID")
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name)"
        ).execute()
        files = results.get("files", [])
        return jsonify({"status": "success", "files_found": len(files)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/download", methods=["POST"])
def process_download():
    data = request.get_json() or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    folder_id = os.environ.get("DRIVE_FOLDER_ID")
    if not folder_id:
        return jsonify({"error": "DRIVE_FOLDER_ID not set"}), 500

    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': 'ba/b',  # Best audio, fallback to best single format
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }],
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'web']
                }
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                song_title = info.get('title', 'Unknown Title')
                
                # Locate extracted mp3 file in working temp dir
                downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                if not downloaded_files:
                    downloaded_files = os.listdir(temp_dir)
                
                if not downloaded_files:
                    return jsonify({"error": "Audio conversion failed"}), 500
                
                file_path = os.path.join(temp_dir, downloaded_files[0])

            service = get_drive_service()
            file_metadata = {
                'name': f"{song_title}.mp3",
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, mimetype='audio/mpeg', resumable=True)
            
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name'
            ).execute()

            return jsonify({
                "status": "success",
                "message": "Song downloaded and uploaded to Google Drive!",
                "title": song_title,
                "drive_file_id": uploaded_file.get('id')
            }), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)