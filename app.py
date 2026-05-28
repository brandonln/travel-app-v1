from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from search import _get_location, _get_video

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')
    
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

    order_by = request.args.get('orderBy', 'date')
    video_type = request.args.get('videoType', 'vlog')
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
    app.run(debug=True, port=8000)
