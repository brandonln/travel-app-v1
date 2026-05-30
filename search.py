import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("YOUTUBE_API_KEY")

def _get_location(latitude, longitude):
    """Get the city/town/village from coordinates using Nominatim."""

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json"
            },
            headers={"User-Agent": "travel-app/1.0"}
        )

        response.raise_for_status()
        data = response.json()

        address = data.get("address", {})

        location = (
                address.get("city") or
                address.get("town") or
                address.get("village")
        )

        return location if location else None

    except requests.exceptions.HTTPError as e:
        raise NominatimAPIError(e.response.status_code, str(e))
    except requests.exceptions.RequestException as e:
        raise NominatimAPIError(0, f"Network error: {str(e)}")


def _get_video(location, vid_type="vlog", order="date"):
    """Search for the latest video matching the search term."""

    if not api_key:
        return None

    try:
        response = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet",
            "q": f"{location} + {vid_type}",
            "order": order,
            "maxResults": 1,
            "key": api_key,
            "type": "video",
            "videoDuration": "medium"
        })

        response.raise_for_status()
        data = response.json()

        if "items" not in data or len(data["items"]) == 0:
            return None

        video = data["items"][0]
        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        url = f"https://youtube.com/watch?v={video_id}"
        thumbnails = video["snippet"]["thumbnails"]
        thumbnail_url = thumbnails.get("high", {}).get("url") or thumbnails.get("default", {}).get("url")

        return {"title": title, "url": url, "thumbnail": thumbnail_url}

    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json().get("error", {})
            error_reason = error_data.get("errors", [{}])[0].get("reason", "")
            error_message = error_data.get("message", "Unknown error")
            status_code = e.response.status_code

            if error_reason == "quotaExceeded":
                raise QuotaExceededError(status_code, error_reason, error_message)
            else:
                raise YouTubeAPIError(status_code, error_reason, error_message)
        except (ValueError, KeyError, IndexError):
            raise YouTubeAPIError(e.response.status_code, "unknown", str(e))
    except requests.exceptions.RequestException as e:
        raise NetworkError("Failed to fetch video")


class NominatimAPIError(Exception):
    """Raised when Nominatim API returns an error."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{status_code}: {message}")


class YouTubeAPIError(Exception):
    """Raised when YouTube API returns an error."""
    def __init__(self, status_code, reason, message):
        self.status_code = status_code
        self.reason = reason
        self.message = message
        super().__init__(f"{status_code} {reason}: {message}")


class QuotaExceededError(YouTubeAPIError):
    """Raised when YouTube API quota is exceeded."""
    pass


class NetworkError(Exception):
    """Raised when a network error occurs."""
    pass