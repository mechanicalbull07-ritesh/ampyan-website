import re


CSRF_META_PATTERN = re.compile(
    rb'<meta name="csrf-token" content="([^"]+)"'
)


def csrf_token(client, path="/"):
    response = client.get(path)
    assert response.status_code == 200
    match = CSRF_META_PATTERN.search(response.data)
    assert match, f"No CSRF token rendered by {path}"
    return match.group(1).decode("utf-8")


def csrf_form_data(client, path="/", **values):
    return {"csrf_token": csrf_token(client, path), **values}


def csrf_json_headers(client, path="/"):
    return {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token(client, path),
    }
