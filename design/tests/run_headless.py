"""Runs a test page in a headless Chrome and prints its log as it goes.
  python3 design/tests/run_headless.py "tests/simulate.html?games=10"
Needs the design server on port 8771 (python3 -m http.server 8771 --directory design) and Google Chrome.
The page reports by putting lines in #log and its final result in window.__result. Only the standard library is used:
a tiny websocket client talks to Chrome's debugging port."""
import base64, json, os, shutil, socket, struct, subprocess, sys, tempfile, time, urllib.request

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PORT = int(os.environ.get('CDP_PORT', 9333))
url = 'http://localhost:8771/' + (sys.argv[1] if len(sys.argv) > 1 else 'tests/simulate.html')
limit = float(sys.argv[2]) if len(sys.argv) > 2 else 1800

prof = tempfile.mkdtemp(prefix='bgsim')
proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + prof, '--window-size=1400,1000',
                         '--no-first-run', '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
                         '--disable-backgrounding-occluded-windows', '--autoplay-policy=no-user-gesture-required', 'about:blank'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class WS:
    def __init__(self, wsurl):
        host, path = wsurl[len('ws://'):].split('/', 1)
        h, p = host.split(':')
        self.s = socket.create_connection((h, int(p)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(('GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (path, host, key)).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.rest = buf.split(b'\r\n\r\n', 1)[1]
        self.n = 0

    def _recv(self, n):
        while len(self.rest) < n:
            self.rest += self.s.recv(65536)
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytes([0x81])
        ln = len(data)
        if ln < 126: hdr += bytes([0x80 | ln])
        elif ln < 65536: hdr += bytes([0x80 | 126]) + struct.pack('>H', ln)
        else: hdr += bytes([0x80 | 127]) + struct.pack('>Q', ln)
        mask = os.urandom(4)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b''
        while True:
            b0, b1 = self._recv(2)
            ln = b1 & 0x7f
            if ln == 126: ln = struct.unpack('>H', self._recv(2))[0]
            elif ln == 127: ln = struct.unpack('>Q', self._recv(8))[0]
            msg += self._recv(ln)
            if b0 & 0x80: return json.loads(msg)

    def call(self, method, **params):
        self.n += 1
        self.send({'id': self.n, 'method': method, 'params': params})
        while True:
            r = self.recv()
            if r.get('id') == self.n: return r

    def eval(self, expr):
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True)
        return r.get('result', {}).get('result', {}).get('value')


try:
    for _ in range(50):
        try:
            tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:%d/json' % PORT).read())
            page = [t for t in tabs if t['type'] == 'page'][0]
            break
        except Exception:
            time.sleep(0.2)
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable')
    ws.call('Page.navigate', url=url)
    t0, shown = time.time(), 0
    while time.time() - t0 < limit:
        time.sleep(5)
        lines = ws.eval("(function(){var l=document.getElementById('log');return l?l.innerText.split('\\n'):[]})()") or []
        for ln in lines[shown:]:
            print(ln, flush=True)
        shown = len(lines)
        res = ws.eval('window.__result ? JSON.stringify(window.__result) : null')
        if res:
            print('RESULT', res, flush=True)
            break
    else:
        print('TIMEOUT', ws.eval("document.getElementById('sum') && document.getElementById('sum').innerText"), flush=True)
finally:
    proc.terminate()
    try: proc.wait(5)
    except Exception: proc.kill()
    shutil.rmtree(prof, ignore_errors=True)
