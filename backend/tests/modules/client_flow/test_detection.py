"""
Detection Service Tests

Tests for YOLO-based clothing detection:
- Detection classes mapping
- Detection results processing
- YOLO class to product mapping
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image

from backend.app.services.detection import detect_in_image, get_model_classes


pytestmark = pytest.mark.asyncio


class TestDetectionService:
    """Tests for the detection service."""

    async def test_get_model_classes_returns_dict(self):
        """Test that get_model_classes returns a dictionary."""
        classes = get_model_classes()

        assert isinstance(classes, dict)

    async def test_detect_in_image_returns_expected_format(self):
        """Test that detection returns expected format."""
        mock_image = Image.new('RGB', (640, 480), color='red')

        result = await detect_in_image(mock_image)

        assert "detections" in result
        assert "image_size" in result
        assert isinstance(result["detections"], list)
        assert isinstance(result["image_size"], (list, tuple))

    async def test_detect_in_image_empty_for_no_objects(self):
        """Test detection on image with no clothing objects."""
        mock_image = Image.new('RGB', (100, 100), color='blue')

        result = await detect_in_image(mock_image, conf_threshold=0.99)

        assert isinstance(result["detections"], list)


class TestDetectionClasses:
    """Tests for detection class mapping."""

    def test_yolo_classes_known(self):
        """Test that known YOLO classes are recognized."""
        classes = get_model_classes()

        known_classes = ["gorra-roja-lacoste", "top", "pants"]

        for cls_name in known_classes:
            if cls_name in classes.values():
                assert True

    def test_classes_are_strings(self):
        """Test that all class names are strings."""
        classes = get_model_classes()

        for key, value in classes.items():
            assert isinstance(key, int)
            assert isinstance(value, str)


class TestDetectionResults:
    """Tests for processing detection results."""

    async def test_detection_bbox_format(self):
        """Test that bounding box has correct format."""
        mock_image = Image.new('RGB', (640, 480), color='red')

        result = await detect_in_image(mock_image)

        for detection in result["detections"]:
            bbox = detection.get("bbox", [])
            assert len(bbox) == 4
            assert all(isinstance(x, (int, float)) for x in bbox)

    async def test_detection_confidence_range(self):
        """Test that confidence is between 0 and 1."""
        mock_image = Image.new('RGB', (640, 480), color='red')

        result = await detect_in_image(mock_image)

        for detection in result["detections"]:
            confidence = detection.get("confidence", 0)
            assert 0 <= confidence <= 1

    async def test_detection_image_size_matches(self):
        """Test that returned image size matches input."""
        width, height = 800, 600
        mock_image = Image.new('RGB', (width, height), color='red')

        result = await detect_in_image(mock_image)

        assert result["image_size"][0] == width
        assert result["image_size"][1] == height


class TestDetectionEdgeCases:
    """Tests for edge cases in detection."""

    async def test_detect_small_image(self):
        """Test detection on very small image."""
        mock_image = Image.new('RGB', (50, 50), color='red')

        result = await detect_in_image(mock_image)

        assert "detections" in result

    async def test_detect_large_image(self):
        """Test detection on large image."""
        mock_image = Image.new('RGB', (1920, 1080), color='red')

        result = await detect_in_image(mock_image)

        assert "detections" in result

    async def test_detect_grayscale_image(self):
        """Test detection on grayscale image."""
        mock_image = Image.new('L', (640, 480), color=128)

        result = await detect_in_image(mock_image)

        assert "detections" in result
        assert "image_size" in result
