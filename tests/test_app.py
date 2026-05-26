import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app


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

    @patch('app._get_location')
    def test_location_api_success(self, mock_get_location):
        """Test GET /api/location with valid coordinates returns location."""
        mock_get_location.return_value = "Petaling Jaya"

        response = self.client.get('/api/location/3.3163/101.5901')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['location_found'])
        self.assertEqual(data['location'], "Petaling Jaya")
        mock_get_location.assert_called_once_with(3.3163, 101.5901)

    @patch('app._get_location')
    def test_location_api_not_found(self, mock_get_location):
        """Test GET /api/location when location cannot be found."""
        mock_get_location.return_value = None

        response = self.client.get('/api/location/0.0/0.0')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['found'])

    def test_location_api_invalid_latitude(self):
        """Test GET /api/location with invalid latitude returns 400."""
        response = self.client.get('/api/location/invalid/101.5901')

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Invalid coordinates")

    def test_location_api_invalid_longitude(self):
        """Test GET /api/location with invalid longitude returns 400."""
        response = self.client.get('/api/location/3.3163/invalid')

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['error'], "Invalid coordinates")

    @patch('app._get_video')
    @patch('app._get_location')
    def test_video_api_success(self, mock_get_location, mock_get_video):
        """Test GET /api/video returns video when location and video found."""
        mock_get_location.return_value = "Bangkok"
        mock_get_video.return_value = {
            "title": "Amazing Walking Tour",
            "url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
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
    def test_video_api_calls_with_walking_tour(self, mock_get_location, mock_get_video):
        """Test GET /api/video calls _get_video with 'walking tour' type."""
        mock_get_location.return_value = "Tokyo"
        mock_get_video.return_value = {"title": "Tour", "url": "http://example.com"}

        self.client.get('/api/video/35.6762/139.6503')

        # Verify _get_video was called with 'walking tour' as vid_type
        args, kwargs = mock_get_video.call_args
        self.assertEqual(args[0], "Tokyo ")
        self.assertEqual(args[1], "walking tour")

    def test_json_response_headers(self):
        """Test API endpoints return JSON content type."""
        response = self.client.get('/api/location/1.0/101.0')

        self.assertEqual(response.content_type, 'application/json')

    def test_cors_enabled(self):
        """Test that CORS headers are present in response."""
        response = self.client.options('/api/location/1.0/101.0')

        # Flask-CORS should be enabled
        self.assertIn('Access-Control-Allow-Origin', response.headers)


if __name__ == '__main__':
    unittest.main()
