from __future__ import annotations

import ast

from mcp_architecton.detectors import registry

_SAMPLE = """
class A: pass
class B: pass

class Context:
    def __init__(self):
        self.state = None

def factory():
    return A()

def create():
    return B()

def singleton():
    if not hasattr(singleton, '_i'):
        singleton._i = A()  # noqa: SLF001
    return singleton._i

def command_handler(cmd):
    if cmd == 'x':
        return factory()
    return None
"""


def test_all_detectors_invoke() -> None:
    tree = ast.parse(_SAMPLE)
    total = 0
    for name, detector in registry.items():
        try:
            detector(tree, _SAMPLE)  # execution for coverage; result not asserted
            total += 1
        except Exception:  # noqa: BLE001
            # Detectors are heuristic; ignore failures in smoke test
            continue
    assert total == len(registry)
