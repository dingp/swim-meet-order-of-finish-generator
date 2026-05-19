#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from flask import Flask, abort, render_template, request, send_file
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PORT = 8000
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "20"))

GENERATORS = {
    "one_event_per_page": {
        "label": "One Event Per Page",
        "script": BASE_DIR / "generate_oof_1evt_1pg.py",
        "output_name": "prefilled_order_of_finish_1evt_1pg.pdf",
    },
    "two_events_per_page": {
        "label": "Two Events Per Page",
        "script": BASE_DIR / "generate_oof_2evt_1pg.py",
        "output_name": "prefilled_order_of_finish_2evt_1pg.pdf",
    },
}

app = Flask(__name__, template_folder="web_templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def render_index(error: str | None = None, status_code: int = 200) -> tuple[str, int]:
    return (
        render_template(
            "index.html",
            generators=GENERATORS,
            max_upload_mb=MAX_UPLOAD_MB,
            error=error,
        ),
        status_code,
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(_: RequestEntityTooLarge) -> tuple[str, int]:
    return render_index(
        error=f"Upload failed: the session report is larger than {MAX_UPLOAD_MB} MB.",
        status_code=413,
    )


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException) -> tuple[str, int]:
    if request.path == "/generate" and exc.code and exc.code >= 400:
        return render_index(error=exc.description, status_code=exc.code)
    return render_index(error=exc.description or "Request failed.", status_code=exc.code or 500)


@app.errorhandler(Exception)
def handle_unexpected_error(_: Exception) -> tuple[str, int]:
    return render_index(error="Unexpected server error.", status_code=500)


@app.get("/healthz")
def healthz() -> tuple[str, int]:
    return "ok", 200


@app.get("/")
def index() -> tuple[str, int]:
    return render_index()


@app.post("/generate")
def generate() -> object:
    upload = request.files.get("session_report")
    template_key = request.form.get("template_key", "")

    if upload is None or upload.filename == "":
        abort(400, "A session report PDF is required.")
    if template_key not in GENERATORS:
        abort(400, "Please select a valid template layout.")

    filename = secure_filename(upload.filename)
    if not filename:
        abort(400, "The uploaded filename is invalid.")
    if not filename.lower().endswith(".pdf"):
        abort(400, "The session report must be a PDF file.")

    generator = GENERATORS[template_key]

    with tempfile.TemporaryDirectory(prefix="oof_web_") as tmpdir_name:
        tmpdir = Path(tmpdir_name)
        report_path = tmpdir / filename
        output_path = tmpdir / generator["output_name"]
        upload.save(report_path)

        command = [
            "python3",
            str(generator["script"]),
            "--report",
            str(report_path),
            "--output",
            str(output_path),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            abort(500, f"Generation failed: {stderr}")

        if not output_path.exists():
            abort(500, "Generation failed: output PDF was not created.")

        pdf_bytes = output_path.read_bytes()

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=generator["output_name"],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", DEFAULT_PORT)))
