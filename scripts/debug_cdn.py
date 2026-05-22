"""Debug CDN upload"""
import subprocess, json, sys, os, hashlib, random, base64, struct, time

BOT_TOKEN = "93ce2a55ab54@im.bot:0600001b85c77c7845abfab549157923d42eeb"
WECHAT_USER_ID = "o9cq805lfrS-OgQ59AIP9tamh3Jw@im.wechat"

def random_wechat_uin():
    uint32 = struct.unpack("I", os.urandom(4))[0]
    return base64.b64encode(str(uint32).encode("utf-8")).decode()

def ilink_request(endpoint, body):
    body["base_info"] = {"channel_version": "2.4.3", "bot_agent": "OpenClaw"}
    cmd = ["curl", "-s", "-k", "-X", "POST",
        f"https://ilinkai.weixin.qq.com/{endpoint}",
        "-H", "Content-Type: application/json",
        "-H", "AuthorizationType: ilink_bot_token",
        "-H", f"Authorization: Bearer {BOT_TOKEN}",
        "-H", "iLink-App-Id: bot",
        "-H", "iLink-App-ClientVersion: 132099",
        "-H", f"X-WECHAT-UIN: {random_wechat_uin()}",
        "-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    raw = r.stdout.decode("utf-8", errors="replace")
    try:
        resp = json.loads(raw)
        if "ret" not in resp:
            resp["ret"] = 0
        return resp
    except:
        return {"ret": 0, "raw": raw}

# Use a real small image for testing
image_path = r"C:\Users\Administrator\AppData\Local\Temp\pexels_images\pexels-photo-33342194.jpeg"
if not os.path.exists(image_path):
    # Find any jpeg
    import glob
    imgs = glob.glob(r"C:\Users\Administrator\AppData\Local\Temp\pexels_images\*.jpeg")
    if imgs:
        image_path = imgs[0]
        print(f"Using: {image_path}")
    else:
        print("No images found!")
        sys.exit(1)

with open(image_path, "rb") as f:
    plaintext = f.read()
rawsize = len(plaintext)
rawfilemd5 = hashlib.md5(plaintext).hexdigest()
print(f"File: {rawsize}B, md5: {rawfilemd5}")

# AES encrypt
from Crypto.Cipher import AES
aeskey = os.urandom(16)
filekey = "".join(random.choices("0123456789abcdef", k=32))

pad_len = 16 - (len(plaintext) % 16)
padded = plaintext + bytes([pad_len] * pad_len)
ciphertext = AES.new(aeskey, AES.MODE_ECB).encrypt(padded)
filesize_cipher = len(ciphertext)
print(f"Ciphertext: {filesize_cipher}B")

# getuploadurl
get_body = {
    "filekey": filekey,
    "media_type": 2,
    "to_user_id": WECHAT_USER_ID,
    "rawsize": rawsize,
    "rawfilemd5": rawfilemd5,
    "filesize": filesize_cipher,
    "no_need_thumb": True,
    "aeskey": aeskey.hex(),
}
url_resp = ilink_request("ilink/bot/getuploadurl", get_body)
print(f"\ngetuploadurl response: {json.dumps(url_resp, indent=2)}")

upload_full_url = url_resp.get("upload_full_url", "").strip()
if not upload_full_url:
    print("No upload URL!")
    sys.exit(1)

# Write ciphertext to temp file
import tempfile
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
tmp.write(ciphertext)
tmp.close()

# Try CDN upload - Method 1: exactly like OpenClaw (no Auth-Key, no Content-Length)
print(f"\n=== Method 1: octet-stream only ===")
cmd1 = ["curl", "-s", "-k", "-v", "-X", "POST", upload_full_url,
    "-H", "Content-Type: application/octet-stream",
    "--data-binary", f"@{tmp.name}"]
r1 = subprocess.run(cmd1, capture_output=True, timeout=60)
out1 = r1.stdout.decode("utf-8", errors="replace")
err1 = r1.stderr.decode("utf-8", errors="replace")
print(f"Response: {out1[:500]}")
# Extract headers from stderr (curl -v)
for line in err1.split("\n"):
    if "x-encrypted-param" in line.lower() or "x-error" in line.lower() or "HTTP/" in line:
        print(f"  {line.strip()}")

# Method 2: with Auth-Key header
auth_key = url_resp.get("auth_key", "")
if auth_key:
    print(f"\n=== Method 2: with Auth-Key ===")
    cmd2 = ["curl", "-s", "-k", "-v", "-X", "POST", upload_full_url,
        "-H", "Content-Type: application/octet-stream",
        "-H", f"Auth-Key: {auth_key}",
        "--data-binary", f"@{tmp.name}"]
    r2 = subprocess.run(cmd2, capture_output=True, timeout=60)
    out2 = r2.stdout.decode("utf-8", errors="replace")
    err2 = r2.stderr.decode("utf-8", errors="replace")
    print(f"Response: {out2[:500]}")
    for line in err2.split("\n"):
        if "x-encrypted-param" in line.lower() or "x-error" in line.lower() or "HTTP/" in line:
            print(f"  {line.strip()}")

os.unlink(tmp.name)
