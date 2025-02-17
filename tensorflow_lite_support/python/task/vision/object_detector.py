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
"""Object detector task."""

import dataclasses

from tensorflow_lite_support.python.task.core.proto import base_options_pb2
from tensorflow_lite_support.python.task.processor.proto import detection_options_pb2
from tensorflow_lite_support.python.task.processor.proto import detections_pb2
from tensorflow_lite_support.python.task.vision.core import tensor_image
from tensorflow_lite_support.python.task.vision.core.pybinds import image_utils
from tensorflow_lite_support.python.task.vision.pybinds import _pywrap_object_detector
from tensorflow_lite_support.python.task.vision.pybinds import object_detector_options_pb2

_ProtoObjectDetectorOptions = object_detector_options_pb2.ObjectDetectorOptions
_CppObjectDetector = _pywrap_object_detector.ObjectDetector
_BaseOptions = base_options_pb2.BaseOptions
_DetectionOptions = detection_options_pb2.DetectionOptions


@dataclasses.dataclass
class ObjectDetectorOptions:
  """Options for the object detector task."""
  base_options: _BaseOptions
  detection_options: _DetectionOptions = _DetectionOptions()


class ObjectDetector(object):
  """Class that performs object detection on images."""

  def __init__(self, options: ObjectDetectorOptions,
               detector: _CppObjectDetector) -> None:
    """Initializes the `ObjectDetector` object."""
    # Creates the object of C++ ObjectDetector class.
    self._options = options
    self._detector = detector

  @classmethod
  def create_from_file(cls, file_path: str) -> "ObjectDetector":
    """Creates the `ObjectDetector` object from a TensorFlow Lite model.

    Args:
      file_path: Path to the model.

    Returns:
      `ObjectDetector` object that's created from the model file.
    Raises:
      status.StatusNotOk if failed to create `ObjectDetector` object from the
      provided file such as invalid file.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    base_options = _BaseOptions(file_name=file_path)
    options = ObjectDetectorOptions(base_options=base_options)
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(cls,
                          options: ObjectDetectorOptions) -> "ObjectDetector":
    """Creates the `ObjectDetector` object from object detector options.

    Args:
      options: Options for the object detector task.

    Returns:
      `ObjectDetector` object that's created from `options`.
    Raises:
      status.StatusNotOk if failed to create `ObjectDetector` object from
        `ObjectDetectorOptions` such as missing the model.
    """
    # TODO(b/220931229): Raise RuntimeError instead of status.StatusNotOk.
    # Need to import the module to catch this error:
    # `from pybind11_abseil import status`
    # see https://github.com/pybind/pybind11_abseil#abslstatusor.
    detector = _CppObjectDetector.create_from_options(options.base_options,
                                                      options.detection_options)
    return cls(options, detector)

  def detect(self,
             image: tensor_image.TensorImage) -> detections_pb2.DetectionResult:
    """Performs object detection on the provided TensorImage.

    Args:
      image: Tensor image, used to extract the feature vectors.

    Returns:
      detection result.
    Raises:
      status.StatusNotOk if failed to get the feature vector. Need to import the
        module to catch this error: `from pybind11_abseil
        import status`, see
        https://github.com/pybind/pybind11_abseil#abslstatusor.
    """
    image_data = image_utils.ImageData(image.buffer)

    return self._detector.detect(image_data)
