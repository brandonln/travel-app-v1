import os
import logging
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from search import _get_location, _get_video

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB max request size

allowed_origins = [
    'http://localhost:3000',
    'http://localhost:8000',
]

vercel_url = os.getenv('VERCEL_URL')
if vercel_url:
    allowed_origins.append(f'https://{vercel_url}')

CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"]
)

@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f'Rate limit exceeded from {request.remote_addr}')
    return jsonify({"error": "Rate limit exceeded"}), 429

@app.errorhandler(413)
def request_too_large(e):
    logger.warning(f'Request payload too large from {request.remote_addr}')
    return jsonify({"error": "Request payload too large"}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f'Internal server error: {e}')
    return jsonify({"error": "Internal server error"}), 500

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/api/video/<latitude>/<longitude>')
@limiter.limit("100 per hour; 500 per day")
def get_video(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({"error": "Invalid coordinates"}), 400

    location = _get_location(latitude, longitude)

    if not location:
        return jsonify({"location_found": False}), 200

    allowed_order = ['date', 'relevance', 'viewCount']
    allowed_types = ['vlog', 'walking tour']

    order_by = request.args.get('orderBy', 'date')
    video_type = request.args.get('videoType', 'vlog')

    if order_by not in allowed_order:
        order_by = 'date'
    if video_type not in allowed_types:
        video_type = 'vlog'

    video = _get_video(f"{location} ", video_type, order_by)

    if not video:
        return jsonify({"video_found": False}), 200
    
    return jsonify({
        "video_found": True,
        "location": location,
        "title": video["title"],
        "url": video["url"]
    })

if __name__ == "__main__":
    app.run(debug=False, port=8000)
