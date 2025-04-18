import os
import uuid
import zipfile
from flask import Flask, request, send_file, jsonify, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload():
    try:
        from_email = request.form.get("from_email")
        to_email = request.form.get("to_email")
        subject = request.form.get("subject")
        files = request.files.getlist("files")

        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        uid = str(uuid.uuid4())
        user_folder = os.path.join(UPLOAD_FOLDER, uid)
        os.makedirs(user_folder, exist_ok=True)

        for file in files:
            filename = secure_filename(file.filename)
            file.save(os.path.join(user_folder, filename))

        zip_path = os.path.join(UPLOAD_FOLDER, f"{uid}.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for file in os.listdir(user_folder):
                zipf.write(os.path.join(user_folder, file), arcname=file)

        download_url = request.url_root.strip("/") + url_for("download", uid=uid)
        return jsonify({"download_url": download_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<uid>")
def download(uid):
    zip_path = os.path.join(UPLOAD_FOLDER, f"{uid}.zip")
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)
