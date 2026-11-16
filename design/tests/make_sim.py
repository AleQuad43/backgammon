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
    undoFrom: undoFrom, stepsOf: stepsOf, forfeit: forfeit, canDouble: canDouble, isRace: isRace, closedOut: closedOut, tapMove: tapMove };
"""
mark = "\n  /* ---------- start ---------- */"
assert src.count(mark) == 1
out = src.replace(mark, hook + mark)
i = out.index('<meta charset="utf-8">') + len('<meta charset="utf-8">\n')
out = out[:i] + speed + out[i:]
(HERE / name).write_text(out)
print(name, len(out))
