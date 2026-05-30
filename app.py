import logging
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from search import _get_location, _get_video, APIError, YouTubeAPIError, NetworkError

app = Flask(__name__, static_folder='static', static_url_path='/static')




# Configure trusted hosts for host header validation
trusted_hosts = ['localhost', '127.0.0.1']
if os.getenv('VERCEL_ENV') == 'production':
    custom_domain = os.getenv('VERCEL_PROJECT_PRODUCTION_URL')
    if custom_domain:
        trusted_hosts.extend([custom_domain, f'www.{custom_domain}'])
elif os.getenv('VERCEL_ENV') == 'preview':
    trusted_hosts.extend(['*.vercel.app', os.getenv('VERCEL_URL', '')])
else:
    trusted_hosts.extend(['localhost:*', '127.0.0.1:*'])

app.config['TRUSTED_HOSTS'] = trusted_hosts



# Use ProxyFix for Vercel's reverse proxy infrastructure
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

is_production = os.getenv('VERCEL_ENV') == 'production' or os.getenv('FLASK_ENV') == 'production'

Talisman(
    app,
    force_https=is_production,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "cdnjs.cloudflare.com", "vercel.live"],
        'style-src': ["'self'", "cdnjs.cloudflare.com"],
        'img-src': ["'self'", "*.tile.openstreetmap.org", "youtube.com", "*.ytimg.com"],
        'frame-src': ["'self'", "youtube.com", "www.youtube.com", "vercel.live"],
        'connect-src': ["'self'", "nominatim.openstreetmap.org", "www.googleapis.com"]
    }
)


app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max request size
app.config['MAX_FORM_MEMORY_SIZE'] = 1 * 1024 * 1024  # 1MB max form data

load_dotenv()
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/video/<latitude>/<longitude>')
@limiter.limit("100 per hour; 500 per day")
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
