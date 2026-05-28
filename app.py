from flask import Flask, jsonify, render_template
from flask_cors import CORS
from search import _get_location, _get_video

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

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
    
    video = _get_video(f"{location} ", "walking tour")

    if not video:
        return jsonify({"video_found": False}), 200
    
    return jsonify({
        "video_found": True,
        "location": location,
        "title": video["title"],
        "url": video["url"],
        "thumbnail": video["thumbnail"]
    })

if __name__ == "__main__":
    app.run(debug=True, port=8000)
