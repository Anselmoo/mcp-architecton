from __future__ import annotations

from typing import Callable, Dict, list


class Observable:
	def __init__(self) -> None:
		self._subs: Dict[str, list[Callable]] = {}

	def subscribe(self, event: str, handler: Callable) -> None:
		self._subs.setdefault(event, []).append(handler)

	def notify(self, event: str, payload) -> None:  # pragma: no cover - scaffold
		for h in self._subs.get(event, []):
			h(payload)