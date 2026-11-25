"""Two real phones in a headless Chrome: each player is its own browser tab (own screen size, own history, own timers),
so a phone can be turned upright or sideways, sent to the background (frozen, as a phone does with an app you leave),
reloaded, and photographed. Tabs on the same origin share localStorage, so the local test store (?mock) works between
them as it does between two frames.
Used by scenarios.py. Needs the design server on port 8771 and Google Chrome. Standard library only."""
import base64, json, os, shutil, socket, struct, subprocess, tempfile, time, urllib.request

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
BASE = os.environ.get('BASE', 'http://localhost:8771/')


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
            self.rest += self.s.recv(1 << 20)
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytes([0x81]); ln = len(data)
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
            if r.get('id') == self.n:
                if 'error' in r: raise RuntimeError('%s: %s' % (method, r['error']))
                return r.get('result', {})


class Chrome:
    def __init__(self, port=9344):
        self.port = port
        self.prof = tempfile.mkdtemp(prefix='bgphones')
        self.proc = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=%d' % port, '--user-data-dir=' + self.prof,
                                      '--no-first-run', '--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'] + (['--enable-gpu', '--ignore-gpu-blocklist', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-gpu-rasterization'] if os.environ.get('GPU') else []) + ['about:blank'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(300):
            try: urllib.request.urlopen('http://127.0.0.1:%d/json/version' % port); break
            except Exception: time.sleep(0.1)
        else: raise RuntimeError('Chrome did not start')

    def tab(self, url):
        # each phone in a window of its own, so both are on screen at once (a second tab would be a hidden page)
        tid = self.browser().call('Target.createTarget', url=url, newWindow=True)['targetId']
        t = [x for x in json.loads(urllib.request.urlopen('http://127.0.0.1:%d/json' % self.port).read()) if x['id'] == tid][0]
        ph = Phone(WS(t['webSocketDebuggerUrl'])); ph.tid = tid; ph.chrome = self
        return ph

    def browser(self):
        if not getattr(self, 'bws', None):
            v = json.loads(urllib.request.urlopen('http://127.0.0.1:%d/json/version' % self.port).read())
            self.bws = WS(v['webSocketDebuggerUrl'])
        return self.bws

    def close(self):
        self.proc.terminate()
        try: self.proc.wait(5)
        except Exception: self.proc.kill()
        shutil.rmtree(self.prof, ignore_errors=True)


class Phone:
    """One phone: a tab with a phone-sized screen (CSS pixels, 3x density, touch)."""
    def __init__(self, ws):
        self.ws = ws
        ws.call('Page.enable'); ws.call('Runtime.enable')
        self.upright = False

    def size(self, upright):
        self.upright = upright
        w, h = (390, 844) if upright else (844, 390)
        self.ws.call('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=3, mobile=True,
                     screenOrientation={'type': 'portraitPrimary' if upright else 'landscapePrimary', 'angle': 0 if upright else 90})
        self.ws.call('Emulation.setTouchEmulationEnabled', enabled=True, maxTouchPoints=5)

    def go(self, url):
        self.ws.call('Page.navigate', url=BASE + url)
        for _ in range(100):
            time.sleep(0.1)
            if self.js('document.readyState') == 'complete' and self.js('!!window.BG'): return
        raise RuntimeError('page did not load: ' + url)

    def js(self, expr, wait=False):
        r = self.ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=wait)
        if r.get('exceptionDetails'): raise RuntimeError('js error: %s\n  in: %s' % (r['exceptionDetails'].get('exception', {}).get('description') or r['exceptionDetails'], expr[:200]))
        return r.get('result', {}).get('value')

    def background(self):
        """The app is left (home button, screen locked): nothing in the page runs (timers, frames, incoming data all wait)
        until it comes back. Headless Chrome can't show a hidden page again, so the page is paused in the debugger."""
        self.ws.call('Debugger.enable')
        self.ws.send({'id': 999999, 'method': 'Debugger.pause', 'params': {}})
        while self.ws.recv().get('method') != 'Debugger.paused': pass   # the board draws every frame, so this is quick
        self.paused = True

    def foreground(self):
        self.ws.send({'id': 999998, 'method': 'Debugger.resume', 'params': {}})
        self.paused = False
        time.sleep(0.1)

    def tap(self, x, y):
        pts = [{'x': x, 'y': y}]
        self.ws.call('Input.dispatchTouchEvent', type='touchStart', touchPoints=pts)
        time.sleep(0.05)
        self.ws.call('Input.dispatchTouchEvent', type='touchEnd', touchPoints=[])

    def shot(self, path):
        r = self.ws.call('Page.captureScreenshot', format='png')
        with open(path, 'wb') as f: f.write(base64.b64decode(r['data']))
        return path
