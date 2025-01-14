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
"""TensorImage class."""

import numpy as np

from tensorflow_lite_support.python.task.vision.core import color_space_type
from tensorflow_lite_support.python.task.vision.core.pybinds import image_utils


class TensorImage(object):
  """Wrapper class for the Image object."""

  def __init__(self,
               image_data: image_utils.ImageData,
               is_from_file: bool = False) -> None:
    """Initializes the `TensorImage` object.

    Args:
      image_data: image_utils.ImageData, contains raw image data, width, height
        and channels info.
      is_from_file: boolean, whether `image_data` is loaded from the image file,
        if True, need to free the storage of ImageData in the destructor.
    """
    self._image_data = image_data
    self._is_from_file = is_from_file

    # Gets the FrameBuffer object.

  @classmethod
  def create_from_file(cls, file_name: str) -> "TensorImage":
    """Creates `TensorImage` object from the image file.

    Args:
      file_name: Image file name.

    Returns:
      `TensorImage` object.

    Raises:
      status.StatusNotOk if the image file can't be decoded. Need to import
        the module to catch this error: `from pybind11_abseil import status`,
        see https://github.com/pybind/pybind11_abseil#abslstatusor.
    """
    image_data = image_utils.DecodeImageFromFile(file_name)
    return cls(image_data, is_from_file=True)

  @classmethod
  def create_from_array(cls, array: np.ndarray) -> "TensorImage":
    """Creates `TensorImage` object from the numpy array.

    Args:
      array: numpy array with dtype=uint8. Its shape should be either (h, w, 3)
        or (1, h, w, 3) for RGB images, either (h, w) or (1, h, w) for GRAYSCALE
        images and either (h, w, 4) or (1, h, w, 4) for RGBA images.

    Returns:
        `TensorImage` object.

    Raises:
      ValueError if the dytype of the numpy array is not `uint8` or the
        dimention is not the valid dimention.
    """
    if array.dtype != np.uint8:
      raise ValueError("Expect numpy array with dtype=uint8.")

    image_data = image_utils.ImageData(np.squeeze(array))
    return cls(image_data)

  def __del__(self) -> None:
    """Destructor to free the storage of ImageData if loaded from the file."""
    if self._is_from_file:
      image_utils.ImageDataFree(self._image_data)

  @property
  def buffer(self) -> np.ndarray:
    """Gets the numpy array that represents `self.image_data`.

    Returns:
      Numpy array that represents `self.image_data` which is an
        `image_util.ImageData` object. To avoid copy, we will use
        `return np.array(..., copy = False)`. Therefore, this `TensorImage`
        object should out live the returned numpy array.
    """
    return np.array(self._image_data, copy=False)

  @property
  def height(self) -> int:
    """Gets the height of the image."""
    return self._image_data.height

  @property
  def width(self) -> int:
    """Gets the width of the image."""
    return self._image_data.width

  @property
  def color_space_type(self) -> color_space_type.ColorSpaceType:
    """Gets the color space type of the image."""
    channels = self._image_data.channels
    if channels == 1:
      return color_space_type.ColorSpaceType.GRAYSCALE
    elif channels == 3:
      return color_space_type.ColorSpaceType.RGB
    elif channels == 4:
      return color_space_type.ColorSpaceType.RGBA
    else:
      raise ValueError("Unsupported color space type.")
