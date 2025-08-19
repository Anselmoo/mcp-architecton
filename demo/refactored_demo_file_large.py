"""
Refactored demo using the Facade pattern.

This file intentionally replaces the heavy, framework-specific demo with a
lightweight, dependency-free example that illustrates the Facade pattern.

Contract (informal):
- Inputs: sequences of numbers (x) and labels (y). Keep it simple for a demo.
- Facade exposes: fit, predict, evaluate, export_model.
- Internals: small subsystems (preprocessing, model building, training).

The subsystems are kept minimal so the demo runs without extra packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


# --------------------------- Subsystems (internal) ---------------------------


class _DataPreprocessor:
    """Simple preprocessor that can normalize numeric inputs.

    For a demo, we only compute and apply (x - mean) / std when enabled.
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


class _TunerSelector:
    """Selects a tuning strategy (mocked for demo purposes)."""

    _VALID = {"greedy", "random", "hyperband", "bayesian"}

    def __init__(
        self, name: str = "greedy", max_trials: int = 100, seed: Optional[int] = None
    ) -> None:
        if name not in self._VALID:
            raise ValueError(f"Unknown tuner '{name}'. Allowed: {sorted(self._VALID)}")
        self.name = name
        self.max_trials = int(max_trials)
        self.seed = seed

    def describe(self) -> str:
        return f"Tuner(name={self.name}, max_trials={self.max_trials}, seed={self.seed})"


class _SimpleModel:
    """A tiny model that learns the average of y and predicts that constant.

    - fit: stores the mean of y
    - predict: returns that mean for each x
    - evaluate: reports MAE against y
    """

    def __init__(self) -> None:
        self._bias: float = 0.0
        self._fitted: bool = False

    @staticmethod
    def _to_floats(data: Iterable[float]) -> List[float]:
        return [float(v) for v in data]

    def fit(self, x: Iterable[float], y: Iterable[float]) -> None:  # noqa: ARG002 (x unused for this simple model)
        labels = self._to_floats(y)
        if labels:
            self._bias = sum(labels) / len(labels)
        else:
            self._bias = 0.0
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
        mae = sum(abs(preds[i] - labels[i]) for i in range(n)) / n
        return mae


# ------------------------------- Public Facade -------------------------------


@dataclass
class TrainingHistory:
    """Minimal training history for the demo."""

    tuner: str
    trials_run: int
    metric_name: str
    metric_value: float


class AutoModelFacade:
    """Facade that streamlines pipeline setup and usage.

    It hides the details of preprocessing, (mock) tuning, model building,
    and the training/eval loop behind a small, easy-to-use API.
    """

    def __init__(
        self,
        *,
        tuner: str = "greedy",
        max_trials: int = 100,
        project_name: str = "auto_model",
        directory: Optional[str] = None,
        seed: Optional[int] = None,
        normalize: bool = True,
    ) -> None:
        self.project_name = project_name
        self.directory = directory
        self._pre = _DataPreprocessor(normalize=normalize)
        self._tuner = _TunerSelector(name=tuner, max_trials=max_trials, seed=seed)
        self._model = _SimpleModel()
        self._last_history: Optional[TrainingHistory] = None

    # ------------------------------- Core API -------------------------------

    def fit(
        self,
        x: Iterable[float],
        y: Iterable[float],
        *,
        metric_name: str = "mae",
    ) -> TrainingHistory:
        """Fit the model and return a minimal training history.

        For a demo, we run a single "best" trial using the chosen tuner name
        (no actual search), and compute the metric on the training set.
        """
        x_proc = self._pre.fit_transform(x)
        self._model.fit(x_proc, y)
        metric = self._model.evaluate(x_proc, y)
        history = TrainingHistory(
            tuner=self._tuner.describe(),
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


__all__ = ["AutoModelFacade", "TrainingHistory"]
