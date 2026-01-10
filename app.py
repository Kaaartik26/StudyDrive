import os
import shutil
import stat
import json
import time
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, redirect, session
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from auth import auth_bp, login_required, admin_required

# ------------------ App Config ------------------

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY not set in environment")

UPLOAD_FOLDER = "uploads"
META_FILE = "file_meta.json"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXTENSIONS = {"txt", "c", "cpp", "py", "java", "md", "pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register auth blueprint
app.register_blueprint(auth_bp)


# ------------------ Helpers ------------------

def load_metadata():
    if not os.path.exists(META_FILE):
        return {"folders": [], "files": []}
    with open(META_FILE, "r") as f:
        return json.load(f)


def save_metadata(data):
    with open(META_FILE, "w") as f:
        json.dump(data, f, indent=2)


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------ DASHBOARDS ------------------

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    metadata = load_metadata()
    return render_template("admin_dashboard.html", folders=metadata["folders"])


@app.route("/dashboard")
@login_required
def user_dashboard():
    metadata = load_metadata()
    return render_template("user_dashboard.html", folders=metadata["folders"])


# ------------------ ADMIN: CREATE FOLDER ------------------

@app.route("/admin/create-folder", methods=["POST"])
@admin_required
def create_folder():
    folder_name = secure_filename(request.form.get("folder_name"))

    if not folder_name:
        return jsonify({"error": "Folder name required"}), 400

    metadata = load_metadata()

    if folder_name in metadata["folders"]:
        return jsonify({"error": "Folder exists"}), 400

    os.makedirs(os.path.join(UPLOAD_FOLDER, folder_name), exist_ok=True)
    metadata["folders"].append(folder_name)
    save_metadata(metadata)

    return jsonify({"message": "Folder created"})


# ------------------ ADMIN: DELETE FOLDER ------------------

@app.route("/admin/delete-folder", methods=["POST"])
@admin_required
def delete_folder():
    folder_name = request.form.get("folder_name")

    metadata = load_metadata()

    if folder_name not in metadata["folders"]:
        return jsonify({"error": "Folder not found"}), 404

    path = os.path.join(UPLOAD_FOLDER, folder_name)

    def handle_remove_error(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(path, onerror=handle_remove_error)

    metadata["folders"].remove(folder_name)
    metadata["files"] = [
        f for f in metadata["files"] if f["folder"] != folder_name
    ]
    save_metadata(metadata)

    return jsonify({"message": "Folder deleted"})


# ------------------ FILE UPLOAD ------------------

@app.route("/upload/<folder>", methods=["POST"])
@login_required
def upload_file(folder):
    metadata = load_metadata()

    if folder not in metadata["folders"]:
        return jsonify({"error": "Folder not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    original = secure_filename(file.filename)
    stored = f"{int(time.time())}_{original}"

    save_path = os.path.join(UPLOAD_FOLDER, folder, stored)
    file.save(save_path)

    metadata["files"].append({
        "stored_filename": stored,
        "original_filename": original,
        "folder": folder,
        "timestamp": datetime.now().isoformat(),
        "size": os.path.getsize(save_path),
        "uploaded_by": session.get("role")
    })

    save_metadata(metadata)
    return jsonify({"message": "Uploaded"})


# ------------------ FILE LIST ------------------

@app.route("/files/<folder>")
@login_required
def list_files(folder):
    metadata = load_metadata()

    if folder not in metadata["folders"]:
        return jsonify({"error": "Folder not found"}), 404

    return jsonify({
        "files": [f for f in metadata["files"] if f["folder"] == folder]
    })


# ------------------ DOWNLOAD ------------------

@app.route("/download/<folder>/<filename>")
@login_required
def download_file(folder, filename):
    return send_from_directory(
        os.path.join(UPLOAD_FOLDER, folder),
        filename,
        as_attachment=True
    )


# ------------------ ADMIN: DELETE FILE ------------------

@app.route("/admin/delete-file", methods=["POST"])
@admin_required
def delete_file():
    data = request.get_json()
    stored = data.get("stored_filename")
    folder = data.get("folder")

    metadata = load_metadata()

    entry = next(
        (f for f in metadata["files"]
         if f["stored_filename"] == stored and f["folder"] == folder),
        None
    )

    if not entry:
        return jsonify({"error": "File not found"}), 404

    path = os.path.join(UPLOAD_FOLDER, folder, stored)
    if os.path.exists(path):
        os.remove(path)

    metadata["files"].remove(entry)
    save_metadata(metadata)

    return jsonify({"message": "File deleted"})


# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)
