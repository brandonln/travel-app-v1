import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from search import NominatimAPIError


class TestFlaskApp(unittest.TestCase):
    """Test cases for Flask app routes."""

    def setUp(self):
        """Create a test client before each test."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_index_route(self):
        """Test GET / returns index.html."""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_api_success(self, mock_get_location, mock_get_video):
        """Test GET /api/video returns video when location and video found."""
        mock_get_location.return_value = "Bangkok"
        mock_get_video.return_value = {
            "title": "Amazing Walking Tour",
            "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg"
        }

        response = self.client.get('/api/video/13.7563/100.5018')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['video_found'])
        self.assertEqual(data['location'], "Bangkok")
        self.assertEqual(data['title'], "Amazing Walking Tour")
        self.assertEqual(data['url'], "https://youtube.com/watch?v=dQw4w9WgXcQ")
        mock_get_location.assert_called_once_with(13.7563, 100.5018)
        mock_get_video.assert_called_once()

    @patch('app._get_location')
    def test_video_api_location_not_found(self, mock_get_location):
        """Test GET /api/video returns 200 when location cannot be found."""
        mock_get_location.return_value = None

        response = self.client.get('/api/video/0.0/0.0')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['location_found'])

    @patch('app._get_location')
    def test_video_api_nominatim_error(self, mock_get_location):
        """Test GET /api/video returns error when Nominatim API fails."""
        mock_get_location.side_effect = NominatimAPIError(503, "Service unavailable")

        response = self.client.get('/api/video/0.0/0.0')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['nominatim_error'])
        self.assertEqual(data['status_code'], 503)
        self.assertEqual(data['message'], "Service unavailable")

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_api_video_not_found(self, mock_get_location, mock_get_video):
        """Test GET /api/video returns 200 when video cannot be found."""
        mock_get_location.return_value = "Singapore"
        mock_get_video.return_value = None

        response = self.client.get('/api/video/1.3521/103.8198')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['video_found'])

    def test_video_api_invalid_coordinates(self):
        """Test GET /api/video with invalid coordinates returns 400."""
        response = self.client.get('/api/video/invalid/103.8198')

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['error'], "Invalid coordinates")

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_api_calls_with_custom_video_type(self, mock_get_location, mock_get_video):
        """Test GET /api/video passes videoType query parameter to _get_video."""
        mock_get_location.return_value = "Tokyo"
        mock_get_video.return_value = {
            "title": "Tour",
            "url": "http://example.com",
            "thumbnail": "https://example.com/image.jpg"
        }

        self.client.get('/api/video/35.6762/139.6503?videoType=walking+tour')

        # Verify _get_video was called with 'walking tour' as vid_type
        args, kwargs = mock_get_video.call_args
        self.assertEqual(args[0], "Tokyo ")
        self.assertEqual(args[1], "walking tour")

    def test_cors_enabled(self):
        """Test that CORS headers are present in response."""
        response = self.client.options('/api/location/1.0/101.0')

        # Flask-CORS should be enabled
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_index_returns_html(self):
        """Test that index route returns HTML content."""
        response = self.client.get('/')

        self.assertIn(b'<!doctype', response.data.lower())

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_api_unexpected_exception(self, mock_get_location, mock_get_video):
        """Test handling of unexpected exceptions in video route."""
        mock_get_location.return_value = "Bangkok"
        mock_get_video.side_effect = RuntimeError("Unexpected error")

        # Disable error handling to see the raw exception
        self.app.config['PROPAGATE_EXCEPTIONS'] = True
        with self.assertRaises(RuntimeError):
            self.client.get('/api/video/1.0/101.0')
        self.app.config['PROPAGATE_EXCEPTIONS'] = False

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_response_structure(self, mock_get_location, mock_get_video):
        """Test video response has correct structure."""
        mock_get_location.return_value = "Bangkok"
        mock_get_video.return_value = {
            "title": "Walking Tour",
            "url": "https://youtube.com/watch?v=id",
            "thumbnail": "https://i.ytimg.com/vi/id/default.jpg"
        }

        response = self.client.get('/api/video/13.7563/100.5018')
        data = response.get_json()

        # Verify required fields
        self.assertIn('video_found', data)
        self.assertIn('location', data)
        self.assertIn('title', data)
        self.assertIn('url', data)
        self.assertIn('thumbnail', data)
        # Verify no unexpected fields
        self.assertEqual(
            set(data.keys()),
            {'location_found', 'video_found', 'location', 'title', 'url', 'thumbnail'}
        )

    @patch('app._get_location')
    def test_video_api_location_not_found_response_structure(self, mock_get_location):
        """Test video not found (location) response structure."""
        mock_get_location.return_value = None

        response = self.client.get('/api/video/0.0/0.0')
        data = response.get_json()

        self.assertIn('location_found', data)
        self.assertFalse(data['location_found'])

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_api_video_not_found_response_structure(self, mock_get_location, mock_get_video):
        """Test video not found response structure."""
        mock_get_location.return_value = "Singapore"
        mock_get_video.return_value = None

        response = self.client.get('/api/video/1.3521/103.8198')
        data = response.get_json()

        self.assertIn('video_found', data)
        self.assertFalse(data['video_found'])

    def test_video_error_response_is_json(self):
        """Test that video error responses are JSON."""
        response = self.client.get('/api/video/invalid/101.0')

        self.assertEqual(response.content_type, 'application/json')
        data = response.get_json()
        self.assertIn('error', data)

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_response_url_format(self, mock_get_location, mock_get_video):
        """Test that video URL is properly formatted."""
        mock_get_location.return_value = "Tokyo"
        mock_get_video.return_value = {
            "title": "Tour",
            "url": "https://youtube.com/watch?v=abc123",
            "thumbnail": "https://i.ytimg.com/vi/abc123/default.jpg"
        }

        response = self.client.get('/api/video/35.6762/139.6503')
        data = response.get_json()

        self.assertTrue(data['url'].startswith('https://youtube.com/watch?v='))


if __name__ == '__main__':
    unittest.main()
