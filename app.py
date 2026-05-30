import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from search import _get_location, _get_video, NominatimAPIError, YouTubeAPIError, NetworkError

domain = os.getenv("DOMAIN")

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app, resource={r"/api/*": {"origins": [domain]}})

def validate_coordinates(latitude, longitude):
    """Validate and convert latitude and longitude to floats."""
    try:
        return float(latitude), float(longitude)
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
    except NominatimAPIError as e:
        return jsonify({
            "nominatim_error": True,
            "status_code": e.status_code,
            "message": e.message
        }), 200

    if not location:
        return jsonify({"location_found": False}), 200
    
    VALID_ORDER_BY = {'date', 'relevance'}
    VALID_VIDEO_TYPES = {'vlog', 'walking tour'}

    order_by = request.args.get('orderBy', 'date')
    video_type = request.args.get('videoType', 'vlog')

    if order_by not in VALID_ORDER_BY:
        return jsonify({"error": "Invalid orderBy parameter"}), 400

    if video_type not in VALID_VIDEO_TYPES:
        return jsonify({"error: Invalid orderBy parameter"}), 400

    try:
        video = _get_video(f"{location} ", video_type, order_by)
    except YouTubefror as e:
        return jsonify({
            "youtube_error": True,
            "status_code": e.status_code,
            "reason": e.reason,
            "message": e.message
        }), 200
    except NetworkError:
        return jsonify({"network_error": True}), 200

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
