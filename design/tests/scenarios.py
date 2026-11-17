"""Real-phone scenarios: two tabs (phones.py), each checked on what its screen shows (window.__screen in the test build).
  python3 design/build_app.py && python3 design/tests/make_sim.py
  python3 -m http.server 8771 --directory design   (in another terminal)
  python3 design/tests/scenarios.py [name ...]     (no names: all of them)
Screenshots of failures go to design/tests/shots/."""
import json, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(__file__))
from phones import Chrome

APP = os.environ.get('APP', 'tests/sim_app.html')
GID = 'scn_pair'
SEATS = {'A': {'name': 'Quad', 'ini': 'qu'}, 'B': {'name': 'Nolf', 'ini': 'no'}}
SHOTS = os.path.join(os.path.dirname(__file__), 'shots')
os.makedirs(SHOTS, exist_ok=True)
results = []


def board(pts_a=None):
    """seat A's numbers, + = A's checkers"""
    pts = [0] * 25
    for a, n in (pts_a or {24: 2, 13: 5, 8: 3, 6: 5, 1: -2, 12: -5, 17: -3, 19: -5}).items(): pts[a] = n
    return {'pts': pts, 'bar': {'A': 0, 'B': 0}, 'off': {'A': 0, 'B': 0}}


def gdoc(**kw):
    d = {'v': 10, 'by': 'B', 'game': 1, 'round': 0, 'phase': 'roll', 'turn': 'A', 'open': {'A': None, 'B': None}, 'board': board(),
         'dice': None, 'cube': {'v': 1, 'owner': None}, 'offerBy': None, 'score': {'A': 0, 'B': 0}, 'result': None, 'to': 5,
         'log': [], 'race': None, 'ro': None, 't0': int(time.time() * 1000) - 3600e3, 'pips': True, 'prev': None}
    d.update(kw)
    return d


class Run:
    def __init__(self, chrome, name):
        self.c, self.name, self.fails, self.n = chrome, name, [], 0

    def phone(self, seat, upright=False):
        p = self.c.tab('about:blank')
        p.size(upright)
        p.go(APP + '?mock&t=%d' % (time.time() * 1000))
        p.seat = seat
        return p

    def seed(self, p, d):
        p.js("Object.keys(localStorage).forEach(function(k){ if (/^mock:|^bgSeen:|^bgEnd:/.test(k)) localStorage.removeItem(k); });"
             "localStorage.setItem('mock:games/%s', %s)" % (GID, json.dumps(json.dumps(d))))

    def open(self, p, **extra):
        o = {'id': 'no' if p.seat == 'A' else 'qu', 'gid': GID, 'seat': p.seat, 'seats': SEATS, 'name': SEATS['B' if p.seat == 'A' else 'A']['name'], 'ini': 'x', 'to': 5, 'pips': True}
        o.update(extra)
        p.js('BG.open(%s)' % json.dumps(o))

    def doc(self, p):
        return json.loads(p.js("localStorage.getItem('mock:games/%s')" % GID) or 'null')

    def check(self, ok, what, p=None):
        self.n += 1
        if not ok:
            self.fails.append(what)
            shot = ''
            if p is not None:
                shot = p.shot(os.path.join(SHOTS, '%s_%d.png' % (self.name, len(self.fails))))
            print('  ✗', what, ('[' + os.path.basename(shot) + ']') if shot else '', flush=True)
        else:
            print('  ✓', what, flush=True)

    def screen(self, p, what, settled=True):
        p.js('window.__screen(true)'); time.sleep(1.5)   # a first look, so a checker still on its way is not counted
        probs = p.js('window.__screen(%s)' % ('true' if settled else 'false')) or []
        errs = p.js('window.__errors.splice(0)') or []
        self.check(not probs and not errs, '%s: %s screen%s' % (p.seat, what, (' — ' + '; '.join((probs + errs)[:4])) if probs or errs else ' is right'), p)

    def until(self, p, expr, secs=10):
        t = time.time()
        while time.time() - t < secs:
            try:
                if p.js(expr): return True
            except Exception: pass
            time.sleep(0.15)
        return False

    def status(self, p):
        return p.js("document.getElementById('status').textContent")


# ---------------------------------------------------------------------------------------------------------------------
def offer_upright(r):
    """Nolf doubles while Quad opens the game holding the phone upright (home is upright), then turns it sideways."""
    a = r.phone('A', upright=True)
    r.seed(a, gdoc(phase='offered', turn='B', offerBy='B', by='B'))
    r.open(a)
    r.until(a, "__T.G && __T.G.phase === 'offered'", 8)
    time.sleep(2.2)
    a.size(False)
    time.sleep(1.5)
    r.screen(a, 'double arrived upright, phone turned sideways')


def offer_rotate_twice(r):
    """Quad's board is open sideways when Nolf doubles; Quad turns the phone upright and back."""
    a = r.phone('A')
    r.seed(a, gdoc(phase='roll', turn='B', by='A'))
    r.open(a)
    time.sleep(2.5)
    d = r.doc(a); d.update(v=d['v'] + 5, by='B', phase='offered', turn='B', offerBy='B')
    a.js("localStorage.setItem('mock:games/%s', %s); window.dispatchEvent(new StorageEvent('storage', {key: 'mock:games/%s'}))" % (GID, json.dumps(json.dumps(d)), GID))
    r.until(a, "__T.G.phase === 'offered'", 5); time.sleep(2)
    r.screen(a, 'double arrived sideways')
    a.size(True); time.sleep(0.8); a.size(False); time.sleep(1.5)
    r.screen(a, 'double, after turning upright and back')


MID = {24: 1, 20: 1, 13: 4, 8: 3, 6: 4, 5: 2, 1: -2, 12: -4, 17: -2, 19: -4, 21: -2, 3: -1}  # 15 / 15


def move_doc(seat='B', vals=(5, 1)):
    return gdoc(phase='move', turn=seat, by=seat, board=board(MID),
                dice={'by': seat, 'n': 'n1', 't': None, 'list': [{'v': v, 'used': False} for v in vals]})


def open_variants(r):
    """Nolf opens a game where it's his move, in every way a phone can: upright then turned, turned during the
    opening animation, sent to the background during it, opened twice quickly."""
    cases = [('sideways', False, None), ('upright, then turned', True, 'turn'), ('turned during the case animation', True, 'turn-early'),
             ('background during the case animation', False, 'bg'), ('upright + background, then turned', True, 'bg-turn')]
    for label, up, what in cases:
        b = r.phone('B', upright=up)
        r.seed(b, move_doc())
        r.open(b)
        if what == 'turn-early': time.sleep(0.3); b.size(False)
        if what in ('bg', 'bg-turn'): time.sleep(0.4); b.background(); time.sleep(2); b.foreground()
        if what in ('turn', 'bg-turn'): time.sleep(1.5); b.size(False)
        time.sleep(4)
        r.screen(b, 'opened ' + label)
        b.ws.call('Page.close')


def reopen_variants(r):
    """Nolf's board was open; he goes home and back, or the app goes to the background, while Quad plays."""
    a, b = r.phone('A'), r.phone('B')
    r.seed(a, move_doc('A', (6, 5)))
    r.open(a); r.open(b); time.sleep(4)
    r.screen(b, 'watching')
    # Quad plays 6-5 (24/13) and hands over; Nolf's board is closed meanwhile
    b.js('BG.close()')
    a.js("__T.stepMove(24, 18, 6); __T.stepMove(18, 13, 5); __T.afterMyMove(); __T.handOver(null)")
    time.sleep(2.5)
    b.size(True); r.open(b); time.sleep(1); b.size(False); time.sleep(8)
    r.screen(b, 'back to the board (upright, then turned) after Quad played')
    b.background(); time.sleep(1)
    a.js("BG.close()")
    time.sleep(1); b.foreground(); time.sleep(3)
    r.screen(b, 'after the app came back from the background')


RACE = {6: 3, 5: 3, 4: 3, 3: 2, 2: 2, 1: 2, 19: -3, 20: -3, 21: -3, 22: -2, 23: -2, 24: -2}
OVER = "__T.G && __T.G.phase === 'over' && !document.getElementById('over').hidden"


def rollout_variants(r):
    """A race is rolled out (Quad answers yes, Nolf had already). While it replays, each phone does something a
    phone does; both must reach the end card with the board at the final position."""
    for what in ['nothing', 'B background', 'B closes and reopens', 'B turns upright and back', 'B taps to skip',
                 'A background', 'A closes and reopens', 'A starts the next game at once', 'B reloads']:
        a, b = r.phone('A'), r.phone('B')
        r.seed(a, gdoc(phase='roll', turn='A', by='B', board=board(RACE), race={'A': None, 'B': True}, score={'A': 1, 'B': 1}))
        r.open(b); r.open(a)
        if not r.until(a, "__T.G.asking && !!document.querySelector('#note button[data-a=\"1\"]')", 8):
            r.check(False, what + ': Quad is asked to roll out', a); continue
        a.js("document.querySelector('#note button[data-a=\"1\"]').click()")
        time.sleep(3)
        if what == 'B background': b.background(); time.sleep(6); b.foreground()
        if what == 'A background': a.background(); time.sleep(6); a.foreground()
        if what == 'B closes and reopens': b.js('BG.close()'); time.sleep(3); r.open(b)
        if what == 'A closes and reopens': a.js('BG.close()'); time.sleep(3); r.open(a)
        if what == 'B turns upright and back': b.size(True); time.sleep(2); b.size(False)
        if what == 'B taps to skip': b.tap(300, 200)
        if what == 'B reloads': b.go(APP + '?mock&t=%d' % (time.time() * 1000)); r.open(b)
        if what == 'A starts the next game at once':
            r.until(a, OVER, 90); time.sleep(0.5); a.js("var g=document.getElementById('again'); g && g.click()")
        for p in (a, b):
            if what == 'A starts the next game at once' and p is a: continue
            ok = r.until(p, OVER, 100)
            r.check(ok, '%s: %s — %s reaches the end card (%s, “%s”)' % (what, p.seat, 'Quad' if p is a else 'Nolf', p.js('__T.G.phase'), r.status(p)), p)
            if ok: time.sleep(0.5); r.screen(p, what + ', end of the roll-out')
        if what == 'A starts the next game at once':
            r.until(b, "__T.G && document.getElementById('again') && !document.getElementById('over').hidden", 5)
        for p in (a, b): p.ws.call('Page.close')


def wiped_pictures(r):
    """The phone wipes the board's kept pictures while the app is in the background (Nolf's empty board)."""
    b = r.phone('B')
    r.seed(b, move_doc()); r.open(b); time.sleep(4)
    r.check(b.js('__T.cachesOk()'), 'B: the kept pictures are seen as fine when they are', b)
    b.background(); time.sleep(1); b.foreground(); b.js('__T.wipe()')
    r.check(not b.js('__T.cachesOk()'), 'B: a wiped picture is noticed')
    time.sleep(3)
    r.check(b.js('__T.cachesOk()'), 'B: and made again within 3 s', b)
    b.shot(os.path.join(SHOTS, 'wiped_after.png'))


def elo_after_match(r):
    """With accounts (the deployed page on a fake Firebase): Quad wins a 1-point match against Nolf. The match is
    saved once, both phones' Elo moves by the same amount, and Nolf's phone only shows it once it has shown the end."""
    ck = {'m': 'bone', 't': 2, 'f': 'rosette', 'i': 'brass', 'a': 0.2, 's': 4242}
    pts = [0] * 25; pts[1] = 1; pts[19] = -5; pts[20] = -5
    near = gdoc(v=10, by='B', phase='move', turn='A', board={'pts': pts, 'bar': {'A': 0, 'B': 0}, 'off': {'A': 14, 'B': 5}},
                dice={'by': 'A', 'n': 'e1', 't': None, 'list': [{'v': 6, 'used': False}, {'v': 5, 'used': False}]}, to=1)
    seed = {'players/ua': {'name': 'Quad', 'ck': ck, 'elo': 1500, 't': 1}, 'players/ub': {'name': 'Nolf', 'ck': ck, 'elo': 1500, 't': 2},
            'games/ua_ub': {'j': json.dumps(near), 't': 1}}
    def phone(uid):
        p = r.c.tab('about:blank'); p.size(True)
        p.ws.call('Page.navigate', url='http://localhost:8771/tests/' + os.environ.get('CLOUD_APP', 'sim_cloud.html') + '?as=%s&t=%d' % (uid, time.time() * 1000))
        r.until(p, "document.readyState === 'complete' && !!window.BG", 10)
        return p
    a = phone('ua')
    a.js("Object.keys(localStorage).forEach(function(k){ if (/^fb:|^bgEnd:|^bgSeen:/.test(k)) localStorage.removeItem(k); });" +
         ''.join("localStorage.setItem('fb:%s', %s);" % (k, json.dumps(json.dumps(v))) for k, v in seed.items()) + "location.reload()")
    time.sleep(1); r.until(a, "!!window.BG && document.querySelectorAll('.star').length >= 2", 10)
    b = phone('ub'); r.until(b, "document.querySelectorAll('.star').length >= 2", 10)
    elo = "(function(){var o={}; document.querySelectorAll('.star').forEach(function(s){var m=(s.getAttribute('aria-label')||'').match(/^(.*), Elo (\\d+)/); if(m && m[1] !== 'Computer') o[m[1]]=+m[2];}); return o;})()"
    r.check(a.js(elo) == {'Quad': 1500, 'Nolf': 1500}, 'before: everyone at 1500 (%s)' % a.js(elo), a)
    a.size(False)
    a.js("BG.open({id: 'ub', gid: 'ua_ub', seat: 'A', seats: {A: {name: 'Quad', ini: 'ua'}, B: {name: 'Nolf', ini: 'ub'}}, name: 'Nolf', ini: 'ub', to: 1, pips: true, newMatch: false})")
    r.check(r.until(a, OVER, 20), 'Quad bears off his last checker and sees the end card', a)
    r.check(r.until(a, "!!localStorage.getItem('fb:matches/ua_ub_1')", 5), 'the match is saved once, as matches/ua_ub_1')
    m = json.loads(a.js("localStorage.getItem('fb:matches/ua_ub_1')") or 'null') or {}
    r.check(m.get('winner') == 'ua' and m.get('loser') == 'ub' and m.get('to') == 1, 'with Quad as the winner, match to 1 (%s)' % m)
    a.js('BG.close()'); a.size(True); time.sleep(1.5)
    ea = a.js(elo)
    r.check(ea.get('Quad', 0) > 1500 and ea.get('Nolf', 9999) < 1500 and ea['Quad'] - 1500 == 1500 - ea['Nolf'], 'Quad’s phone: Quad up, Nolf down by the same (%s)' % ea, a)
    eb = b.js(elo)
    r.check(eb == {'Quad': 1500, 'Nolf': 1500}, 'Nolf’s phone, end not seen yet: no change, so no spoiler (%s)' % eb, b)
    b.size(False)
    b.js("BG.open({id: 'ua', gid: 'ua_ub', seat: 'B', seats: {A: {name: 'Quad', ini: 'ua'}, B: {name: 'Nolf', ini: 'ub'}}, name: 'Quad', ini: 'ua', to: 1, pips: true, newMatch: false})")
    r.check(r.until(b, OVER, 20), 'Nolf opens the game and sees the end card', b)
    b.js('BG.close()'); b.size(True); time.sleep(1.5)
    eb = b.js(elo)
    r.check(eb == ea, 'Nolf’s phone now shows the same Elo as Quad’s (%s)' % eb, b)
    n = b.js("Object.keys(localStorage).filter(function(k){return /^fb:matches\\//.test(k)}).length")
    r.check(n == 1, 'still one match saved, not two (%s)' % n)
    for p in (a, b): p.ws.call('Page.close')


SCENARIOS = [elo_after_match,offer_upright, offer_rotate_twice, open_variants, reopen_variants, wiped_pictures, rollout_variants]

if __name__ == '__main__':
    want = sys.argv[1:]
    c = Chrome()
    try:
        for f in SCENARIOS:
            if want and f.__name__ not in want: continue
            print(f.__name__, '—', f.__doc__.strip().split('\n')[0], flush=True)
            r = Run(c, f.__name__)
            try: f(r)
            except Exception: r.fails.append('crashed'); traceback.print_exc()
            results.append((f.__name__, r.n, r.fails))
    finally:
        c.close()
    bad = [x for x in results if x[2]]
    print('\n%d scenarios, %d checks, %d failed' % (len(results), sum(x[1] for x in results), sum(len(x[2]) for x in results)))
    sys.exit(1 if bad else 0)
