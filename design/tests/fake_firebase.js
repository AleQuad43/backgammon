/* A stand-in for Firebase (auth + Firestore, the calls the app makes), so the real deployed page can be tested with
   accounts: tests/make_cloud.py swaps it in for the Firebase scripts. Data lives in localStorage ("fb:<path>"), so two
   phones (windows) on the same origin share it, and each phone hears the other's writes through storage events.
   Sign in by URL: ?as=<uid>. matches/* can only be created, never overwritten (like the real rules). */
(function () {
  var Q = location.search, AS = (Q.match(/[?&]as=([\w-]+)/) || [])[1] || null;
  var subs = [];
  function key(p) { return 'fb:' + p; }
  function read(p) { try { var j = localStorage.getItem(key(p)); return j == null ? null : JSON.parse(j); } catch (e) { return null; } }
  function later(f) { setTimeout(f, 30 + Math.random() * 60); }
  function snapOf(p) { var v = read(p); return { id: p.split('/').pop(), exists: v != null, data: function () { return v == null ? undefined : JSON.parse(JSON.stringify(v)); }, metadata: { fromCache: false, hasPendingWrites: false }, ref: docRef(p) }; }
  function list(coll) {
    var out = [], pre = key(coll + '/');
    for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k.indexOf(pre) === 0 && k.slice(pre.length).indexOf('/') < 0) out.push(k.slice(3)); }
    return out.sort().map(snapOf);
  }
  function notify(p) { subs.slice().forEach(function (s) { if (s.match(p)) later(s.fire); }); }
  window.addEventListener('storage', function (e) { if (e.key && e.key.indexOf('fb:') === 0) notify(e.key.slice(3)); });
  function write(p, v) { if (v == null) localStorage.removeItem(key(p)); else localStorage.setItem(key(p), JSON.stringify(v)); notify(p); }
  function merge(a, b) { Object.keys(b).forEach(function (k) { a[k] = b[k]; }); return a; }
  function denied() { return Promise.reject({ code: 'permission-denied', message: 'denied' }); }
  function docRef(p) {
    return {
      id: p.split('/').pop(), path: p,
      get: function () { return new Promise(function (r) { later(function () { r(snapOf(p)); }); }); },
      set: function (d, o) {
        if (/^matches\//.test(p) && read(p) != null) return denied();
        return new Promise(function (r) { later(function () { write(p, o && o.merge ? merge(read(p) || {}, d) : d); r(); }); });
      },
      update: function (d) { return new Promise(function (r, j) { later(function () { var v = read(p); if (v == null) { j({ code: 'not-found' }); return; } write(p, merge(v, d)); r(); }); }); },
      onSnapshot: function (fn) {
        var s = { match: function (q) { return q === p; }, fire: function () { if (subs.indexOf(s) >= 0) fn(snapOf(p)); } };
        subs.push(s); later(s.fire);
        return function () { subs = subs.filter(function (x) { return x !== s; }); };
      }
    };
  }
  function query(coll, filt) {
    function docs() { return list(coll).filter(function (s) { return !filt || filt(s.data()); }); }
    return {
      where: function (f, op, v) { return query(coll, function (d) { return op === 'array-contains' ? (d[f] || []).indexOf(v) >= 0 : d[f] === v; }); },
      get: function () { return new Promise(function (r) { later(function () { r({ docs: docs() }); }); }); },
      onSnapshot: function (fn) {
        var s = { match: function (q) { return q.indexOf(coll + '/') === 0; }, fire: function () { if (subs.indexOf(s) >= 0) fn({ docs: docs() }); } };
        subs.push(s); later(s.fire);
        return function () { subs = subs.filter(function (x) { return x !== s; }); };
      },
      doc: function (id) { return docRef(coll + '/' + (id || Math.random().toString(36).slice(2, 12))); },
      add: function (d) { var r = docRef(coll + '/' + Math.random().toString(36).slice(2, 12)); return r.set(d).then(function () { return r; }); }
    };
  }
  var fs = {
    doc: docRef, collection: function (c) { return query(c, null); },
    runTransaction: function (fn) {
      var tx = { get: function (r) { return Promise.resolve(snapOf(r.path)); }, set: function (r, d) { write(r.path, d); }, update: function (r, d) { write(r.path, merge(read(r.path) || {}, d)); } };
      return Promise.resolve().then(function () { return fn(tx); });
    }
  };
  var user = AS ? { uid: AS, email: AS + '@test' } : null, authSubs = [];
  var auth = {
    get currentUser() { return user; },
    onAuthStateChanged: function (fn) { authSubs.push(fn); later(function () { fn(user); }); return function () {}; },
    signOut: function () { user = null; authSubs.forEach(function (f) { f(null); }); return Promise.resolve(); },
    signInWithEmailAndPassword: function () { return Promise.reject({ code: 'test' }); },
    createUserWithEmailAndPassword: function () { return Promise.reject({ code: 'test' }); },
    sendPasswordResetEmail: function () { return Promise.resolve(); }
  };
  window.firebase = { apps: [], initializeApp: function (c) { this.apps.push(c); return {}; }, auth: function () { return auth; }, firestore: function () { return fs; } };
})();
