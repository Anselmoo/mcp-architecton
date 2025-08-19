"""
Refactored demo using the Borg (Monostate) pattern.

All instances share the same state (configuration, preprocessing statistics,
and model parameters). This keeps the demo dependency-free and small, while
presenting a familiar API: fit, predict, evaluate, export_model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Tuple


# --------------------------- Utilities and subsystems ---------------------------


class _DataPreprocessor:
    """Simple numeric preprocessor: optional z-score normalization.

    For demonstration: computes mean/std on fit and applies (x - mean) / std.
    """

    def __init__(self, normalize: bool = True) -> None:
        self.normalize = normalize
        self._mean: Optional[float] = None
        self._std: Optional[float] = None

    @staticmethod
    def _to_floats(data: Iterable[float]) -> List[float]:
        return [float(v) for v in data]

    @staticmethod
    def _safe_std(values: Sequence[float]) -> float:
        if not values:
            return 1.0
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)
        return (var**0.5) or 1.0

    def fit(self, x: Iterable[float]) -> None:
        if not self.normalize:
            return
        values = self._to_floats(x)
        if not values:
            self._mean, self._std = 0.0, 1.0
            return
        self._mean = sum(values) / len(values)
        self._std = self._safe_std(values)

    def transform(self, x: Iterable[float]) -> List[float]:
        values = self._to_floats(x)
        if not self.normalize or self._mean is None or self._std is None:
            return values
        return [(v - self._mean) / self._std for v in values]

    def fit_transform(self, x: Iterable[float]) -> List[float]:
        self.fit(x)
        return self.transform(x)


class _SimpleModel:
    """A tiny model that predicts the mean(y) as a constant baseline.

    - fit: stores the mean of y
    - predict: returns that mean for each input
    - evaluate: mean absolute error (MAE)
    """

    def __init__(self) -> None:
        self._bias: float = 0.0
        self._fitted: bool = False

    @staticmethod
    def _to_floats(data: Iterable[float]) -> List[float]:
        return [float(v) for v in data]

    def fit(self, x: Iterable[float], y: Iterable[float]) -> None:  # noqa: ARG002 (x unused for this simple model)
        labels = self._to_floats(y)
        self._bias = sum(labels) / len(labels) if labels else 0.0
        self._fitted = True

    def predict(self, x: Iterable[float]) -> List[float]:
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        xs = self._to_floats(x)
        return [self._bias for _ in xs]

    def evaluate(self, x: Iterable[float], y: Iterable[float]) -> float:
        preds = self.predict(x)
        labels = self._to_floats(y)
        if not labels:
            return 0.0
        n = min(len(preds), len(labels))
        if n == 0:
            return 0.0
        return sum(abs(preds[i] - labels[i]) for i in range(n)) / n


# ------------------------------- Borg core ----------------------------------


class _Borg:
    """Monostate: instances share the same state dictionary."""

    __shared_state: dict[str, Any] = {}

    def __init__(self) -> None:
        # Redirect instance dict to the shared dict.
        self.__dict__ = self.__shared_state


@dataclass
class TrainingHistory:
    tuner: str
    trials_run: int
    metric_name: str
    metric_value: float


class AutoModelBorg(_Borg):
    """Facade-like API where all instances share state (Borg pattern).

    State shared across instances: project_name, directory, preprocessor,
    model parameters, and last history.
    """

    def __init__(
        self,
        *,
        project_name: str = "auto_model",
        directory: Optional[str] = None,
        normalize: bool = True,
        tuner: str = "greedy",
        max_trials: int = 100,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__()
        # Initialize shared state once.
        if not getattr(self, "_initialized", False):
            self.project_name = project_name
            self.directory = directory
            self.tuner = tuner
            self.max_trials = int(max_trials)
            self.seed = seed
            self._pre = _DataPreprocessor(normalize=normalize)
            self._model = _SimpleModel()
            self._last_history: Optional[TrainingHistory] = None
            self._initialized = True
        else:
            # Update a few configurable aspects optionally; keep others shared.
            self.project_name = project_name or self.project_name
            self.directory = directory or self.directory
            self.tuner = tuner or self.tuner
            self.max_trials = int(max_trials) if max_trials else self.max_trials
            self.seed = seed if seed is not None else self.seed
            # Normalization flag controls behavior of the shared preprocessor.
            self._pre.normalize = normalize

    # ------------------------------- API -----------------------------------

    def fit(
        self,
        x: Iterable[float],
        y: Iterable[float],
        *,
        metric_name: str = "mae",
    ) -> TrainingHistory:
        x_proc = self._pre.fit_transform(x)
        self._model.fit(x_proc, y)
        metric = self._model.evaluate(x_proc, y)
        history = TrainingHistory(
            tuner=f"Tuner(name={self.tuner}, max_trials={self.max_trials}, seed={self.seed})",
            trials_run=1,
            metric_name=metric_name,
            metric_value=metric,
        )
        self._last_history = history
        return history

    def predict(self, x: Iterable[float]) -> List[float]:
        x_proc = self._pre.transform(x)
        return self._model.predict(x_proc)

    def evaluate(
        self, x: Iterable[float], y: Iterable[float], *, metric_name: str = "mae"
    ) -> Tuple[str, float]:
        x_proc = self._pre.transform(x)
        value = self._model.evaluate(x_proc, y)
        return metric_name, value

    def export_model(self) -> _SimpleModel:
        return self._model


__all__ = ["AutoModelBorg", "TrainingHistory"]
