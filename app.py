import os
import shutil
import stat
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "super-secret-key"  # needed for sessions

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'txt', 'c', 'cpp', 'py', 'java', 'md', 'pdf'}

ADMIN_PASSWORD = "admin123"  # change later

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ------------ helpers -------------

def load_metadata():
    try:
        with open('file_meta.json', 'r') as f:
            return json.load(f)
    except:
        return {"folders": [], "files": []}


def save_metadata(data):
    with open('file_meta.json', 'w') as f:
        json.dump(data, f, indent=2)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------ role selection -------------

@app.route("/")
def home():
    return redirect("/role")


@app.route("/role")
def role():
    return render_template("role.html")


# ------------ ADMIN LOGIN -------------

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect("/admin")

        return render_template("admin_login.html", error="Wrong password")

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/role")


# ------------ ADMIN DASHBOARD -------------

@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect("/role")

    metadata = load_metadata()
    return render_template("admin_dashboard.html", folders=metadata["folders"])


# ------------ USER PAGE -------------

@app.route("/user")
def user_page():
    metadata = load_metadata()
    return render_template("user.html", folders=metadata["folders"])


# ------------ ADMIN: CREATE FOLDER -------------

@app.route("/create_folder", methods=["POST"])
def create_folder():
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403

    folder_name = secure_filename(request.form.get("folder_name"))

    metadata = load_metadata()

    if folder_name in metadata["folders"]:
        return jsonify({"error": "Folder exists"}), 400

    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], folder_name), exist_ok=True)
    metadata["folders"].append(folder_name)
    save_metadata(metadata)

    return jsonify({"message": "Folder created"})


# ------------ ADMIN: DELETE FOLDER -------------

@app.route("/delete_folder", methods=["POST"])
def delete_folder():
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403

    folder_name = request.form.get("folder_name")
    if not folder_name:
        return jsonify({"error": "Folder name required"}), 400

    meta = load_metadata()

    if folder_name not in meta["folders"]:
        return jsonify({"error": "Folder not found"}), 404

    path = os.path.join(app.config["UPLOAD_FOLDER"], folder_name)

    def handle_remove_error(func, path, exc):
        # make read-only things writable and retry
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            print("force-delete failed:", e)

    # 🚀 FORCE DELETE EVEN IF LOCKED / READONLY
    shutil.rmtree(path, onerror=handle_remove_error)

    # update metadata
    meta["folders"].remove(folder_name)
    meta["files"] = [f for f in meta["files"] if f["folder"] != folder_name]
    save_metadata(meta)

    return jsonify({"message": "Folder deleted"})



# ------------ FILE UPLOAD (ADMIN + USER) -------------

@app.route("/upload/<folder>", methods=["POST"])
def upload_file(folder):
    metadata = load_metadata()

    if folder not in metadata["folders"]:
        return jsonify({"error": "Folder not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    original = secure_filename(file.filename)
    stored = f"{int(time.time())}_{original}"

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, stored)
    file.save(save_path)

    metadata["files"].append({
        "stored_filename": stored,
        "original_filename": original,
        "folder": folder,
        "timestamp": datetime.now().isoformat(),
        "size": os.path.getsize(save_path)
    })

    save_metadata(metadata)

    return jsonify({"message": "Uploaded"})


# ------------ LIST FILES -------------

@app.route("/files/<folder>")
def files(folder):
    meta = load_metadata()

    if folder not in meta["folders"]:
        return jsonify({"error": "Folder not found"}), 404

    return jsonify({
        "files": [f for f in meta["files"] if f["folder"] == folder]
    })


# ------------ DOWNLOAD -------------

@app.route("/download/<folder>/<fname>")
def download(folder, fname):
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], folder), fname, as_attachment=True)


# ------------ ADMIN DELETE FILE -------------

@app.route("/delete_file", methods=["POST"])
def delete_file():
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403

    data = request.get_json()
    stored = data.get("stored_filename")
    folder = data.get("folder")

    meta = load_metadata()

    entry = next((f for f in meta["files"] if f["stored_filename"] == stored and f["folder"] == folder), None)

    if not entry:
        return jsonify({"error": "File not found"}), 404

    path = os.path.join(app.config["UPLOAD_FOLDER"], folder, stored)

    if os.path.exists(path):
        os.remove(path)

    meta["files"].remove(entry)
    save_metadata(meta)

    return jsonify({"message": "File deleted"})


if __name__ == "__main__":
    app.run(debug=True)
