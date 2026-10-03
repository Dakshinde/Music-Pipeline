import os
import json
import tempfile
import glob
import traceback
import static_ffmpeg
from flask import Flask, jsonify, request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import yt_dlp
import base64

# Register static ffmpeg binaries on container boot
static_ffmpeg.add_paths()

app = Flask(__name__)

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable is missing")
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
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get("files", [])
        return jsonify({"status": "success", "files_found": len(files)}), 200
    except BaseException as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/download", methods=["POST"])
def process_download():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    folder_id = os.environ.get("DRIVE_FOLDER_ID")
    if not folder_id:
        return jsonify({"error": "DRIVE_FOLDER_ID environment variable not set"}), 500

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_path = None
    
            raw_cookies_b64 = os.environ.get("YOUTUBE_COOKIES")
            if raw_cookies_b64:
                cookie_path = os.path.join(temp_dir, "cookies.txt")
                try:
                    # Handle both plain base64 and potential raw string fallback
                    decoded_cookies = base64.b64decode(raw_cookies_b64.strip()).decode("utf-8")
                except Exception:
                    decoded_cookies = raw_cookies_b64

                with open(cookie_path, "w", encoding="utf-8") as f:
                    f.write(decoded_cookies)

            ydl_opts = {
                'format': 'ba/ba*/bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'noplaylist': True,
                'nocheckcertificate': True,
            }

            if cookie_path and os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                song_title = info.get('title', 'Unknown Title')

            extracted_files = glob.glob(os.path.join(temp_dir, "*"))
            if not extracted_files:
                return jsonify({"status": "error", "message": "No audio file created by yt-dlp"}), 500

            mp3_files = [f for f in extracted_files if f.endswith('.mp3')]
            target_file = mp3_files[0] if mp3_files else extracted_files[0]

            service = get_drive_service()
            file_metadata = {
                'name': f"{song_title}.mp3",
                'parents': [folder_id]
            }
            media = MediaFileUpload(target_file, mimetype='audio/mpeg', resumable=True)

            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name',
                supportsAllDrives=True
            ).execute()

            return jsonify({
                "status": "success",
                "message": "Song downloaded and uploaded to Google Drive!",
                "title": song_title,
                "drive_file_id": uploaded_file.get('id')
            }), 200

    except BaseException as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)