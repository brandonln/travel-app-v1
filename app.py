import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from search import _get_location, _get_video

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

is_production = os.getenv('VERCEL_ENV') == 'production' or os.getenv('FLASK_DEBUG')

Talisman(
    app,
    force_https=is_production,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "cdnjs.cloudflare.com", "vercel.live"],
        'style-src': ["'self'", "cdnjs.cloudflare.com"],
        'img-src': ["'self'", "data:", "*.tile.openstreetmap.org", "youtube.com", "*.ytimg.com", "cdnjs.cloudflare.com"],
        'frame-src': ["'self'", "youtube.com", "www.youtube.com", "vercel.live"],
        'connect-src': ["'self'", "nominatim.openstreetmap.org", "www.googleapis.com"]
    }
)


app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max request size
app.config['MAX_FORM_MEMORY_SIZE'] = 1 * 1024 * 1024  # 1MB max form data

load_dotenv()

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
def get_video(latitude, longitude):
    lat, lon = validate_coordinates(latitude, longitude)
    if lat is None or lon is None:
        return jsonify({"reason": "Invalid coordinates"}), 400

    result = _get_location(lat, lon)

    if not result:
        return jsonify({"location_found": False}), 200

    if "reason" in result:
        error_reason = result["reason"]
        return jsonify({"reason": error_reason}), 400
    
    location = result
    
    VALID_ORDER_BY = {'date', 'relevance'}
    VALID_VIDEO_TYPES = {'vlog', 'walking tour'}

    order_by = request.args.get('orderBy', 'date')
    video_type = request.args.get('videoType', 'vlog')

    if order_by not in VALID_ORDER_BY:
        return jsonify({"reason": "Invalid orderBy parameter"}), 400

    if video_type not in VALID_VIDEO_TYPES:
        return jsonify({"reason": "Invalid videoType parameter"}), 400
    
    result = _get_video(f"{location} ", video_type, order_by)

    if "reason" in result:
        error_reason = result["reason"]
        return jsonify({"reason": error_reason}), 400
    else:
        video = result

    if not video:
        return jsonify({"location_found": True, "video_found": False}), 200

    return jsonify({
        "location_found": True,
        "video_found": True,
        "location": location,
        "title": result["title"],
        "url": video["url"],
        "thumbnail": video["thumbnail"]
    }), 200
