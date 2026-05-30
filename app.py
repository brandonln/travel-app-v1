import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from search import _get_location, _get_video, APIError, YouTubeAPIError, NetworkError

app = Flask(__name__, static_folder='static', static_url_path='/static')

load_dotenv()
logger = logging.getLogger(__name__)

def validate_coordinates(latitude, longitude):
    """Validate and convert latitude and longitude to floats."""
    try:
        lat = float(latitude)
        lon = float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None, None
        return lat, lon
    except ValueError:
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/video/<latitude>/<longitude>')
def get_video(latitude, longitude):
    lat, lon = validate_coordinates(latitude, longitude)
    if lat is None or lon is None:
        return jsonify({"error": "Invalid coordinates"}), 400

    try:
        location = _get_location(lat, lon)
    except APIError as e:
        logger.error(f"Location service error: {e.message}")
        return jsonify({"error": "Location service unavailable"}), e.status_code


    if not location:
        return jsonify({"location_found": False}), 200
    
    VALID_ORDER_BY = {'date', 'relevance'}
    VALID_VIDEO_TYPES = {'vlog', 'walking tour'}

    order_by = request.args.get('orderBy', 'date')
    video_type = request.args.get('videoType', 'vlog')

    if order_by not in VALID_ORDER_BY:
        return jsonify({"error": "Invalid orderBy parameter"}), 400

    if video_type not in VALID_VIDEO_TYPES:
        return jsonify({"error": "Invalid videoType parameter"}), 400

    try:
        video = _get_video(f"{location} ", video_type, order_by)
    except YouTubeAPIError as e:
        logger.error(f"YouTube API Error: {e.message}")
        return jsonify({"error": "YouTube API unavailable"}), e.status_code
    except NetworkError as e:
        logger.error(f"Network error: {e.message}")
        return jsonify({"error": "Network error"}), e.status_code

    if not video:
        return jsonify({"location_found": True, "video_found": False}), 200

    return jsonify({
        "location_found": True,
        "video_found": True,
        "location": location,
        "title": video["title"],
        "url": video["url"],
        "thumbnail": video["thumbnail"]
    })
