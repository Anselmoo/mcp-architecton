"""
Refactored AutoModel applying the Strategy pattern for tuner selection.

This mirrors the behavior of demo_file_large.AutoModel but injects a
TunerSelectionStrategy to resolve the tuner from a name or class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Type, Union, Dict

import keras
import numpy as np
import tensorflow as tf
import tree

from autokeras import blocks
from autokeras import graph as graph_module
from autokeras import pipeline
from autokeras import tuners
from autokeras.engine import head as head_module
from autokeras.engine import node as node_module
from autokeras.engine import tuner as tuner_module
from autokeras.nodes import Input
from autokeras.utils import data_utils
from autokeras.utils import utils


class TunerSelectionStrategy(ABC):
    """Strategy interface for resolving a tuner.

    Contract
    - input: a tuner identifier (str or subclass of AutoTuner)
    - output: a subclass of AutoTuner suitable for instantiation
    - errors: ValueError on unknown string identifiers
    """

    @abstractmethod
    def resolve(
        self, tuner: Union[str, Type[tuner_module.AutoTuner]]
    ) -> Type[tuner_module.AutoTuner]:
        raise NotImplementedError


class MappingTunerSelectionStrategy(TunerSelectionStrategy):
    """Resolves tuner by looking up a mapping of name -> class."""

    def __init__(self, mapping: Dict[str, Type[tuner_module.AutoTuner]]):
        self._mapping = dict(mapping)

    def resolve(
        self, tuner: Union[str, Type[tuner_module.AutoTuner]]
    ) -> Type[tuner_module.AutoTuner]:
        if isinstance(tuner, str) and tuner in self._mapping:
            return self._mapping[tuner]
        raise ValueError(
            "Expected the tuner argument to be one of {keys}, but got {tuner}".format(
                keys=sorted(self._mapping.keys()), tuner=tuner
            )
        )


TUNER_CLASSES: Dict[str, Type[tuner_module.AutoTuner]] = {
    "bayesian": tuners.BayesianOptimization,
    "random": tuners.RandomSearch,
    "hyperband": tuners.Hyperband,
    "greedy": tuners.Greedy,
}


def get_tuner_class(tuner: Union[str, Type[tuner_module.AutoTuner]]):
    if isinstance(tuner, str) and tuner in TUNER_CLASSES:
        return TUNER_CLASSES.get(tuner)
    else:
        raise ValueError(
            'Expected the tuner argument to be one of "greedy", '
            '"random", "hyperband", or "bayesian", '
            "but got {tuner}".format(tuner=tuner)
        )


class AutoModel(object):
    """A Model defined by inputs and outputs, with Strategy for tuner selection.

    The public API mirrors the original AutoModel to make this drop-in for demo purposes.
    """

    def __init__(
        self,
        inputs: Union[Input, List[Input]],
        outputs: Union[head_module.Head, node_module.Node, list],
        project_name: str = "auto_model",
        max_trials: int = 100,
        directory: Union[str, Path, None] = None,
        objective: str = "val_loss",
        tuner: Union[str, Type[tuner_module.AutoTuner]] = "greedy",
        overwrite: bool = False,
        seed: Optional[int] = None,
        max_model_size: Optional[int] = None,
        tuner_strategy: Optional[TunerSelectionStrategy] = None,
        **kwargs,
    ):
        self.inputs = tree.flatten(inputs)
        self.outputs = tree.flatten(outputs)
        self.seed = seed
        if seed:
            np.random.seed(seed)
            tf.random.set_seed(seed)

        # Inject Strategy (defaults to mapping-based)
        self._tuner_strategy = tuner_strategy or MappingTunerSelectionStrategy(TUNER_CLASSES)

        # Initialize the hyper_graph.
        graph = self._build_graph()

        # Use Strategy for string tuner identifiers
        if isinstance(tuner, str):
            tuner = self._tuner_strategy.resolve(tuner)

        self.tuner = tuner(
            hypermodel=graph,
            overwrite=overwrite,
            objective=objective,
            max_trials=max_trials,
            directory=directory,
            seed=self.seed,
            project_name=project_name,
            max_model_size=max_model_size,
            **kwargs,
        )
        self.overwrite = overwrite
        self._heads = [output_node.in_blocks[0] for output_node in self.outputs]

    @property
    def objective(self):
        return self.tuner.objective

    @property
    def max_trials(self):
        return self.tuner.max_trials

    @property
    def directory(self):
        return self.tuner.directory

    @property
    def project_name(self):
        return self.tuner.project_name

    def _assemble(self):
        """Assemble the Blocks based on the input output nodes."""
        inputs = tree.flatten(self.inputs)
        outputs = tree.flatten(self.outputs)

        middle_nodes = [input_node.get_block()(input_node) for input_node in inputs]

        # Merge the middle nodes.
        if len(middle_nodes) > 1:
            output_node = blocks.Merge()(middle_nodes)
        else:
            output_node = middle_nodes[0]

        outputs = tree.flatten([output_blocks(output_node) for output_blocks in outputs])
        return graph_module.Graph(inputs=inputs, outputs=outputs)

    def _build_graph(self):
        # Using functional API.
        if all([isinstance(output, node_module.Node) for output in self.outputs]):
            graph = graph_module.Graph(inputs=self.inputs, outputs=self.outputs)
        # Using input/output API.
        elif all([isinstance(output, head_module.Head) for output in self.outputs]):
            # Clear session to reset get_uid(). The names of the blocks will
            # start to count from 1 for new blocks in a new AutoModel afterwards.
            keras.backend.clear_session()
            graph = self._assemble()
            self.outputs = graph.outputs
            keras.backend.clear_session()

        return graph

    def fit(
        self,
        x=None,
        y=None,
        batch_size=32,
        epochs=None,
        callbacks=None,
        validation_split=0.2,
        validation_data=None,
        verbose=1,
        **kwargs,
    ):
        """Search for the best model and hyperparameters for the AutoModel."""
        # Check validation information.
        if not validation_data and not validation_split:
            raise ValueError(
                "Either validation_data or a non-zero validation_split should be provided."
            )

        if validation_data:
            validation_split = 0

        dataset, validation_data = self._convert_to_dataset(
            x=x, y=y, validation_data=validation_data, batch_size=batch_size
        )
        self._analyze_data(dataset)
        self._build_hyper_pipeline(dataset)

        # Split the data with validation_split.
        if validation_data is None and validation_split:
            dataset, validation_data = data_utils.split_dataset(dataset, validation_split)

        history = self.tuner.search(
            x=dataset,
            epochs=epochs,
            callbacks=callbacks,
            validation_data=validation_data,
            validation_split=validation_split,
            verbose=verbose,
            **kwargs,
        )

        return history

    def _adapt(self, dataset, hms, batch_size):
        if isinstance(dataset, tf.data.Dataset):
            sources = data_utils.unzip_dataset(dataset)
        else:
            sources = tree.flatten(dataset)
        adapted = []
        for source, hm in zip(sources, hms):
            source = hm.get_adapter().adapt(source, batch_size)
            adapted.append(source)
        if len(adapted) == 1:
            return adapted[0]
        return tf.data.Dataset.zip(tuple(adapted))

    def _check_data_format(self, dataset, validation=False, predict=False):
        """Check if the dataset has the same number of IOs with the model."""
        if validation:
            in_val = " in validation_data"
            if isinstance(dataset, tf.data.Dataset):
                x = dataset
                y = None
            else:
                x, y = dataset
        else:
            in_val = ""
            x, y = dataset

        if isinstance(x, tf.data.Dataset) and y is not None:
            raise ValueError(
                "Expected y to be None when x is tf.data.Dataset{in_val}.".format(in_val=in_val)
            )

        if isinstance(x, tf.data.Dataset):
            if not predict:
                x_shapes, y_shapes = data_utils.dataset_shape(x)
                x_shapes = tree.flatten(x_shapes)
                y_shapes = tree.flatten(y_shapes)
            else:
                x_shapes = tree.flatten(data_utils.dataset_shape(x))
        else:
            x_shapes = [a.shape for a in tree.flatten(x)]
            if not predict:
                y_shapes = [a.shape for a in tree.flatten(y)]

        if len(x_shapes) != len(self.inputs):
            raise ValueError(
                "Expected x{in_val} to have {input_num} arrays, but got {data_num}".format(
                    in_val=in_val,
                    input_num=len(self.inputs),
                    data_num=len(x_shapes),
                )
            )
        if not predict and len(y_shapes) != len(self.outputs):
            raise ValueError(
                "Expected y{in_val} to have {output_num} arrays, but got {data_num}".format(
                    in_val=in_val,
                    output_num=len(self.outputs),
                    data_num=len(y_shapes),
                )
            )

    def _analyze_data(self, dataset):
        input_analysers = [node.get_analyser() for node in self.inputs]
        output_analysers = [head.get_analyser() for head in self._heads]
        analysers = input_analysers + output_analysers
        for x, y in dataset:
            x = tree.flatten(x)
            y = tree.flatten(y)
            for item, analyser in zip(x + y, analysers):
                analyser.update(item)

        for analyser in analysers:
            analyser.finalize()

        for hm, analyser in zip(self.inputs + self._heads, analysers):
            hm.config_from_analyser(analyser)

    def _build_hyper_pipeline(self, dataset):
        self.tuner.hyper_pipeline = pipeline.HyperPipeline(
            inputs=[node.get_hyper_preprocessors() for node in self.inputs],
            outputs=[head.get_hyper_preprocessors() for head in self._heads],
        )
        self.tuner.hypermodel.hyper_pipeline = self.tuner.hyper_pipeline

    def _convert_to_dataset(self, x, y, validation_data, batch_size):
        """Convert the data to tf.data.Dataset."""
        # Convert training data.
        self._check_data_format((x, y))
        if isinstance(x, tf.data.Dataset):
            dataset = x
            x = dataset.map(lambda x, y: x)
            y = dataset.map(lambda x, y: y)
        x = self._adapt(x, self.inputs, batch_size)
        y = self._adapt(y, self._heads, batch_size)
        dataset = tf.data.Dataset.zip((x, y))

        # Convert validation data
        if validation_data:
            self._check_data_format(validation_data, validation=True)
            if isinstance(validation_data, tf.data.Dataset):
                x = validation_data.map(lambda x, y: x)
                y = validation_data.map(lambda x, y: y)
            else:
                x, y = validation_data
            x = self._adapt(x, self.inputs, batch_size)
            y = self._adapt(y, self._heads, batch_size)
            validation_data = tf.data.Dataset.zip((x, y))

        return dataset, validation_data

    def _has_y(self, dataset):
        """Remove y from the tf.data.Dataset if exists."""
        shapes = data_utils.dataset_shape(dataset)
        # Only one or less element in the first level.
        if len(shapes) <= 1:
            return False
        # The first level has more than 1 element.
        # The tree has 2 levels.
        for shape in shapes:
            if isinstance(shape, tuple):
                return True
        # The tree has one level.
        # It matches the single IO case.
        return len(shapes) == 2 and len(self.inputs) == 1 and len(self.outputs) == 1

    def predict(self, x, batch_size=32, verbose=1, **kwargs):
        """Predict the output for a given testing data."""
        if isinstance(x, tf.data.Dataset) and self._has_y(x):
            x = x.map(lambda x, y: x)
        self._check_data_format((x, None), predict=True)
        dataset = self._adapt(x, self.inputs, batch_size)
        pipeline = self.tuner.get_best_pipeline()
        model = self.tuner.get_best_model()
        dataset = pipeline.transform_x(dataset)
        dataset = tf.data.Dataset.zip((dataset, dataset))
        y = model.predict(dataset, **kwargs)
        y = utils.predict_with_adaptive_batch_size(
            model=model, batch_size=batch_size, x=dataset, verbose=verbose, **kwargs
        )
        return pipeline.postprocess(y)

    def evaluate(self, x, y=None, batch_size=32, verbose=1, **kwargs):
        """Evaluate the best model for the given data."""
        self._check_data_format((x, y))
        if isinstance(x, tf.data.Dataset):
            dataset = x
            x = dataset.map(lambda x, y: x)
            y = dataset.map(lambda x, y: y)
        x = self._adapt(x, self.inputs, batch_size)
        y = self._adapt(y, self._heads, batch_size)
        dataset = tf.data.Dataset.zip((x, y))
        pipeline = self.tuner.get_best_pipeline()
        dataset = pipeline.transform(dataset)
        model = self.tuner.get_best_model()
        return utils.evaluate_with_adaptive_batch_size(
            model=model, batch_size=batch_size, x=dataset, verbose=verbose, **kwargs
        )

    def export_model(self):
        """Export the best Keras Model."""
        return self.tuner.get_best_model()
