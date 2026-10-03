import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Music Pipeline V2 API on Render is running!"}), 200

@app.route("/download", methods=["POST"])
def trigger_download():
    data = request.get_json() or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Placeholder for yt-dlp + Drive upload logic
    return jsonify({"status": "received", "url": url}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)