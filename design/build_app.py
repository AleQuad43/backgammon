"""Builds app.html: the friends home (orbs) + the board from game.html, with the sky following the time of day.
The board's script is taken from game.html and patched in a few named places, so board fixes made in game.html
can be carried over by running this again:  python3 build_app.py"""
import re, pathlib

HERE = pathlib.Path(__file__).parent
game = (HERE / 'game.html').read_text()
shell = (HERE / 'app_shell.html').read_text()

js = game[game.index('<script>') + len('<script>'):game.rindex('</script>')]

def sub(old, new, count=1):
    global js
    n = js.count(old)
    assert n == count, (old, n)
    js = js.replace(old, new)

def resub(pat, new, count=1):
    global js
    js, n = re.subn(pat, new, js, flags=re.S)
    assert n == count, (pat, n)

# The board fills the screen: no scaled phone frame.
resub(r"function fit\(\) \{.*?\n  \}\n", "function fit() {}\n")
# Board sky: the time-of-day pools, shared with the home screen.
sub("var sk = document.querySelector('.sky')", "var sk = $('gsky')")
sub("c: '--g1' }", "c: '--p1' }"); sub("c: '--g2' }", "c: '--p2' }"); sub("c: '--g3' }", "c: '--p3' }")
sub("}).join(', ') + ', var(--gbase)';", "}).join(', ') + ', var(--sky)';")
# Highlight colours follow the sky's hues as the day goes on.
sub("var SKYC = null;", "var SKYC = null; setInterval(function () { SKYC = null; }, 20000);")
# Prototype controls that lived in the notes below the board.
resub(r"\n  \$\('spinDur'\)[^\n]*\n  \$\('spinDur'\)[^\n]*\n  \$\('spinTry'\)[^\n]*", "")
resub(r"\n  \$\('holdMs'\)[^\n]*\n  \$\('holdMs'\)[^\n]*", "")
resub(r"\n  \$\('aiDbl'\)\.addEventListener[^\n]*", "")
sub(" $('aiDbl').textContent = 'Let Luca double you on his next turn';", "")
sub("\n    $('aiDbl').hidden = !!DUO;", "")
sub("\n  $('seatBtn').addEventListener('click', pickSeat);", "")
sub(" $('seatBtn').hidden = false;", "")
resub(r"\n  \$\('flip'\)[^\n]*\n  \$\('bearoff'\)[^\n]*\n  \$\('restart'\)[^\n]*", "")
sub("\n  $('goFull').addEventListener('click', goFull);", "")
resub(r"\n  document\.addEventListener\('pointerdown', function first[^\n]*", "")
# The opponent is whoever you opened the game with.
sub("SEATS[DUO.other] : { name: 'Luca', ini: 'LU' }", "SEATS[DUO.other] : OPP")
sub("say('Luca is playing.')", "say(NAME.them + ' is playing.')")
sub("'. Luca is playing.'", "'. ' + NAME.them + ' is playing.'")
sub("say('Luca rolled ' + D[0].v + '. Throw yours.')", "say(NAME.them + ' rolled ' + D[0].v + '. Throw yours.')")
sub("'Luca starts'", "NAME.them + ' starts'")
sub("say('Luca rolled ' + v + ' when he challenged you. Throw yours.');", "say(NAME.them + ' rolled ' + v + ' when they challenged you. Throw yours.');")
sub("var keep = G ? G.score : { me: 3, them: 2 };", "var keep = G ? G.score : (OPP.score || { me: 0, them: 0 });")
# The two real players for the first test.
sub("var SEATS = { A: { name: 'Alessandro', ini: 'AL' }, B: { name: 'Luca', ini: 'LU' } };", "var SEATS = { A: { name: 'Quad', ini: 'QU' }, B: { name: 'Nolf', ini: 'NO' } };")
sub("'<button data-s=\"A\">Me (Alessandro)</button><button data-s=\"B\">Luca</button>", "'<button data-s=\"A\">Quad</button><button data-s=\"B\">Nolf</button>")
sub("me = DUO ? SEATS[DUO.seat] : { ini: 'AL' }", "me = DUO ? SEATS[DUO.seat] : { ini: 'QU' }")
# Seat choice: joining happens when you open the game with Luca, not on load.
resub(r"var m = q\.match\(/\[\?&\]seat=\(\[AB\]\)/\), s = m \? m\[1\] : null;\n\s*if \(!s\) try \{ s = localStorage\.getItem\('duoSeat'\); \} catch \(e\) \{\}\n\s*if \(s === 'A' \|\| s === 'B'\) joinDuo\(s\); else if \(s !== 'ai'\) pickSeat\(\);",
      "if (PENDING) { var f = PENDING; PENDING = null; f(); }")
sub("      if (!db) return;\n      DB = db;", "      if (!db) { NODB = true; if (PENDING) { var f0 = PENDING; PENDING = null; f0(); } return; }\n      DB = db;")
sub("}).catch(function () {});\n  }\n\n  /* ---------- start", "}).catch(function () { NODB = true; });\n  }\n\n  /* ---------- start")
# Start-up: nothing is shown until a game is opened from home.
sub("  fit(); layout(); start(); connect();", "  connect();")
sub("window.addEventListener('resize', function () { fit(); layout(); });", "window.addEventListener('resize', function () { if (!$('gv').hidden) layout(); });")

api = r"""
  /* ---------- App hooks: the home screen opens and closes the board ---------- */
  var OPP = { name: 'Nolf', ini: 'NO' }, CUR = null, PENDING = null, NODB = false;
  function storedSeat() { var m = location.search.match(/[?&]seat=([AB])/); if (m) return m[1]; try { return localStorage.getItem('duoSeat'); } catch (e) { return null; } }
  function showBoard() { $('gv').hidden = false; layout(); paintSky(skyA); }
  window.BG = {
    open: function (o) {
      showBoard();
      /* Real accounts: one shared game per pair of friends, seat decided by the app. */
      if (o.gid && !NODB) {
        if (!DB) { PENDING = function () { window.BG.open(o); }; say('Connecting to the shared game…'); return; }
        if (DUO && DUO.gid !== o.gid) { if (DUO.unsub) DUO.unsub(); DUO = null; G = null; }
        CUR = o.id; SEATS.A = o.seats.A; SEATS.B = o.seats.B; OPP = SEATS[o.seat === 'A' ? 'B' : 'A'];
        if (!DUO) { CASE.fresh = true; MATCH = o.to || 5; window.GAMEID = o.gid; joinDuo(o.seat); DUO.gid = o.gid; }
        return;
      }
      if (o.duo && !NODB) {
        if (!DB) { PENDING = function () { window.BG.open(o); }; if (!G) { OPP = o; setNames(); start(); } say('Connecting to the shared game…'); return; }
        CUR = 'duo';
        if (!DUO) { CASE.fresh = true; var s = storedSeat(); if (s === 'A' || s === 'B') joinDuo(s); else pickSeat(); }
        return;
      }
      if (DUO) { if (DUO.unsub) DUO.unsub(); DUO = null; }
      var fresh = CUR !== o.id || !G; CUR = o.id; OPP = o; setNames();
      if (fresh) { CASE.fresh = true; G = null; if (o.to) { MATCH = o.to; $('scTo').textContent = 'to ' + MATCH; } start(); }
    },
    close: function () { $('gv').hidden = true; $('over').hidden = true; },
    seat: function () { CUR = 'duo'; showBoard(); if (DB) pickSeat(); else say('The shared game needs the published page.'); },
    bearOff: function () { tryBearOff(); },
    restart: function () { if (DUO) newGame(true); else { G = null; start(); } },
    current: function () { return DUO && !DUO.gid ? 'no' : CUR; },
    ready: function () { return !!G && $('over').hidden && !$('gv').hidden && (CUR !== 'duo' || !!(DUO && DUO.lastDoc)); }
  };
  $('homeBtn').addEventListener('click', function () { window.BG.close(); if (window.onBoardClosed) window.onBoardClosed(); });
"""
sub("\n  /* ---------- start ---------- */", api + "\n  /* ---------- start ---------- */")

# Board styles, scoped under #gv so they don't clash with the home screen's.
css = game[game.index('\n.sky {'):game.index('\n.notes {')]
css = css.replace('breathe', 'gbreathe').replace('wob', 'gwob')
def scope(line):
    if not line.strip() or line.startswith('@') or line.startswith(' ') or '{' not in line: return line
    sel, rest = line.split('{', 1)
    return ', '.join('#gv ' + s.strip() for s in sel.split(',')) + ' {' + rest
css = '\n'.join(scope(l) for l in css.split('\n'))

# The rail on the board shows each player's checker instead of initials.
sub("ref: DB.doc('games/duo')", "ref: DB.doc('games/' + (window.GAMEID || 'duo'))")
sub("$('avThem').textContent = them.ini; $('avMe').textContent = me.ini;",
    "if (window.ckAv) { ckAv($('avThem'), them.ini); ckAv($('avMe'), me.ini); } else { $('avThem').textContent = them.ini; $('avMe').textContent = me.ini; }")

# Checker avatars: the drawing code lives in checkers.html (the workshop); the app gets the same code.
work = (HERE / 'checkers.html').read_text()
ck = work[work.index('  /* ---------- materials'):work.index('  /* ---------- canvases ---------- */')]
ages = re.search(r"  var AGES = .*?\n  function ageName.*?\n", work).group(0)
rnd = re.search(r"  function randomChecker\(\) .*?\n", work).group(0)
checker = ("(function () {\n" + ck + ages + rnd +
           "  window.Checker = { MAT: MAT, FACES: FACES, INLAYS: INLAYS, AGES: AGES, ageName: ageName, random: randomChecker, top: drawTop, tilt: drawTilt, texture: texture, chips: chipsFor, frac: fracColour, THICK: THICK };\n})();")

out = shell.replace('/*BOARD_SCRIPT*/', js).replace('/*BOARD_CSS*/', css).replace('/*CHECKER*/', checker)
(HERE / 'app.html').write_text(out)
print('app.html', len(out))
(HERE / 'preview.html').write_text('<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + out)

# The deployed version (GitHub Pages, ../docs): same page, installable, with Firebase as the shared store.
WEB_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Backgammon">
<meta name="theme-color" content="#E6ECEA">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js"></script>
<script src="firebase-config.js"></script>
<script>
/* Firebase behind the same small doc/set/update/onSnapshot shape the board already uses.
   Each game is kept as one JSON string, so nested arrays are fine; update is a read-merge-write transaction. */
window.fbDb = function () {
  if (!window.firebase || !window.FB_CONFIG) return null;
  var fs = firebase.apps.length ? firebase.firestore() : (firebase.initializeApp(window.FB_CONFIG), firebase.firestore());
  function merge(a, b) { Object.keys(b).forEach(function (k) { if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k]) && a[k] && typeof a[k] === 'object') merge(a[k], b[k]); else a[k] = b[k]; }); return a; }
  function val(s) { return s.exists ? JSON.parse(s.data().j) : null; }
  return { doc: function (p) { var r = fs.doc(p); return {
    set: function (d) { return r.set({ j: JSON.stringify(d), t: Date.now() }); },
    update: function (d) { return fs.runTransaction(function (tx) { return tx.get(r).then(function (s) {
      var v = val(s); if (!v) throw { code: 'invalid_argument' }; tx.set(r, { j: JSON.stringify(merge(v, d)), t: Date.now() }); }); }); },
    onSnapshot: function (fn) { return r.onSnapshot(function (s) { var v = val(s); fn({ exists: !!v, data: function () { return v; }, metadata: s.metadata }); }); }
  }; } };
};
if ('serviceWorker' in navigator) addEventListener('load', function () { navigator.serviceWorker.register('sw.js'); });
</script>
</head>
<body>
"""
assert out.count("Promise.resolve(/[?&]mock/.test(q) ? mockDb() : null)") == 1
web = out.replace("Promise.resolve(/[?&]mock/.test(q) ? mockDb() : null)",
                  "Promise.resolve(/[?&]mock/.test(q) ? mockDb() : (window.fbDb ? window.fbDb() : null))")
web = web.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
docs = HERE.parent / 'docs'
docs.mkdir(exist_ok=True)
(docs / 'index.html').write_text(WEB_HEAD + web + '\n</body>\n</html>\n')
print('docs/index.html', len(web))
