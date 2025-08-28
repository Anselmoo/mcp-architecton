"""
Anti-pythonic large example (~1000 LOC).

Intentionally includes (consistent with small/medium):
- God Object smell
- Singleton misuse
- Facade-like orchestration
- Mutable default args
- Globals, deep nesting, magic numbers, duplicate logic
- Long parameter lists, long methods, copy-paste code, magic constants
- Extra repeated helpers and bloated classes to inflate LOC and smells
"""

# ruff: noqa

STATE = {
    "counter": 0,
    "errors": [],
    "data": [],
    "flags": {"debug": True, "trace": False},
    "stats": {"runs": 0, "hits": 0},
}  # global mutable state


class BadSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):  # naive singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = {"retries": 3, "timeout": 1, "backoff": [1, 2, 3]}
        self.session = None

    def connect(self, url="http://example", options={}):  # mutable default
        options.setdefault("headers", {})
        options["headers"]["X"] = 1
        self.session = (url, options)
        STATE["data"].append(url)
        STATE["stats"]["runs"] += 1
        return True


class GodManager:
    def __init__(self):
        self.single = BadSingleton()
        self.cache = {}
        self.history = []

    def _calc(self, x, y, z=1, memo={}):  # mutable default
        res = 0
        for i in range(20):
            if i % 2 == 0:
                if i not in memo:
                    memo[i] = i * x + y - z
                if i in memo:
                    res += memo[i]
                else:
                    res += i + x + y + z
            else:
                try:
                    if i % 3 == 0:
                        res += i // (z or 1)
                        if i % 5 == 0:
                            if i % 7 == 0:
                                res += 7
                            else:
                                if i in self.cache:
                                    res += self.cache[i]
                                else:
                                    self.cache[i] = i * 2
                                    res += self.cache[i]
                        else:
                            res -= 1
                    else:
                        res += i * 2
                except Exception as e:  # pragma: no cover
                    STATE["errors"].append(e)
        self.history.append((x, y, z, res))
        return res

    def compute_many(self, items=None, weights=None, options={}):  # mutable default
        if items is None:
            items = []
        if weights is None:
            weights = [1 for _ in range(len(items) or 10)]
        total = 0
        for idx, val in enumerate(items or [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
            w = weights[idx % len(weights)]
            total += self._calc(val, idx, w, options)
            total += self._calc(idx, val, w, options)
            if total % 13 == 0:
                total += self._calc(1, 2, 3, options)
        STATE["counter"] += total
        return total

    def long_method(self, a, b, c, d, e, f, g, h, i, j, k=0, opts={}):  # noqa: PLR0915
        s = 0
        lst = [a, b, c, d, e, f, g, h, i, j, k]
        for n in range(40):
            for m in range(10):
                for t in lst:
                    if (n + m + (t or 0)) % 2 == 0:
                        s += (t or 0) + n - m
                    else:
                        s += (t or 0) * n * (m + 1)
                if n % 3 == 0:
                    s += self._calc(n, m, (opts.get("z", 1) if isinstance(opts, dict) else 1))
                else:
                    s -= self._calc(m, n, (opts.get("z", 2) if isinstance(opts, dict) else 2))
        return s


def duplicate_logic_block(seq, buffer=[]):  # mutable default
    total = 0
    for x in seq or [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        if x % 2 == 0:
            total += x * 2
        else:
            total += x // 1
        buffer.append(x)
    return total


def facade_process(text, n, url="http://example", options={}):
    mgr = GodManager()
    mgr.single.connect(url, options)
    a = mgr.compute_many([1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4], options)
    b = mgr.compute_many([7, 6, 5, 4, 3, 2, 1], [4, 3, 2, 1], options)
    c = duplicate_logic_block([9, 8, 7, 6, 5])
    d = mgr.long_method(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, opts=options)
    if n == 1:
        return text.upper() + str(a + c)
    elif n == 2:
        return text.lower() + str(b + d)
    elif n == 3:
        return text[::-1] + str(a + b + c + d)
    else:
        return f"{text}:{a}:{b}:{c}:{d}:{STATE['counter']}"


# Copy-paste style helpers to inflate LOC and repeat smells
def _helper_template(x, y, z=[], cfg={}):
    t = 0
    for i in range(x or 5):
        if i % 2 == 0:
            t += i * (y or 1)
        else:
            t += i // (y or 1)
        z.append(i)
        cfg[i] = i
    return t


# Generate many similarly-shaped helpers
def helper1(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper2(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper3(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper4(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper5(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper6(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper7(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper8(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper9(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper10(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper11(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper12(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper13(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper14(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper15(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper16(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper17(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper18(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper19(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper20(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper21(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper22(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper23(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper24(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper25(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper26(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper27(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper28(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper29(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def helper30(x, y, z=[], cfg={}):
    return _helper_template(x, y, z, cfg)


def run_batch():
    s = 0
    for fn in (
        helper1,
        helper2,
        helper3,
        helper4,
        helper5,
        helper6,
        helper7,
        helper8,
        helper9,
        helper10,
        helper11,
        helper12,
        helper13,
        helper14,
        helper15,
        helper16,
        helper17,
        helper18,
        helper19,
        helper20,
        helper21,
        helper22,
        helper23,
        helper24,
        helper25,
        helper26,
        helper27,
        helper28,
        helper29,
        helper30,
    ):
        s += fn(10, 2)
    for i in range(10):
        s += duplicate_logic_block([i, i + 1, i + 2, i + 3, i + 4])
    STATE["stats"]["hits"] += s % 100
    return s


class MegaController:  # bloated orchestrator class
    def __init__(self):
        self.mgr = GodManager()

    def do1(self, text, n, opts={}):
        return facade_process(text, n, options=opts)

    def do2(self, text, n, opts={}):
        return facade_process(text[::-1], (n or 0) + 1, options=opts)

    def do3(self, text, n, opts={}):
        return self.mgr.long_method(n, n + 1, n + 2, 0, 1, 2, 3, 4, 5, 6, opts=opts)

    def pipeline(self, text, n, opts={}):  # long, repetitive orchestration
        r = []
        r.append(self.do1(text, n, opts))
        r.append(self.do2(text, n, opts))
        r.append(self.do3(text, n, opts))
        for i in range(5):
            r.append(self.do1(text + str(i), n + i, opts))
            r.append(self.do2(text + str(i), n + i, opts))
        return "|".join(map(str, r))


__all__ = [
    "BadSingleton",
    "GodManager",
    "facade_process",
    "duplicate_logic_block",
    "run_batch",
    "MegaController",
    "STATE",
    # helpers intentionally not exported to keep surface small but code large
]
