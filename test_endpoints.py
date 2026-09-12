import re
import urllib.parse
import urllib.request


def multipart_post(url, fields, files):
    """fields: dict[str,str]; files: dict[str,tuple[filename,bytes,content-type]]."""
    boundary = "----kpeflyertest"
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    for k, (filename, data, ctype) in files.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {ctype}\r\n\r\n".encode()
        body += data
        body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        url, data=bytes(body), method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), r.status


def count_pages(raw):
    return len(re.findall(rb"data:image/png;base64,", raw))


DATA = {
    "stamm": "München",
    "plz": "81739 München",
    "address": "Maximilian-Kolbe-Allee 18",
    "grouptime": "Freitag, 16.00-18.00 Uhr",
    "sfm": "Vroni Spörl",
    "mail": "stammstjakobus@gmail.com",
    "phone": "01577774472",
    "geschlecht": "weiblich",
    "instagram": "@muenchen",
}

# --- Vorschau ohne Upload (beide Seiten) ---
raw, status = multipart_post("http://localhost:5001/preview", DATA, {})
assert status == 200, status
n = count_pages(raw)
assert n == 2, f"erwartet 2 Seiten, erhalten {n}"
print(f"Vorschau (kein Upload): {n} Seiten gerendert")

# --- Vorschau mit Foto-Upload auf Seite 1 (Live-Tausch) ---
fake_png = b"\x89PNG\r\n\x1a\n" + b"X" * 2000
data1 = dict(DATA); data1["pages"] = "1"
files_upload = {"woelflingo": ("test_woelf.png", fake_png, "image/png")}
raw, status = multipart_post("http://localhost:5001/preview", data1, files_upload)
assert status == 200, f"Upload failed: {status}"
n = count_pages(raw)
assert n == 1, f"erwartet 1 Seite (pages=1), erhalten {n}"
print(f"Vorschau (Upload woelflingo): {n} Seite gerendert")

# --- Download ---
raw, status = multipart_post("http://localhost:5001/download", DATA, {})
assert status == 200, status
assert raw[:4] == b"%PDF", raw[:4]
print(f"Download: {len(raw)} Bytes PDF")

print("OK: alle Endpoints getestet")
