from __future__ import annotations

from typing import Any


class UnitOfWork:
    def __init__(self, session_factory: Any):
        self.session_factory = session_factory
        self.session: Any | None = None

    def __enter__(self):
        self.session = self.session_factory()
        self.begin()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rollback()
        else:
            self.commit()

    def begin(self):
        # start tx
        return None

    def commit(self):
        assert self.session is not None
        self.session.commit()

    def rollback(self):
        if self.session is not None:
            self.session.rollback()
