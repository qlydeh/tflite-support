# Copyright 2022 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Text embedder task."""

import dataclasses

from tensorflow_lite_support.python.task.core.proto import base_options_pb2
from tensorflow_lite_support.python.task.processor.proto import embedding_options_pb2
from tensorflow_lite_support.python.task.processor.proto import embeddings_pb2
from tensorflow_lite_support.python.task.text.pybinds import _pywrap_text_embedder
from tensorflow_lite_support.python.task.text.pybinds import text_embedder_options_pb2

_ProtoTextEmbedderOptions = text_embedder_options_pb2.TextEmbedderOptions
_CppTextEmbedder = _pywrap_text_embedder.TextEmbedder
_BaseOptions = base_options_pb2.BaseOptions
_EmbeddingOptions = embedding_options_pb2.EmbeddingOptions


@dataclasses.dataclass
class TextEmbedderOptions:
  """Options for the text embedder task."""
  base_options: _BaseOptions
  embedding_options: _EmbeddingOptions = _EmbeddingOptions()


class TextEmbedder(object):
  """Class that performs dense feature vector extraction on text."""

  def __init__(self, options: TextEmbedderOptions,
               cpp_embedder: _CppTextEmbedder) -> None:
    """Initializes the `TextEmbedder` object."""
    # Creates the object of C++ TextEmbedder class.
    self._options = options
    self._embedder = cpp_embedder

  @classmethod
  def create_from_file(cls, file_path: str) -> "TextEmbedder":
    """Creates the `TextEmbedder` object from a TensorFlow Lite model.

    Args:
      file_path: Path to the model.

    Returns:
      `TextEmbedder` object that's created from the model file.
    Raises:
      status.StatusNotOk if failed to create `TextEmbedder` object from the
      provided file such as invalid file.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    base_options = _BaseOptions(file_name=file_path)
    options = TextEmbedderOptions(base_options=base_options)
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(cls, options: TextEmbedderOptions) -> "TextEmbedder":
    """Creates the `TextEmbedder` object from text embedder options.

    Args:
      options: Options for the text embedder task.

    Returns:
      `TextEmbedder` object that's created from `options`.
    Raises:
      status.StatusNotOk if failed to create `TextEmbdder` object from
        `TextEmbedderOptions` such as missing the model.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    embedder = _CppTextEmbedder.create_from_options(options.base_options,
                                                    options.embedding_options)
    return cls(options, embedder)

  def embed(self, text: str) -> embeddings_pb2.EmbeddingResult:
    """Performs actual feature vector extraction on the provided text.

    Args:
      text: the input text, used to extract the feature vectors.

    Returns:
      embedding result.

    Raises:
      status.StatusNotOk if failed to get the embedding vector.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    return self._embedder.embed(text)

  def cosine_similarity(self, u: embeddings_pb2.FeatureVector,
                        v: embeddings_pb2.FeatureVector) -> float:
    """Computes cosine similarity [1] between two feature vectors."""
    return self._embedder.cosine_similarity(u, v)

  def get_embedding_dimension(self, output_index: int) -> int:
    """Gets the dimensionality of the embedding output.

    Args:
      output_index: The output index of output layer.

    Returns:
      Dimensionality of the embedding output by the output_index'th output
      layer. Returns -1 if `output_index` is out of bounds.
    """
    return self._embedder.get_embedding_dimension(output_index)

  @property
  def number_of_output_layers(self) -> int:
    """Gets the number of output layers of the model."""
    return self._embedder.get_number_of_output_layers()

  @property
  def options(self) -> TextEmbedderOptions:
    return self._options
