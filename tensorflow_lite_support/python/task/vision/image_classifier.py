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
"""Image classifier task."""

import dataclasses
from typing import Optional

from tensorflow_lite_support.python.task.core.proto import base_options_pb2
from tensorflow_lite_support.python.task.processor.proto import bounding_box_pb2
from tensorflow_lite_support.python.task.processor.proto import classification_options_pb2
from tensorflow_lite_support.python.task.processor.proto import classifications_pb2
from tensorflow_lite_support.python.task.vision.core import tensor_image
from tensorflow_lite_support.python.task.vision.core.pybinds import image_utils
from tensorflow_lite_support.python.task.vision.pybinds import _pywrap_image_classifier
from tensorflow_lite_support.python.task.vision.pybinds import image_classifier_options_pb2

_ProtoImageClassifierOptions = image_classifier_options_pb2.ImageClassifierOptions
_CppImageClassifier = _pywrap_image_classifier.ImageClassifier
_ClassificationOptions = classification_options_pb2.ClassificationOptions
_BaseOptions = base_options_pb2.BaseOptions


@dataclasses.dataclass
class ImageClassifierOptions:
  """Options for the image classifier task."""
  base_options: _BaseOptions
  classification_options: _ClassificationOptions = _ClassificationOptions()


class ImageClassifier(object):
  """Class that performs classification on images."""

  def __init__(self, options: ImageClassifierOptions,
               classifier: _CppImageClassifier) -> None:
    """Initializes the `ImageClassifier` object."""
    # Creates the object of C++ ImageClassifier class.
    self._options = options
    self._classifier = classifier

  @classmethod
  def create_from_file(cls, file_path: str) -> "ImageClassifier":
    """Creates the `ImageClassifier` object from a TensorFlow Lite model.

    Args:
      file_path: Path to the model.
    Returns:
      `ImageClassifier` object that's created from the model file.
    Raises:
      status.StatusNotOk if failed to create `ImageClassifier` object from the
      provided file such as invalid file.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    base_options = _BaseOptions(file_name=file_path)
    options = ImageClassifierOptions(base_options=base_options)
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(cls,
                          options: ImageClassifierOptions) -> "ImageClassifier":
    """Creates the `ImageClassifier` object from image classifier options.

    Args:
      options: Options for the image classifier task.
    Returns:
      `ImageClassifier` object that's created from `options`.
    Raises:
      status.StatusNotOk if failed to create `ImageClassifier` object from
      `ImageClassifierOptions` such as missing the model.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    classifier = _CppImageClassifier.create_from_options(
        options.base_options, options.classification_options)
    return cls(options, classifier)

  def classify(
      self,
      image: tensor_image.TensorImage,
      bounding_box: Optional[bounding_box_pb2.BoundingBox] = None
  ) -> classifications_pb2.ClassificationResult:
    """Performs classification on the provided TensorImage.

    Args:
      image: Tensor image, used to extract the feature vectors.
      bounding_box: Bounding box, optional. If set, performed feature vector
        extraction only on the provided region of interest. Note that the region
        of interest is not clamped, so this method will fail if the region is
        out of bounds of the input image.
    Returns:
      classification result.
    Raises:
      status.StatusNotOk if failed to get the feature vector. Need to import the
        module to catch this error: `from pybind11_abseil
        import status`, see
        https://github.com/pybind/pybind11_abseil#abslstatusor.
    """
    image_data = image_utils.ImageData(image.buffer)
    if bounding_box is None:
      return self._classifier.classify(image_data)

    return self._classifier.classify(image_data, bounding_box)

  @property
  def options(self) -> ImageClassifierOptions:
    return self._options
