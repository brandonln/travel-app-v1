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

let videoOrderBy = 'date';
let videoType = 'vlog';

const OptionsControl = L.Control.extend({
    options: {
        groups: []
    },
    onAdd: function(map) {
        const container = L.DomUtil.create('div', 'leaflet-control leaflet-bar');

        this.options.groups.forEach(group => {
            const label = L.DomUtil.create('div', 'leaflet-bar-part', container);
            label.textContent = group.label;

            group.options.forEach((opt, i) => {
                const optLabel = L.DomUtil.create('label', 'leaflet-bar-part', container);
                const input = L.DomUtil.create('input', '', optLabel);
                input.type = 'radio';
                input.name = group.name;
                input.value = opt.value;
                if (i === 0) input.checked = true;
                input.addEventListener('change', (e) => {
                    group.onChange(e.target.value);
                });
                optLabel.appendChild(document.createTextNode(opt.label));
            });
        });

        return container;
    }
});

new OptionsControl({
    position: 'bottomright',
    groups: [
        {
            label: 'Search by:',
            name: 'videoOrder',
            options: [
                { value: 'date', label: ' Date' },
                { value: 'relevance', label: ' Relevance' }
            ],
            onChange: (value) => { videoOrderBy = value; }
        },
        {
            label: 'Video Type:',
            name: 'videoType',
            options: [
                { value: 'vlog', label: ' Vlog' },
                { value: 'walking tour', label: ' Walking Tour' }
            ],
            onChange: (value) => { videoType = value; }
        }
    ]
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

function closeVideoOverlay() {
    const overlay = document.getElementById('video-overlay');
    if (overlay && overlay.classList.contains('show')) {
        overlay.classList.remove('show');
        overlay.classList.add('fade-out');
        setTimeout(() => {
            overlay.classList.remove('fade-out');
            overlay.innerHTML = '';
        }, 500);
    }
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

async function getVideo(latitude, longitude) {
    try {
        const response = await fetch(`/api/video/${latitude}/${longitude}?orderBy=${videoOrderBy}&videoType=${videoType}`);
        const data = await response.json();

        if (response.ok && data.video_found) {
            showVideoOverlay(data.title, data.thumbnail, data.url);
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
    const overlay = document.getElementById('video-overlay');

    // If overlay is visible, close it instead of fetching a new video
    if (overlay && overlay.classList.contains('show')) {
        closeVideoOverlay();
    } else {
        // Only fetch video if no overlay is currently displayed
        getVideo(e.latlng.lat, e.latlng.lng);
    }
}

map.on('click', handleMapInteraction);
map.on('tap', handleMapInteraction);

// Close overlay when user interacts with map
map.on('dragstart', closeVideoOverlay);
map.on('zoomstart', closeVideoOverlay);

window.addEventListener('load', () => {
    setTimeout(() => {
        const notification = document.getElementById('notification');
        notification.classList.add('load');
        showNotification('Click anywhere for a video', 10000);
    }, 3000);
});
