"""Builds tests/sim_app.html: the app (preview.html) with a test hook that lets tests/simulate.html drive the board.
Run after build_app.py:  python3 design/tests/make_sim.py
- window.__T exposes the board's own functions (throw, move, hand over, double, undo, give up...) and its state.
- ?speed=4 makes every timer in the page run four times faster (animations and physics stay real time)."""
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
# optional: another build to test (e.g. an older version's preview.html) and the name to write it under
src = pathlib.Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else (HERE.parent / 'preview.html').read_text()
name = sys.argv[2] if len(sys.argv) > 2 else 'sim_app.html'

speed = """<script>
(function () { var k = +((location.search.match(/[?&]speed=([\\d.]+)/) || [])[1]) || 1; if (k === 1) return;
  var st = window.setTimeout; window.setTimeout = function (f, ms) { var a = [].slice.call(arguments, 2); return st.apply(window, [f, (+ms || 0) / k].concat(a)); }; })();
/* ?reduce: the phone asks for reduced motion (the board then skips throws, glides and replays) */
if (/[?&]reduce/.test(location.search)) { var mm = window.matchMedia; window.matchMedia = function (q) { return /reduced-motion/.test(q) ? { matches: true, addListener: function () {}, addEventListener: function () {} } : mm.call(window, q); }; }
/* the two phones are frames in one tab, which share one history: "back" in one would close the other's board */
try { history.pushState = function () {}; history.replaceState = function () {}; history.back = function () {}; } catch (e) {}
window.__errors = [];
window.addEventListener('error', function (e) { window.__errors.push(String(e.message) + ' @' + e.lineno); });
(function () { var ce = console.error; console.error = function () { window.__errors.push([].map.call(arguments, function (x) { return x && x.stack ? x.stack.split('\\n').slice(0, 3).join(' | ') : String(x); }).join(' ')); return ce.apply(console, arguments); }; })();
</script>
"""
hook = """
  window.__T = { get G() { return G; }, get D() { return D; }, get DUO() { return DUO; }, get stacks() { return stacks; }, get REPL() { return REPL; }, get FOLD() { return FOLD; },
    ME: ME, TH: TH, state: state, plays: plays, legal: legal, remaining: remaining, anyMove: anyMove, canThrow: canThrow, canPass: canPass, canForfeit: canForfeit,
    myThrow: myThrow, stepMove: stepMove, afterMyMove: afterMyMove, handOver: handOver, takeDouble: takeDouble, dropDouble: dropDouble, offerMine: offerMine,
    undoFrom: undoFrom, stepsOf: stepsOf, forfeit: forfeit, canDouble: canDouble, isRace: isRace, closedOut: closedOut, tapMove: tapMove,
    get ck() { return ck; }, get L() { return L; }, get W() { return W; }, get H() { return H; }, get CASE() { return CASE; }, posOf: posOf, offerPos: offerPos, cvClient: cvClient,
    /* (older builds have no cachesOk: the same test, done here) */
    cachesOk: typeof cachesOk === 'function' ? cachesOk : function () {
      var op = function (c, x, y) { return c.getContext('2d').getImageData(x, y, 1, 1).data[3] > 0; };
      if (!op(bg, Math.round(L.lx * DPR + 6), Math.round(L.mid * DPR))) return false;
      for (var k in CKS) if (CKS[k].width && !op(CKS[k], CKS[k].width >> 1, CKS[k].height >> 1)) return false;
      return true; },
    /* what a phone does to a page in the background: the pictures it kept aside are wiped */
    wipe: function () { Object.keys(CKS).forEach(function (k) { var g = CKS[k].getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, 1e4, 1e4); }); bx.setTransform(1, 0, 0, 1, 0, 0); bx.clearRect(0, 0, bg.width, bg.height); } };
  /* What the screen shows, checked against what it should show. Returns a list of problems (empty = fine).
     settled: nothing has changed for a while, so everything should have come to rest. */
  window.__screen = function (settled) {
    var out = [], gv = $('gv');
    if (!G || !stacks || !gv || gv.hidden) return out;
    var vw = window.innerWidth, vh = window.innerHeight, upright = vh > vw;
    var cr = cv.getBoundingClientRect();
    if (!upright && (cr.width < 100 || cr.height < 100)) out.push('the board canvas is ' + Math.round(cr.width) + '×' + Math.round(cr.height) + ' on screen');
    if (!upright && (Math.abs(W - $('wrap').clientWidth) > 1 || Math.abs(H - $('wrap').clientHeight) > 1)) out.push('the board is laid out for ' + W + '×' + H + ' but the screen holds ' + $('wrap').clientWidth + '×' + $('wrap').clientHeight);
    var busy = CASE.a || FOLD;
    if (!busy && cv.style.visibility === 'hidden') out.push('the board canvas is hidden');
    if (!busy && cv.style.opacity === '0') out.push('the board canvas is see-through');
    if (!busy && document.querySelector('#wrap .case')) out.push('a case/fold layer is left over the board');
    var n = { me: 0, them: 0 };
    Object.keys(stacks).forEach(function (k) {
      var loc = isNaN(+k) ? k : +k;
      stacks[k].forEach(function (id, i) {
        var c = ck[id]; n[c.side === ME ? 'me' : 'them']++;
        if (!isFinite(c.x) || !isFinite(c.y)) { out.push('checker ' + id + ' on ' + k + ' has no position (' + c.x + ',' + c.y + ')'); return; }
        if (settled && !busy && !c.place && !(drag && drag.id === id)) {
          var p = posOf(loc, i, String(loc).indexOf('off') === 0 ? 0 : stacks[k].length);
          /* off its place and not moving since the last look (a slow test browser draws few frames, so a checker can
             still be on its way) */
          var still = c.__seen && Math.hypot(c.__seen[0] - c.x, c.__seen[1] - c.y) < 0.5; c.__seen = [c.x, c.y];
          if (Math.hypot(p[0] - c.x, p[1] - c.y) > 3 && still) out.push('checker ' + id + ' on ' + k + ' drawn at ' + Math.round(c.x) + ',' + Math.round(c.y) + ' instead of ' + Math.round(p[0]) + ',' + Math.round(p[1]));
          if (c.x < 0 || c.y < 0 || c.x > W || c.y > H) out.push('checker ' + id + ' off the board');
        }
      });
    });
    if (n.me !== 15 || n.them !== 15) out.push('checkers on the board: ' + n.me + ' / ' + n.them);
    D.forEach(function (d) {
      if (!d.live) return;
      if (!isFinite(d.x) || !isFinite(d.y)) out.push('a die has no position');
      else if (settled && (d.x < 0 || d.y < 0 || d.x > W || d.y > H)) out.push('a die is off the board at ' + Math.round(d.x) + ',' + Math.round(d.y));
    });
    if (settled && !busy && !upright) {
      var cf = $('cubeFloat'), cube = $('cube');
      if (G.phase === 'offered') {
        if (!cf.hidden && !cf.getAnimations().length) {
          var r = cf.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
          if (cf.style.visibility === 'hidden' || r.width < 5) out.push('their double: the cube to tap is invisible');
          else if (x < cr.left || x > cr.right || y < cr.top || y > cr.bottom) out.push('their double: the cube to tap is off the board, at ' + Math.round(x) + ',' + Math.round(y) + ' (board ' + Math.round(cr.left) + '–' + Math.round(cr.right) + ' × ' + Math.round(cr.top) + '–' + Math.round(cr.bottom) + ')');
          else { var op = offerPos(), oc = cvClient(op[0], op[1]); if (Math.hypot(oc[0] - x, oc[1] - y) > 40) out.push('their double: the cube shows at ' + Math.round(x) + ',' + Math.round(y) + ' but a tap counts at ' + Math.round(oc[0]) + ',' + Math.round(oc[1])); }
        }
      } else if (G.phase !== 'wait' && !cdrag) {
        if (!cf.hidden) out.push('a floating cube is left on screen (phase ' + G.phase + ')');
        if (cube.classList.contains('dragging')) out.push('the rail cube is left faded (phase ' + G.phase + ')');
      }
    }
    var ov = $('over'), on = !ov.hidden && ov.style.visibility !== 'hidden';
    if (settled && !busy && G.phase !== 'over' && G.phase !== 'replay' && on && !(DUO && DUO.prevShow)) out.push('an end card is up in phase ' + G.phase);
    if (settled && G.phase === 'over' && !on && DUO && !DUO.away) out.push('the game is over but no end card is shown');
    return out;
  };
"""
mark = "\n  /* ---------- start ---------- */"
assert src.count(mark) == 1
out = src.replace(mark, hook + mark)
i = out.index('<meta charset="utf-8">') + len('<meta charset="utf-8">\n')
out = out[:i] + speed + out[i:]
(HERE / name).write_text(out)
print(name, len(out))
