import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add parent directory to path so we can import search
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from search import _get_location, _get_video, NominatimAPIError, YouTubeAPIError, NetworkError


class TestGetLocation(unittest.TestCase):
    """Test cases for _get_location function."""

    @patch('search.requests.get')
    def test_get_location_success_city(self, mock_get):
        """Test successfully retrieving a city name."""
        mock_get.return_value.json.return_value = {
            "address": {
                "city": "Petaling Jaya",
                "town": None,
                "village": None
            }
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_location(3.3163, 101.5901)

        self.assertEqual(result, "Petaling Jaya")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("nominatim.openstreetmap.org", args[0])

    @patch('search.requests.get')
    def test_get_location_fallback_to_town(self, mock_get):
        """Test fallback to town when city is unavailable."""
        mock_get.return_value.json.return_value = {
            "address": {
                "city": None,
                "town": "Georgetown",
                "village": None
            }
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_location(5.4164, 100.3327)

        self.assertEqual(result, "Georgetown")

    @patch('search.requests.get')
    def test_get_location_fallback_to_village(self, mock_get):
        """Test fallback to village when city and town are unavailable."""
        mock_get.return_value.json.return_value = {
            "address": {
                "city": None,
                "town": None,
                "village": "Small Village"
            }
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_location(1.0, 101.0)

        self.assertEqual(result, "Small Village")

    @patch('search.requests.get')
    def test_get_location_no_location_found(self, mock_get):
        """Test when no location data is available."""
        mock_get.return_value.json.return_value = {
            "address": {
                "city": None,
                "town": None,
                "village": None
            }
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_location(0.0, 0.0)

        self.assertIsNone(result)

    @patch('search.requests.get')
    def test_get_location_empty_address(self, mock_get):
        """Test when address field is missing."""
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_location(1.0, 101.0)

        self.assertIsNone(result)

    @patch('search.requests.get')
    def test_get_location_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        with self.assertRaises(NominatimAPIError):
            _get_location(1.0, 101.0)

    @patch('search.requests.get')
    def test_get_location_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = mock_get.return_value
        http_error = requests.exceptions.HTTPError("404")
        http_error.response = mock_response
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = http_error

        with self.assertRaises(NominatimAPIError):
            _get_location(1.0, 101.0)

    @patch('search.requests.get')
    def test_get_location_sends_correct_params(self, mock_get):
        """Test that correct parameters are sent to Nominatim API."""
        mock_get.return_value.json.return_value = {"address": {"city": "Test"}}
        mock_get.return_value.raise_for_status.return_value = None

        _get_location(3.5, 101.5)

        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['lat'], 3.5)
        self.assertEqual(kwargs['params']['lon'], 101.5)
        self.assertEqual(kwargs['params']['format'], 'json')
        self.assertIn('User-Agent', kwargs['headers'])


class TestGetVideo(unittest.TestCase):
    """Test cases for _get_video function."""

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_success(self, mock_get):
        """Test successfully retrieving a video."""
        mock_get.return_value.json.return_value = {
            "items": [
                {
                    "id": {"videoId": "dQw4w9WgXcQ"},
                    "snippet": {
                        "title": "Amazing Walking Tour",
                        "thumbnails": {
                            "default": {"url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg"}
                        }
                    }
                }
            ]
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_video("Kuala Lumpur")

        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "Amazing Walking Tour")
        self.assertEqual(result['url'], "https://youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertIsNotNone(result['thumbnail'])

    @patch('search.api_key', None)
    def test_get_video_no_api_key(self):
        """Test behavior when API key is missing."""
        result = _get_video("Kuala Lumpur")

        self.assertIsNone(result)

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_no_results(self, mock_get):
        """Test when no videos are found."""
        mock_get.return_value.json.return_value = {"items": []}
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_video("XyzNonExistent")

        self.assertIsNone(result)

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_missing_items(self, mock_get):
        """Test when 'items' key is missing from response."""
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.raise_for_status.return_value = None

        result = _get_video("Singapore")

        self.assertIsNone(result)

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        with self.assertRaises(NetworkError):
            _get_video("Bangkok")

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_http_error(self, mock_get):
        """Test that HTTP errors are raised as YouTubeAPIError."""
        mock_response = mock_get.return_value
        http_error = requests.exceptions.HTTPError("403")
        http_error.response = mock_response
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = http_error
        mock_response.json.return_value = {
            "error": {
                "code": 403,
                "message": "Forbidden",
                "errors": [{"reason": "forbidden"}]
            }
        }

        with self.assertRaises(YouTubeAPIError):
            _get_video("Tokyo")

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_custom_parameters(self, mock_get):
        """Test custom vid_type and order parameters."""
        mock_get.return_value.json.return_value = {
            "items": [
                {
                    "id": {"videoId": "id"},
                    "snippet": {
                        "title": "Title",
                        "thumbnails": {"default": {"url": "https://example.com/image.jpg"}}
                    }
                }
            ]
        }
        mock_get.return_value.raise_for_status.return_value = None

        _get_video("Paris", vid_type="documentary", order="relevance")

        args, kwargs = mock_get.call_args
        self.assertIn("documentary", kwargs['params']['q'])
        self.assertEqual(kwargs['params']['order'], 'relevance')

    @patch('search.api_key', 'test-key')
    @patch('search.requests.get')
    def test_get_video_sends_correct_params(self, mock_get):
        """Test that correct parameters are sent to YouTube API."""
        mock_get.return_value.json.return_value = {
            "items": [
                {
                    "id": {"videoId": "id"},
                    "snippet": {
                        "title": "Title",
                        "thumbnails": {"default": {"url": "https://example.com/image.jpg"}}
                    }
                }
            ]
        }
        mock_get.return_value.raise_for_status.return_value = None

        _get_video("London", "walking tour", "date")

        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['part'], 'snippet')
        self.assertEqual(kwargs['params']['maxResults'], 1)
        self.assertEqual(kwargs['params']['type'], 'video')
        self.assertEqual(kwargs['params']['videoDuration'], 'medium')
        self.assertEqual(kwargs['params']['key'], 'test-key')


if __name__ == '__main__':
    unittest.main()
