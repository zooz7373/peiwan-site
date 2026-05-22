"""测试 openclaw 发送是否正常工作 - 3种方法对比"""
import subprocess
import sys
import os

GATEWAY_TOKEN = "c1e5ee9f04f570917c2874ab615775a4494fbb9039a069bf"
WECHAT_TARGET = "o9cq805lfrS-OgQ59AIP9tamh3Jw@im.wechat"
OPENCLAW_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"
IMAGE_PATH = r"C:\Users\Administrator\AppData\Local\Temp\pexels_images\pexels-photo-29699511.jpeg"

def show(label, r):
    sys.stdout.buffer.write(f"\n=== {label} ===\nRC={r.returncode}\n".encode("utf-8"))
    if r.stdout:
        sys.stdout.buffer.write(b"OUT: " + r.stdout + b"\n")
    if r.stderr:
        sys.stdout.buffer.write(b"ERR: " + r.stderr + b"\n")

# Method 1: cmd /c with set (current xlv_send.py approach)
token_part = f"set OPENCLAW_GATEWAY_TOKEN={GATEWAY_TOKEN} && "
cmd = f'cmd /c "{token_part}{OPENCLAW_CMD} message send --channel openclaw-weixin --target {WECHAT_TARGET} --media {IMAGE_PATH}"'
show("Method1 cmd/c IMAGE", subprocess.run(cmd, shell=True, capture_output=True, timeout=60))

# Method 2: env dict approach
env = os.environ.copy()
env["OPENCLAW_GATEWAY_TOKEN"] = GATEWAY_TOKEN
show("Method2 env IMAGE", subprocess.run(
    [OPENCLAW_CMD, "message", "send", "--channel", "openclaw-weixin",
     "--target", WECHAT_TARGET, "--media", IMAGE_PATH],
    capture_output=True, timeout=60, env=env))

# Method 3: PowerShell text
ps_cmd = (
    f'$env:OPENCLAW_GATEWAY_TOKEN="{GATEWAY_TOKEN}"; '
    f'& "{OPENCLAW_CMD}" message send '
    f'--channel openclaw-weixin '
    f'--target {WECHAT_TARGET} '
    f"-m 'test text from method3'"
)
show("Method3 PS TEXT", subprocess.run(
    ["powershell", "-NoProfile", "-Command", ps_cmd],
    capture_output=True, timeout=60))

# Method 4: env dict text
show("Method2 env TEXT", subprocess.run(
    [OPENCLAW_CMD, "message", "send", "--channel", "openclaw-weixin",
     "--target", WECHAT_TARGET, "-m", "test text from method2 env"],
    capture_output=True, timeout=60, env=env))
