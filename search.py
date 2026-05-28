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
                address.get("village") or
                address.get("town")
        )

        return location if location else None

    except requests.exceptions.RequestException as e:
        return None



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

        return {"title": title, "url": url}

    except requests.exceptions.RequestException as e:
        return None