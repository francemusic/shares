from flask_cors import CORS
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os, uuid, shutil, json, traceback

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1 GB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

METADATA_FILE = 'metadata.json'
def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(uid, files):
    data = load_metadata()
    data[uid] = {
        "files": files,
        "expires_in_days": 3
    }
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f)

def send_email(from_email, to_email, subject, download_url):
    body = f"""
    <h3>{from_email} has shared files with you via FranceMusic</h3>
    <p>You can download them using the link below:</p>
    <a href="{download_url}">{download_url}</a>
    <p><em>This link will expire in 3 days.</em></p>
    """
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = "shares@francemusic.com"
    msg['To'] = "shares@francemusic.com"
    msg['Bcc'] = to_email

    with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as server:
        server.login("shares@francemusic.com", "Om123shares!!!")
        server.sendmail(
    "shares@francemusic.com",
    [to_email, "shares@francemusic.com"],
    msg.as_string()
)


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")

@app.route("/upload", methods=['POST'])
def upload():
    try:
        print("[INFO] Upload request received")
        from_email = request.form['from_email']
        to_email = request.form['to_email']
        subject = request.form['subject']
        print("[INFO] Emails y asunto recibidos")

        files = request.files.getlist("files")
        print(f"[INFO] Archivos recibidos: {[file.filename for file in files]}")

        uid = str(uuid.uuid4())
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], uid)
        os.makedirs(upload_path, exist_ok=True)
        filenames = []

        for file in files:
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))
            filenames.append(filename)
        print("[INFO] Archivos guardados exitosamente")

        save_metadata(uid, filenames)
        print("[INFO] Metadata guardada")

        base_url = "https://francemusic-files.onrender.com"
        download_url = f"{base_url}/download/{uid}"
        print(f"[INFO] Download URL generado: {download_url}")

        send_email(from_email, to_email, subject, download_url)
        print("[INFO] Correo enviado exitosamente")

        return {"download_url": download_url}

    except Exception as e:
        print("[ERROR] Fallo en /upload:", str(e))
        traceback.print_exc()
        return {"error": str(e)}, 500

@app.route("/download/<uid>", methods=['GET'])
def download(uid):
    path = os.path.join(app.config['UPLOAD_FOLDER'], uid)
    if not os.path.exists(path):
        return "Files not found", 404

    zip_path = shutil.make_archive(path, 'zip', path)
    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

