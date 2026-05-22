import subprocess, re, qrcode, sys, os, time

env = os.environ.copy()
env['PATH'] = env['PATH'] + r';C:\Program Files\nodejs'

proc = subprocess.Popen(
    ['cmd', '/c', 'openclaw', 'channels', 'login', '--channel', 'openclaw-weixin'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
)

output = ''
for i in range(30):
    time.sleep(1)
    try:
        line = proc.stdout.readline()
        output += line
    except:
        break
    if 'qrcode=' in output:
        time.sleep(2)
        break

match = re.search(r'(https://liteapp\.weixin\.qq\.com/q/\S+)', output)
if match:
    link = match.group(1)
    print(f'QR_LINK: {link}')
    img = qrcode.make(link)
    img.save(r'C:\Users\Administrator\.openclaw\wechat-qr.png')
    print('SAVED: C:\\Users\\Administrator\\.openclaw\\wechat-qr.png')
else:
    print('NO_LINK_FOUND')
    print(output[:1000])

proc.terminate()
