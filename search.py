import os
import logging
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("YOUTUBE_API_KEY")
if not api_key:
    raise RuntimeError("YOUTUBE_API_KEY environment variable is required")

logger = logging.getLogger(__name__)

def _get_location(latitude, longitude):
    """Get the city/town/village from coordinates using Nominatim."""
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            timeout=5,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json"
            },
            headers={"User-Agent": "travel-app/1.0"},
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
    
    except requests.exceptions as e:
        return {"reason": e.error}

def _get_video(location, vid_type="vlog", order="date"):
    """Search for the latest video matching the search term."""

    pause_requests = False

    if pause_requests:
        title="Getting started with Claude.ai"
        url="https://www.youtube.com/watch?v=0vZ_UVLhSQQ"
        thumbnail_url="https://youtube.com<0vZ_UVLhSQQ>/sddefault.jpg"
    
        return {"title": title, "url": url, "thumbnail": thumbnail_url}

    try:
        response = requests.get("https://www.googleapis.com/youtube/v3/search",
         timeout=10,
         params={
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
        # 1. Grab the response object trapped inside the exception
        error_response = e.response
    
        # 2. Check if the error response actually contains JSON data
        try:
            error_json = error_response.json()
            error_payload = error_json.get("error", {})
        
            # 3. Defensively navigate the JSON to find the reason
            errors_list = error_payload.get("errors", [])
            first_error = next(iter(errors_list), {})
            reason = first_error.get("reason")

            return json.dumps({"reason": reason})
            
        except ValueError:
            # The error response wasn't JSON (e.g., a raw HTML 502 Bad Gateway page)
            return json.dumps({"reason": "Server error threw raw text/HTML"})

    except requests.exceptions.RequestException as e:
        return {"reason": "Network level failure"}