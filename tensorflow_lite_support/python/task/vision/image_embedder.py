# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
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
"""Image embedder task."""

import dataclasses
from typing import Optional

from tensorflow_lite_support.python.task.core.proto import base_options_pb2
from tensorflow_lite_support.python.task.processor.proto import bounding_box_pb2
from tensorflow_lite_support.python.task.processor.proto import embedding_options_pb2
from tensorflow_lite_support.python.task.processor.proto import embeddings_pb2
from tensorflow_lite_support.python.task.vision.core import tensor_image
from tensorflow_lite_support.python.task.vision.core.pybinds import image_utils
from tensorflow_lite_support.python.task.vision.pybinds import _pywrap_image_embedder
from tensorflow_lite_support.python.task.vision.pybinds import image_embedder_options_pb2

_ProtoImageEmbedderOptions = image_embedder_options_pb2.ImageEmbedderOptions
_CppImageEmbedder = _pywrap_image_embedder.ImageEmbedder
_BaseOptions = base_options_pb2.BaseOptions
_EmbeddingOptions = embedding_options_pb2.EmbeddingOptions


@dataclasses.dataclass
class ImageEmbedderOptions:
  """Options for the image embedder task."""
  base_options: _BaseOptions
  embedding_options: _EmbeddingOptions = _EmbeddingOptions()


class ImageEmbedder(object):
  """Class that performs dense feature vector extraction on images."""

  def __init__(self, options: ImageEmbedderOptions,
               cpp_embedder: _CppImageEmbedder) -> None:
    """Initializes the `ImageEmbedder` object."""
    # Creates the object of C++ ImageEmbedder class.
    self._options = options
    self._embedder = cpp_embedder

  @classmethod
  def create_from_file(cls, file_path: str) -> "ImageEmbedder":
    """Creates the `ImageEmbedder` object from a TensorFlow Lite model.

    Args:
      file_path: Path to the model.
    Returns:
      `ImageEmbedder` object that's created from the model file.
    Raises:
      status.StatusNotOk if failed to create `ImageEmbedder` object from the
      provided file such as invalid file.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    base_options = _BaseOptions(file_name=file_path)
    options = ImageEmbedderOptions(base_options=base_options)
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(cls,
                          options: ImageEmbedderOptions) -> "ImageEmbedder":
    """Creates the `ImageEmbedder` object from image embedder options.

    Args:
      options: Options for the image embedder task.
    Returns:
      `ImageEmbedder` object that's created from `options`.
    Raises:
      status.StatusNotOk if failed to create `ImageEmbdder` object from
        `ImageEmbedderOptions` such as missing the model.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    embedder = _CppImageEmbedder.create_from_options(options.base_options,
                                                     options.embedding_options)
    return cls(options, embedder)

  def embed(
      self,
      image: tensor_image.TensorImage,
      bounding_box: Optional[bounding_box_pb2.BoundingBox] = None
  ) -> embeddings_pb2.EmbeddingResult:
    """Performs actual feature vector extraction on the provided TensorImage.

    Args:
      image: Tensor image, used to extract the feature vectors.
      bounding_box: Bounding box, optional. If set, performed feature vector
        extraction only on the provided region of interest. Note that the region
        of interest is not clamped, so this method will fail if the region is
        out of bounds of the input image.

    Returns:
      embedding result.

    Raises:
      status.StatusNotOk if failed to get the embedding vector.
    """
    # TODO(b/220931229) Need to import the module to catch this error:
    # `from pybind11_abseil import status`,
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    image_data = image_utils.ImageData(image.buffer)
    if bounding_box is None:
      return self._embedder.embed(image_data)

    return self._embedder.embed(image_data, bounding_box)

  def get_embedding_by_index(self, result: embeddings_pb2.EmbeddingResult,
                             output_index: int) -> embeddings_pb2.Embedding:
    """Gets the embedding in the embedding result by `output_index`.

    Args:
      result: embedding result.
      output_index: output index of the output layer.

    Returns:
      The Embedding output by the output_index'th layer. In (the most common)
      case where a single embedding is produced, you can just call
      get_feature_vector_by_index(result, 0).

    Raises:
      ValueError if the output index is out of bound.
    """
    if output_index < 0 or output_index >= len(result.embeddings):
      raise ValueError("Output index is out of bound.")
    embedding = self._embedder.get_embedding_by_index(result, output_index)
    return embedding

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
  def options(self) -> ImageEmbedderOptions:
    return self._options
