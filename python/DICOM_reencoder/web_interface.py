#!/usr/bin/env python3
#
# web_interface.py
# Dicom-Tools-py
#
# Serves the Flask-based web UI for uploading, previewing, anonymizing, and validating DICOM files.
#
# Thales Matheus Mendonça Santos - November 2025

"""Flask-powered web interface for the DICOM toolkit."""

import argparse
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .anonymize_dicom import anonymize_dicom
from .core import calculate_statistics, frame_to_png_bytes, load_dataset, summarize_metadata
from .validate_dicom import DicomValidator


BASE_DIR = Path(__file__).parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "web_templates"),
    static_folder=str(BASE_DIR / "web_static"),
)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = tempfile.mkdtemp(prefix="dicom_web_")
app.config["ALLOWED_EXTENSIONS"] = {"dcm", "dicom"}


def allowed_file(filename: str) -> bool:
    # Basic extension guard; deeper checks happen when pydicom parses the upload
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def _uploaded_path(filename: str) -> Path:
    return Path(app.config["UPLOAD_FOLDER"]) / secure_filename(filename)


def _load_uploaded(filename: str):
    path = _uploaded_path(filename)
    if not path.exists():
        return None, (jsonify({"error": "File not found"}), 404)
    try:
        # Use the shared loader so the web API matches CLI behavior
        return load_dataset(path, force=True), None
    except Exception as exc:  # pragma: no cover - surfaced to client
        return None, (jsonify({"error": str(exc)}), 400)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(file.filename)
    filepath = _uploaded_path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    file.save(filepath)

    dataset, error = _load_uploaded(filename)
    if error:
        filepath.unlink(missing_ok=True)
        return error

    summary = summarize_metadata(dataset)
    has_pixel_data = "PixelData" in dataset

    return jsonify({
        "success": True,
        "info": summary,
        "filename": filename,
        "has_pixel_data": has_pixel_data,
    })


@app.route("/api/metadata/<filename>")
def get_metadata(filename: str):
    dataset, error = _load_uploaded(filename)
    if error:
        return error
    return jsonify(summarize_metadata(dataset))


@app.route("/api/image/<filename>")
def get_image(filename: str):
    dataset, error = _load_uploaded(filename)
    if error:
        return error
    if "PixelData" not in dataset:
        return jsonify({"error": "No pixel data in file"}), 400

    png_bytes = frame_to_png_bytes(dataset)
    png_bytes.seek(0)
    return send_file(png_bytes, mimetype="image/png", download_name=f"{filename}.png")


@app.route("/api/stats/<filename>")
def get_pixel_stats(filename: str):
    dataset, error = _load_uploaded(filename)
    if error:
        return error
    if "PixelData" not in dataset:
        return jsonify({"error": "No pixel data in file"}), 400

    stats = calculate_statistics(dataset.pixel_array if dataset.pixel_array.ndim == 2 else dataset.pixel_array[0])
    return jsonify(stats)


@app.route("/api/validate/<filename>")
def validate_file(filename: str):
    dataset, error = _load_uploaded(filename)
    if error:
        return error

    validator = DicomValidator()
    is_valid = validator.validate_dataset(dataset, display=False)
    return jsonify({
        "valid": is_valid,
        "errors": validator.errors,
        "warnings": validator.warnings,
        "info": validator.info,
    })


@app.route("/api/anonymize/<filename>", methods=["POST"])
def anonymize_file(filename: str):
    filepath = _uploaded_path(filename)
    if not filepath.exists():
        return jsonify({"error": "File not found"}), 404

    output_filename = f"anon_{filename}"
    output_filepath = _uploaded_path(output_filename)
    try:
        anonymize_dicom(filepath, output_filepath)
        return jsonify({"success": True, "filename": output_filename})
    except Exception as exc:  # pragma: no cover - surfaced to client
        return jsonify({"error": str(exc)}), 500


@app.route("/api/download/<filename>")
def download_file(filename: str):
    path = _uploaded_path(filename)
    if not path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True, download_name=filename)


def main():
    parser = argparse.ArgumentParser(description="DICOM Tools Web Interface")
    parser.add_argument("-H", "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Port to bind to (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print("\n" + "=" * 72)
    print("DICOM Tools Web Interface")
    print("=" * 72 + "\n")
    print(f"Serving on http://{args.host}:{args.port}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
