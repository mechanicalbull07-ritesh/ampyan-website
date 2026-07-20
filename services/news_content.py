"""Validation and normalization for AMPYAN rich news content.

Article data is deliberately a small, typed JSON vocabulary. Raw HTML, iframe
markup and article-provided scripts are never accepted or rendered.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


MAX_BLOCKS = 160
MAX_INLINE_RUNS = 120
MAX_LIST_ITEMS = 80
MAX_GALLERY_IMAGES = 12
MAX_TABLE_COLUMNS = 12
MAX_TABLE_ROWS = 80
MAX_TEXT = 20_000
MAX_URL = 2_000

SUPPORTED_BLOCK_TYPES = {
    "paragraph", "heading", "subheading", "bullet_list", "numbered_list",
    "image", "gallery", "quote", "highlight", "key_data", "table",
    "divider", "youtube", "instagram",
}


def _text(value, limit=MAX_TEXT):
    return str(value or "").strip()[:limit]


def _safe_url(value, *, relative=False, hosts=None):
    value = _text(value, MAX_URL)
    if not value or any(char in value for char in ("\r", "\n", "\x00")):
        return None
    if relative and value.startswith("/") and not value.startswith("//"):
        return value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    host = (parsed.hostname or "").lower().rstrip(".")
    if hosts and host not in hosts:
        return None
    return value


def normalize_youtube_url(value):
    url = _safe_url(value, hosts={
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
        "youtube-nocookie.com", "www.youtube-nocookie.com",
    })
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]
    video_id = ""
    if host == "youtu.be" and parts:
        video_id = parts[0]
    elif parsed.path == "/watch":
        video_id = (parse_qs(parsed.query).get("v") or [""])[0]
    elif parts and parts[0] in {"shorts", "embed"} and len(parts) > 1:
        video_id = parts[1]
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id or ""):
        return None
    return {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "video_id": video_id,
        "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}",
    }


def normalize_instagram_url(value):
    url = _safe_url(value, hosts={"instagram.com", "www.instagram.com"})
    if not url:
        return None
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] not in {"p", "reel", "tv"}:
        return None
    shortcode = parts[1]
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", shortcode):
        return None
    return {
        "url": f"https://www.instagram.com/{parts[0]}/{shortcode}/",
        "shortcode": shortcode,
    }


def _inline(value):
    raw_runs = value if isinstance(value, list) else [{"text": value}]
    runs = []
    for raw in raw_runs[:MAX_INLINE_RUNS]:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or "")[:5_000]
        if not text.strip():
            continue
        run = {"text": text}
        if raw.get("bold") is True:
            run["bold"] = True
        if raw.get("italic") is True:
            run["italic"] = True
        link = _safe_url(raw.get("link") or raw.get("url"))
        if link:
            run["link"] = link
        runs.append(run)
    return runs


def _image(value):
    if not isinstance(value, dict):
        return None
    url = _safe_url(value.get("url"), relative=True)
    if not url:
        return None
    return {
        "url": url,
        "caption": _text(value.get("caption"), 1_000),
        "alt_text": _text(value.get("alt_text"), 500),
    }


def normalize_block(raw):
    if not isinstance(raw, dict):
        return None
    block_type = _text(raw.get("type"), 40).lower()
    if block_type not in SUPPORTED_BLOCK_TYPES:
        return None

    if block_type == "paragraph":
        content = _inline(raw.get("content", raw.get("text", "")))
        return {"type": block_type, "content": content} if content else None
    if block_type == "heading":
        text = _text(raw.get("text"), 500)
        level = raw.get("level", 2)
        level = level if isinstance(level, int) and level in {2, 3, 4} else 2
        return {"type": block_type, "level": level, "text": text} if text else None
    if block_type == "subheading":
        text = _text(raw.get("text"), 1_000)
        return {"type": block_type, "text": text} if text else None
    if block_type in {"bullet_list", "numbered_list"}:
        items = []
        raw_items = raw.get("items") if isinstance(raw.get("items"), list) else []
        for item in raw_items[:MAX_LIST_ITEMS]:
            runs = _inline(item)
            if runs:
                items.append(runs)
        return {"type": block_type, "items": items} if items else None
    if block_type == "image":
        image = _image(raw)
        return {"type": block_type, **image} if image else None
    if block_type == "gallery":
        images = []
        for item in (raw.get("images") if isinstance(raw.get("images"), list) else [])[:MAX_GALLERY_IMAGES]:
            normalized = _image(item)
            if normalized:
                images.append(normalized)
        return {"type": block_type, "images": images} if images else None
    if block_type in {"quote", "highlight"}:
        content = _inline(raw.get("content", raw.get("text", "")))
        if not content:
            return None
        result = {"type": block_type, "content": content}
        label = _text(raw.get("title") or raw.get("cite"), 300)
        if label:
            result["title" if block_type == "highlight" else "cite"] = label
        return result
    if block_type == "key_data":
        items = []
        for item in (raw.get("items") if isinstance(raw.get("items"), list) else [])[:24]:
            if not isinstance(item, dict):
                continue
            label, value = _text(item.get("label"), 300), _text(item.get("value"), 1_000)
            if label or value:
                items.append({"label": label, "value": value})
        return {"type": block_type, "items": items} if items else None
    if block_type == "table":
        headers = [_text(cell, 500) for cell in (raw.get("headers") or [])[:MAX_TABLE_COLUMNS]] if isinstance(raw.get("headers"), list) else []
        if not headers:
            return None
        rows = []
        for row in (raw.get("rows") if isinstance(raw.get("rows"), list) else [])[:MAX_TABLE_ROWS]:
            if not isinstance(row, list):
                continue
            cells = [_text(cell, 2_000) for cell in row[:len(headers)]]
            cells.extend([""] * (len(headers) - len(cells)))
            rows.append(cells)
        return {"type": block_type, "headers": headers, "rows": rows}
    if block_type == "divider":
        return {"type": block_type}
    if block_type == "youtube":
        normalized = normalize_youtube_url(raw.get("url"))
        return {"type": block_type, **normalized} if normalized else None
    if block_type == "instagram":
        normalized = normalize_instagram_url(raw.get("url"))
        return {"type": block_type, **normalized} if normalized else None
    return None


def normalize_content_blocks(value):
    if value is None:
        return None
    if isinstance(value, list):
        raw_blocks = value
    elif isinstance(value, dict) and isinstance(value.get("blocks"), list):
        raw_blocks = value["blocks"]
    else:
        return None
    blocks = []
    for raw in raw_blocks[:MAX_BLOCKS]:
        block = normalize_block(raw)
        if block:
            blocks.append(block)
    return {"version": 1, "blocks": blocks} if blocks else None


def content_blocks_limit_error(value):
    """Return a user-facing error before normalization could discard content."""
    raw_blocks = value if isinstance(value, list) else value.get("blocks") if isinstance(value, dict) else None
    if not isinstance(raw_blocks, list):
        return "Rich content must contain a blocks list."
    if len(raw_blocks) > MAX_BLOCKS:
        return f"Rich articles support up to {MAX_BLOCKS} blocks; remove or combine {len(raw_blocks) - MAX_BLOCKS} block(s)."

    def inline_error(raw_value, location):
        runs = raw_value if isinstance(raw_value, list) else [{"text": raw_value}]
        if len(runs) > MAX_INLINE_RUNS:
            return f"{location} has more than {MAX_INLINE_RUNS} formatted text runs."
        for run in runs:
            if isinstance(run, dict) and len(str(run.get("text") or "")) > 5_000:
                return f"{location} contains a formatted text segment longer than 5,000 characters. Split it into paragraphs."
        return None

    for index, raw in enumerate(raw_blocks, start=1):
        if not isinstance(raw, dict):
            continue
        block_type = str(raw.get("type") or "").strip().lower()
        location = f"Block {index}"
        if block_type in {"paragraph", "quote", "highlight"}:
            error = inline_error(raw.get("content", raw.get("text", "")), location)
            if error:
                return error
            label = raw.get("title") or raw.get("cite") or ""
            if block_type in {"quote", "highlight"} and len(str(label)) > 300:
                return f"{location} label/citation must be 300 characters or fewer."
        elif block_type == "heading" and len(str(raw.get("text") or "")) > 500:
            return f"{location} heading must be 500 characters or fewer."
        elif block_type == "subheading" and len(str(raw.get("text") or "")) > 1_000:
            return f"{location} subheading must be 1,000 characters or fewer."
        elif block_type in {"bullet_list", "numbered_list"}:
            items = raw.get("items") if isinstance(raw.get("items"), list) else []
            if len(items) > MAX_LIST_ITEMS:
                return f"{location} supports up to {MAX_LIST_ITEMS} list items."
            for item_index, item in enumerate(items, start=1):
                error = inline_error(item, f"{location}, list item {item_index}")
                if error:
                    return error
        elif block_type in {"image", "gallery"}:
            images = [raw] if block_type == "image" else raw.get("images") if isinstance(raw.get("images"), list) else []
            if block_type == "gallery" and len(images) > MAX_GALLERY_IMAGES:
                return f"{location} supports up to {MAX_GALLERY_IMAGES} gallery images."
            for image in images:
                if not isinstance(image, dict):
                    continue
                if len(str(image.get("caption") or "")) > 1_000:
                    return f"{location} image caption must be 1,000 characters or fewer."
                if len(str(image.get("alt_text") or "")) > 500:
                    return f"{location} image alt text must be 500 characters or fewer."
                if len(str(image.get("url") or "")) > MAX_URL:
                    return f"{location} image URL must be {MAX_URL:,} characters or fewer."
        elif block_type == "table":
            headers = raw.get("headers") if isinstance(raw.get("headers"), list) else []
            rows = raw.get("rows") if isinstance(raw.get("rows"), list) else []
            if len(headers) > MAX_TABLE_COLUMNS:
                return f"{location} supports up to {MAX_TABLE_COLUMNS} table columns."
            if len(rows) > MAX_TABLE_ROWS:
                return f"{location} supports up to {MAX_TABLE_ROWS} table rows."
            if any(len(str(cell or "")) > 500 for cell in headers):
                return f"{location} table headers must be 500 characters or fewer per cell."
            if any(len(str(cell or "")) > 2_000 for row in rows if isinstance(row, list) for cell in row):
                return f"{location} table cells must be 2,000 characters or fewer."
        elif block_type in {"youtube", "instagram"} and len(str(raw.get("url") or "")) > MAX_URL:
            return f"{location} media URL must be {MAX_URL:,} characters or fewer."
    return None


def blocks_plain_text(value):
    document = normalize_content_blocks(value)
    if not document:
        return ""
    parts = []
    for block in document["blocks"]:
        block_type = block["type"]
        if block_type in {"heading", "subheading"}:
            parts.append(block["text"])
        elif block_type in {"paragraph", "quote", "highlight"}:
            parts.append("".join(run["text"] for run in block["content"]))
        elif block_type in {"bullet_list", "numbered_list"}:
            parts.extend("".join(run["text"] for run in item) for item in block["items"])
        elif block_type == "key_data":
            parts.extend(f"{item['label']}: {item['value']}".strip(": ") for item in block["items"])
        elif block_type == "table":
            parts.append(" | ".join(block["headers"]))
            parts.extend(" | ".join(row) for row in block["rows"])
        elif block_type in {"image", "gallery"}:
            images = [block] if block_type == "image" else block["images"]
            parts.extend(image["caption"] or image["alt_text"] for image in images if image["caption"] or image["alt_text"])
    return "\n\n".join(part for part in parts if part).strip()
