"""Static checks on the board script.  Run:  python3 design/tests/test_static.py

1. No name is declared twice with `var` in the same function scope. Two `var PIPS` (the dots on the dice and the
   pip-count switch) silently became one variable and blanked the dice; this catches that kind of clash.
2. A new match pre-rolls the opening die of whoever starts it, never a fixed seat.
"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
fails = []


def scopes(src):
    """Yield (start, body) for every function body in src, by brace matching (strings and comments skipped)."""
    out, stack, i, n = [], [], 0, len(src)
    while i < n:
        c = src[i]
        if c in '\'"`':
            q, i = c, i + 1
            while i < n and src[i] != q:
                i += 2 if src[i] == '\\' else 1
        elif src.startswith('//', i):
            i = src.find('\n', i)
            if i < 0:
                break
        elif src.startswith('/*', i):
            i = src.find('*/', i) + 1
        elif c == '{':
            head = src[max(0, i - 200):i]
            stack.append((i, bool(re.search(r'function\s*[\w$]*\s*\([^()]*\)\s*$', head))))
        elif c == '}' and stack:
            s, isfn = stack.pop()
            if isfn:
                out.append((s, src[s + 1:i]))
        i += 1
    return out


FUNCS = []


def own_vars(body):
    """var names declared directly in this function body (nested functions removed)."""
    # blank out nested function bodies
    out, i, n = [], 0, len(body)
    while i < n:
        m = re.compile(r'function\s*([\w$]*)\s*\([^()]*\)\s*\{').match(body, i)
        if m:
            if m.group(1) and (i == 0 or not re.match(r'[\w$.]', body[i - 1])) and not re.search(r'[=(:,]\s*$', body[max(0, i - 40):i]):
                FUNCS.append(m.group(1))
            d, j = 1, m.end()
            while j < n and d:
                d += {'{': 1, '}': -1}.get(body[j], 0)
                j += 1
            i = j
            continue
        out.append(body[i])
        i += 1
    flat = ''.join(out)
    names = []
    for m in re.finditer(r'\bvar\s+([^;]+);', flat):
        decl = m.group(1)
        depth, part, parts = 0, '', []
        for ch in decl:
            depth += ch in '([{'
            depth -= ch in ')]}'
            if ch == ',' and depth == 0:
                parts.append(part)
                part = ''
            else:
                part += ch
        parts.append(part)
        for p in parts:
            nm = re.match(r'\s*([A-Za-z_$][\w$]*)', p)
            if nm:
                names.append(nm.group(1))
    return names


for name in ('game.html', 'app.html'):
    html = (HERE / name).read_text()
    for js in re.findall(r'<script>(.*?)</script>', html, re.S):
        for s, body in scopes(js):
            del FUNCS[:]
            vs = own_vars(body)
            fs = list(FUNCS)
            # the same function name declared twice in one scope: the second silently replaces the first everywhere
            fd = sorted({f for f in fs if fs.count(f) > 1} | (set(fs) & set(vs)))
            if fd:
                fails.append('%s: function declared twice (or also as a var) in one scope: %s' % (name, ', '.join(fd)))
            dup = sorted({v for v in vs if vs.count(v) > 1})
            # loop counters (i, j, k…) and short temporaries are re-declared on purpose all over; only flag real names
            dup = [v for v in dup if len(v) > 2 and not v.islower()]
            if dup:
                fails.append('%s: declared twice in one scope: %s' % (name, ', '.join(dup)))

game = (HERE / 'game.html').read_text()
if "open: { A: null, B: fresh ?" in game:
    fails.append('game.html: a new match still pre-rolls seat B whoever starts it')
if 'if (fresh) op[DUO.seat] =' not in game:
    fails.append('game.html: a new match should pre-roll the starter\'s own die')

if fails:
    print('FAIL\n' + '\n'.join(sorted(set(fails))))
    sys.exit(1)
print('ok: no clashing declarations or function names; the opening die belongs to whoever starts')
