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
"""Tests for object detector."""

import enum
import json

from absl.testing import parameterized
# TODO(b/220067158): Change to import tensorflow and leverage tf.test once
# fixed the dependency issue.
from google.protobuf import json_format
import unittest
from tensorflow_lite_support.python.task.core.proto import base_options_pb2
from tensorflow_lite_support.python.task.processor.proto import bounding_box_pb2
from tensorflow_lite_support.python.task.processor.proto import class_pb2
from tensorflow_lite_support.python.task.processor.proto import detection_options_pb2
from tensorflow_lite_support.python.task.processor.proto import detections_pb2
from tensorflow_lite_support.python.task.vision import object_detector
from tensorflow_lite_support.python.task.vision.core import tensor_image
from tensorflow_lite_support.python.test import base_test
from tensorflow_lite_support.python.test import test_util

_BaseOptions = base_options_pb2.BaseOptions
_ObjectDetector = object_detector.ObjectDetector
_ObjectDetectorOptions = object_detector.ObjectDetectorOptions

_MODEL_FILE = 'coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.tflite'
_IMAGE_FILE = 'cats_and_dogs.jpg'
_EXPECTED_DETECTIONS = [
    ({
        'origin_x': 54,
        'origin_y': 396,
        'width': 393,
        'height': 196
    }, {
        'index': 16,
        'score': 0.64453125,
        'class_name': 'cat'
    }),
    ({
        'origin_x': 602,
        'origin_y': 157,
        'width': 394,
        'height': 447
    }, {
        'index': 16,
        'score': 0.59765625,
        'class_name': 'cat'
    }),
    ({
        'origin_x': 261,
        'origin_y': 394,
        'width': 179,
        'height': 209
    }, {
        'index': 16,
        'score': 0.5625,
        'class_name': 'cat'
    }),
    ({
        'origin_x': 389,
        'origin_y': 197,
        'width': 276,
        'height': 409
    }, {
        'index': 17,
        'score': 0.51171875,
        'class_name': 'dog'
    })
]
_ALLOW_LIST = ['cat', 'dog']
_DENY_LIST = ['cat']
_SCORE_THRESHOLD = 0.3
_MAX_RESULTS = 3
_ACCEPTABLE_ERROR_RANGE = 0.000001


class ModelFileType(enum.Enum):
  FILE_CONTENT = 1
  FILE_NAME = 2


class ObjectDetectorTest(parameterized.TestCase, base_test.BaseTestCase):

  def setUp(self):
    super().setUp()
    self.test_image_path = test_util.get_test_data_path(_IMAGE_FILE)
    self.model_path = test_util.get_test_data_path(_MODEL_FILE)

  @classmethod
  def create_detector_from_options(cls, base_options, **detection_options):
    detection_options = detection_options_pb2.DetectionOptions(
        **detection_options)
    options = _ObjectDetectorOptions(
        base_options=base_options, detection_options=detection_options)
    detector = _ObjectDetector.create_from_options(options)
    return detector

  @classmethod
  def build_test_data(cls, expected_detections):
    expected_result = detections_pb2.DetectionResult()

    for index in range(len(expected_detections)):
      bounding_box, category = expected_detections[index]
      detection = detections_pb2.Detection()
      detection.bounding_box.CopyFrom(
          bounding_box_pb2.BoundingBox(**bounding_box))
      detection.classes.append(class_pb2.Category(**category))
      expected_result.detections.append(detection)

    expected_result_dict = json.loads(
        json_format.MessageToJson(expected_result))

    return expected_result_dict

  def test_create_from_file_succeeds_with_valid_model_path(self):
    # Creates with default option and valid model file successfully.
    detector = _ObjectDetector.create_from_file(self.model_path)
    self.assertIsInstance(detector, _ObjectDetector)

  def test_create_from_options_succeeds_with_valid_model_path(self):
    # Creates with options containing model file successfully.
    base_options = _BaseOptions(file_name=self.model_path)
    options = _ObjectDetectorOptions(base_options=base_options)
    detector = _ObjectDetector.create_from_options(options)
    self.assertIsInstance(detector, _ObjectDetector)

  def test_create_from_options_fails_with_invalid_model_path(self):
    # Invalid empty model path.
    with self.assertRaisesRegex(
        Exception,
        r'INVALID_ARGUMENT: ExternalFile must specify at least one of '
        r"'file_content', 'file_name' or 'file_descriptor_meta'. "
        r"\[tflite::support::TfLiteSupportStatus='2']"):
      base_options = _BaseOptions(file_name='')
      options = _ObjectDetectorOptions(base_options=base_options)
      _ObjectDetector.create_from_options(options)

  def test_create_from_options_succeeds_with_valid_model_content(self):
    # Creates with options containing model content successfully.
    with open(self.model_path, 'rb') as f:
      base_options = _BaseOptions(file_content=f.read())
      options = _ObjectDetectorOptions(base_options=base_options)
      detector = _ObjectDetector.create_from_options(options)
      self.assertIsInstance(detector, _ObjectDetector)

  @parameterized.parameters(
      (ModelFileType.FILE_NAME, 4, _EXPECTED_DETECTIONS),
      (ModelFileType.FILE_CONTENT, 4, _EXPECTED_DETECTIONS))
  def test_detect_model(self, model_file_type, max_results,
                        expected_detections):
    # Creates detector.
    if model_file_type is ModelFileType.FILE_NAME:
      base_options = _BaseOptions(file_name=self.model_path)
    elif model_file_type is ModelFileType.FILE_CONTENT:
      with open(self.model_path, 'rb') as f:
        model_content = f.read()
      base_options = _BaseOptions(file_content=model_content)
    else:
      # Should never happen
      raise ValueError('model_file_type is invalid.')

    detector = self.create_detector_from_options(
        base_options, max_results=max_results)

    # Loads image.
    image = tensor_image.TensorImage.create_from_file(self.test_image_path)

    # Performs object detection on the input.
    image_result = detector.detect(image)
    image_result_dict = json.loads(json_format.MessageToJson(image_result))

    # Builds test data.
    expected_result_dict = self.build_test_data(expected_detections)

    # Comparing results.
    self.assertDeepAlmostEqual(
        image_result_dict, expected_result_dict, delta=_ACCEPTABLE_ERROR_RANGE)

  def test_score_threshold_option(self):
    # Creates detector.
    base_options = _BaseOptions(file_name=self.model_path)
    detector = self.create_detector_from_options(
        base_options, score_threshold=_SCORE_THRESHOLD)

    # Loads image.
    image = tensor_image.TensorImage.create_from_file(self.test_image_path)

    # Performs object detection on the input.
    image_result = detector.detect(image)
    image_result_dict = json.loads(json_format.MessageToJson(image_result))

    categories = image_result_dict['detections']

    for category in categories:
      score = category['classes'][0]['score']
      self.assertGreaterEqual(
          score, _SCORE_THRESHOLD,
          'Classification with score lower than threshold found. {0}'.format(
              category))

  def test_max_results_option(self):
    # Creates detector.
    base_options = _BaseOptions(file_name=self.model_path)
    detector = self.create_detector_from_options(
        base_options, max_results=_MAX_RESULTS)

    # Loads image.
    image = tensor_image.TensorImage.create_from_file(self.test_image_path)

    # Performs object detection on the input.
    image_result = detector.detect(image)
    image_result_dict = json.loads(json_format.MessageToJson(image_result))
    detections = image_result_dict['detections']

    self.assertLessEqual(
        len(detections), _MAX_RESULTS, 'Too many results returned.')

  def test_allow_list_option(self):
    # Creates detector.
    base_options = _BaseOptions(file_name=self.model_path)
    detector = self.create_detector_from_options(
        base_options, class_name_allowlist=_ALLOW_LIST)

    # Loads image.
    image = tensor_image.TensorImage.create_from_file(self.test_image_path)

    # Performs object detection on the input.
    image_result = detector.detect(image)
    image_result_dict = json.loads(json_format.MessageToJson(image_result))

    categories = image_result_dict['detections']

    for category in categories:
      label = category['classes'][0]['className']
      self.assertIn(
          label, _ALLOW_LIST,
          'Label "{0}" found but not in label allow list'.format(label))

  def test_deny_list_option(self):
    # Creates detector.
    base_options = _BaseOptions(file_name=self.model_path)
    detector = self.create_detector_from_options(
        base_options, class_name_denylist=_DENY_LIST)

    # Loads image.
    image = tensor_image.TensorImage.create_from_file(self.test_image_path)

    # Performs object detection on the input.
    image_result = detector.detect(image)
    image_result_dict = json.loads(json_format.MessageToJson(image_result))

    categories = image_result_dict['detections']

    for category in categories:
      label = category['classes'][0]['className']
      self.assertNotIn(label, _DENY_LIST,
                       'Label "{0}" found but in deny list.'.format(label))

  def test_combined_allowlist_and_denylist(self):
    # Fails with combined allowlist and denylist
    with self.assertRaisesRegex(
        Exception,
        r'INVALID_ARGUMENT: `class_name_whitelist` and `class_name_blacklist` '
        r'are mutually exclusive options. '
        r"\[tflite::support::TfLiteSupportStatus='2'\]"):
      base_options = _BaseOptions(file_name=self.model_path)
      detection_options = detection_options_pb2.DetectionOptions(
          class_name_allowlist=['foo'], class_name_denylist=['bar'])
      options = _ObjectDetectorOptions(
          base_options=base_options, detection_options=detection_options)
      _ObjectDetector.create_from_options(options)


if __name__ == '__main__':
  unittest.main()
