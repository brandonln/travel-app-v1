function Location(lat, lon, name) {
    this.lat = lat;
    this.lon = lon;
    this.name = name;
}

const map = L.map('map', {
    maxBounds: L.latLngBounds([[-90, -180], [90, 180]])
}).setView([-25.96716, 27.66245], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    minZoom: 5,
    maxZoom: 11
}).addTo(map);

function showNotification(message, duration=3000) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.add('show');
    setTimeout(() => {
        notification.classList.remove('show');
    }, duration);
}

function getVideoIdFromUrl(url) {
    const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
    return match ? match[1] : null;
}

function showVideoOverlay(title, thumbnail, videoUrl) {
    let overlay = document.getElementById('video-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'video-overlay';
        document.body.appendChild(overlay);
    }

    const videoId = getVideoIdFromUrl(videoUrl);
    const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}?autoplay=1` : videoUrl;

    overlay.innerHTML = `
        <div class="video-container">
            <iframe
                width="100%"
                height="200"
                src="${embedUrl}"
                title="${title}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
        </div>
    `;

    overlay.classList.remove('fade-out');
    overlay.classList.add('show');
}

function isMobile() {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

async function getVideo(latitude, longitude) {
    try {
        const response = await fetch(`/api/video/${latitude}/${longitude}`);
        const data = await response.json();

        if (response.ok && data.video_found) {
            if (isMobile()) {
                showVideoOverlay(data.title, data.thumbnail, data.url);
            } else {
                window.open(data.url, '_blank');
            }
        }
        else if (!data.location_found) {
            showNotification('Try a different location...');
        }
        else if (!data.video_found) {
            showNotification('No videos found for this location');
        }
    } catch (error) {
        console.error(error);
        showNotification('Error retrieving video');
    }
}

function handleMapInteraction(e) {
    getVideo(e.latlng.lat, e.latlng.lng);
}

map.on('click', handleMapInteraction);
map.on('tap', handleMapInteraction);

window.addEventListener('load', () => {
    setTimeout(() => {
        const notification = document.getElementById('notification');
        notification.classList.add('load');
        showNotification('Click anywhere for a video', 10000);
    }, 3000);
});
