import os
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

load_dotenv()
api_key = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

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

    except requests.exceptions.RequestException as e:
        return None

def search_youtube_video(search_term):
    """Search for the latest video matching the search term."""

    if not api_key:
        return None


    try:
        response = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet",
            "q": search_term,
            "order": "date",
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

@app.route('/api/location/<latitude>/<longitude>')
def get_location(latitude, longitude):
    """API endpoint to get video for a location."""

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({"error": "Invalid coordinates"}), 400

    location = _get_location(latitude, longitude)

    if not location:
        return jsonify({"found": False}), 200
    
    return jsonify({
        "location_found": True,
        "location": location
    })
    
@app.route('/api/video/<latitude>/<longitude>')
def get_video(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({"error": "Invalid coordinates"}), 400

    location = _get_location(latitude, longitude)

    if not location:
        return jsonify({"location_found": False}), 200
    
    video = search_youtube_video(f"{location} vlog")

    if not video:
        return jsonify({"video_found": False}), 200
    
    return jsonify({
        "video_found": True,
        "location": location,
        "title": video["title"],
        "url": video["url"]
    })


if __name__ == "__main__":
    app.run(debug=True, port=8000)
