"""Builds tests/sim_cloud.html: the deployed page (docs/index.html) with accounts, but Firebase replaced by
tests/fake_firebase.js (data in localStorage, sign in with ?as=<uid>), plus the test hook from make_sim.py.
Run after build_app.py:  python3 design/tests/make_cloud.py   (scenarios.py uses it for the account tests)"""
import os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
# SRC=<another docs/index.html> OUT=<name> to test another build
src = pathlib.Path(os.environ.get('SRC', HERE.parent.parent / 'docs' / 'index.html')).read_text()
for s in ['<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>\n',
          '<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"></script>\n',
          '<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js"></script>\n']:
    assert src.count(s) == 1, s
    src = src.replace(s, '')
old = '<script src="firebase-config.js"></script>'
assert src.count(old) == 1
src = src.replace(old, '<script>window.FB_CONFIG = { projectId: "test" };</script>\n<script src="fake_firebase.js"></script>')
sw = "if ('serviceWorker' in navigator) addEventListener('load', function () { navigator.serviceWorker.register('sw.js'); });"
assert src.count(sw) == 1
src = src.replace(sw, '')
tmp = HERE / 'sim_cloud_src.html'
tmp.write_text(src)
subprocess.run([sys.executable, str(HERE / 'make_sim.py'), str(tmp), os.environ.get('OUT', 'sim_cloud.html')], check=True)
tmp.unlink()
