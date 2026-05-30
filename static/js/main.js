const map = L.map('map', {
    maxBounds: L.latLngBounds([[-90, -180], [90, 180]])
}).setView([-25.96716, 27.66245], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    minZoom: 5,
    maxZoom: 11
}).addTo(map);

let orderBy = 'date';
let videoType = 'vlog';
let loadTimeoutId = null;

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
            name: 'orderBy',
            options: [
                { value: 'date', label: ' Date' },
                { value: 'relevance', label: ' Relevance' }
            ],
            onChange: (value) => { orderBy = value; }
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

function isMobileDevice() {
    return window.innerWidth <= 768;
}

function showVideoOverlay(title, thumbnail, videoUrl) {
    let overlay = document.getElementById('video-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'video-overlay';
        document.body.appendChild(overlay);
        // Prevent clicks on overlay from bubbling to map
        overlay.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    const videoId = getVideoIdFromUrl(videoUrl);
    const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}?autoplay=1&fs=0` : videoUrl;

    const video_container = document.createElement('div');
    video_container.classList.add('video-container');

    const iframe = document.createElement('iframe');
    
    iframe.setAttribute('width',"100%");
    iframe.setAttribute('src', embedUrl);
    iframe.setAttribute('title', title);
    iframe.setAttribute('frameborder',"0");
    iframe.setAttribute('allow','autoplay; picture-in-picture');

    iframe.classList.add('video');

    video_container.appendChild(iframe);
    overlay.appendChild(video_container);

    overlay.classList.remove('fade-out');
    overlay.classList.add('show');
}

function fadeOutOverlay(overlay, callback) {
    overlay.classList.add('fade-out');
    setTimeout(() => {
        overlay.classList.remove('fade-out');
        if (callback) callback();
    }, 500);
}

function closeVideoOverlay() {
    const overlay = document.getElementById('video-overlay');
    if (overlay && overlay.classList.contains('show')) {
        overlay.classList.remove('show');
        fadeOutOverlay(overlay, () => {
            overlay.innerHTML = '';
        });
    }
}

async function getVideo(latitude, longitude) {
    try {
        const params = new URLSearchParams({
            orderBy: orderBy,
            videoType: videoType
        });
        const response = await fetch(`/api/video/${latitude}/${longitude}?${params}`);

        const data = await response.json();

        if (data.nominatim_error) {
            console.error(`Location service error (${data.status_code}):`, data.message);
            showNotification('Sorry, we need to fix this!');
        }
        else if (data.youtube_error) {
            console.error(`YouTube API Error (${data.status_code}):`, data.reason);
            if (data.reason === "quotaExceeded") {
                showNotification('Daily limit exceeded. Try again tomorrow.');
            } else {
                showNotification('Sorry, we need to fix this!');
            }
        }
        else if (data.network_error) {
            showNotification('Connection error.');
        }
        else if (response.ok && data.video_found) {
            if (isMobileDevice()) {
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
    clearTimeout(loadTimeoutId);
    const overlay = document.getElementById('video-overlay');
    const notification = document.getElementById('notification');

    notification.classList.remove('show', 'load');

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
map.on('dragstart', () => {
    closeVideoOverlay();
    map.getContainer().style.cursor = 'grabbing';
});
map.on('dragend', () => {
    map.getContainer().style.cursor = 'auto';
});
map.on('zoomstart', closeVideoOverlay);

window.addEventListener('load', () => {
    loadTimeoutId = setTimeout(() => {
        const notification = document.getElementById('notification');
        notification.classList.add('load');
        showNotification('Click anywhere for a video', 10000);
    }, 3000);
});
