import hashlib
import os
import secrets
import time
from io import BytesIO
from urllib.parse import urlparse

import requests
from flask import current_app, url_for
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_UPLOAD_PIXELS = 24_000_000
MAX_IMAGE_WIDTH = 1200
TARGET_BYTES = 500 * 1024
PLACEHOLDER_STATIC_PATH = "images/logo.png"


def is_external_image_url(value):
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def cloudinary_settings():
    cloudinary_url = os.environ.get("CLOUDINARY_URL")
    if cloudinary_url:
        parsed = urlparse(cloudinary_url)
        if parsed.scheme == "cloudinary" and parsed.hostname and parsed.username and parsed.password:
            return {
                "cloud_name": parsed.hostname,
                "api_key": parsed.username,
                "api_secret": parsed.password,
            }

    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    api_key = os.environ.get("CLOUDINARY_API_KEY")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
    if cloud_name and api_key and api_secret:
        return {"cloud_name": cloud_name, "api_key": api_key, "api_secret": api_secret}
    return None


def _compress_image_to_bytes(image_file):
    try:
        original_filename = secure_filename(image_file.filename or "")
        if not original_filename:
            return None, "missing_filename"
        if "." not in original_filename or original_filename.rsplit(".", 1)[1].lower() not in ALLOWED_IMAGE_EXTENSIONS:
            return None, "invalid_extension"

        image_file.stream.seek(0, os.SEEK_END)
        original_size = image_file.stream.tell()
        image_file.stream.seek(0)
        if original_size <= 0:
            return None, "empty_file"
        if original_size > MAX_UPLOAD_BYTES:
            return None, "file_too_large"

        raw_bytes = image_file.read()
        image_file.stream.seek(0)
        with Image.open(BytesIO(raw_bytes)) as check_img:
            check_img.verify()
        with Image.open(BytesIO(raw_bytes)) as img:
            if (img.format or "").lower() not in {"jpeg", "png", "webp"}:
                return None, "invalid_image_format"
            if img.width * img.height > MAX_UPLOAD_PIXELS:
                return None, "image_dimensions_too_large"

            img = ImageOps.exif_transpose(img)
            if img.width > MAX_IMAGE_WIDTH:
                ratio = MAX_IMAGE_WIDTH / float(img.width)
                img = img.resize((MAX_IMAGE_WIDTH, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)

            output_image = img.convert("RGBA") if img.mode in {"RGBA", "LA"} else img.convert("RGB")
            final_bytes = None
            for quality in (82, 76, 70, 64):
                output = BytesIO()
                output_image.save(output, format="WEBP", quality=quality, method=4)
                final_bytes = output.getvalue()
                if len(final_bytes) <= TARGET_BYTES:
                    break
            return {"bytes": final_bytes, "extension": "webp"}, None
    except Exception as exc:
        return None, exc.__class__.__name__


def _upload_cloudinary(image_bytes, filename, folder):
    settings = cloudinary_settings()
    if not settings:
        return {"ok": False, "url": None, "reason": "config_missing"}

    timestamp = str(int(time.time()))
    signature_payload = f"folder={folder}&timestamp={timestamp}{settings['api_secret']}"
    signature = hashlib.sha1(signature_payload.encode("utf-8")).hexdigest()
    upload_url = f"https://api.cloudinary.com/v1_1/{settings['cloud_name']}/image/upload"
    try:
        response = requests.post(
            upload_url,
            data={
                "api_key": settings["api_key"],
                "timestamp": timestamp,
                "folder": folder,
                "signature": signature,
            },
            files={"file": (filename, image_bytes, "image/webp")},
            timeout=6,
        )
        response.raise_for_status()
        secure_url = (response.json() or {}).get("secure_url")
        if secure_url:
            return {"ok": True, "url": secure_url, "reason": None}
        return {"ok": False, "url": None, "reason": "missing_secure_url"}
    except Exception as exc:
        return {"ok": False, "url": None, "reason": exc.__class__.__name__}


def public_image_url(folder, value, placeholder=True):
    if is_external_image_url(value):
        return value
    if not value:
        return url_for("static", filename=PLACEHOLDER_STATIC_PATH) if placeholder else None

    filename = secure_filename(os.path.basename(value))
    if not filename:
        return url_for("static", filename=PLACEHOLDER_STATIC_PATH) if placeholder else None

    relative_path = os.path.join(folder, filename)
    absolute_path = os.path.join(current_app.static_folder, relative_path)
    if os.path.isfile(absolute_path):
        return url_for("static", filename=relative_path.replace(os.sep, "/"))
    return url_for("static", filename=PLACEHOLDER_STATIC_PATH) if placeholder else None


def store_public_image(image_file, kind, local_folder):
    try:
        compressed, reason = _compress_image_to_bytes(image_file)
        if not compressed:
            return {"ok": False, "stored_value": None, "public_url": None, "reason": reason}

        filename = f"{secure_filename(kind)}_{secrets.token_hex(8)}.{compressed['extension']}"
        folder = os.environ.get(f"CLOUDINARY_{kind.upper()}_FOLDER") or f"ampyan/{kind}"
        cloudinary_result = _upload_cloudinary(compressed["bytes"], filename, folder)
        if cloudinary_result.get("ok"):
            url = cloudinary_result["url"]
            return {"ok": True, "stored_value": url, "public_url": url, "reason": None}

        current_app.logger.warning(
            "public_image_cloudinary_unavailable kind=%s reason=%s",
            kind,
            cloudinary_result.get("reason"),
        )
        os.makedirs(local_folder, exist_ok=True)
        local_path = os.path.join(local_folder, filename)
        with open(local_path, "wb") as output:
            output.write(compressed["bytes"])
        return {
            "ok": True,
            "stored_value": filename,
            "public_url": public_image_url(os.path.basename(local_folder), filename),
            "reason": "local_fallback",
        }
    except Exception as exc:
        current_app.logger.warning("public_image_store_failed kind=%s reason=%s", kind, exc.__class__.__name__)
        return {"ok": False, "stored_value": None, "public_url": None, "reason": exc.__class__.__name__}
