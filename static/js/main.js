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

function showVideoOverlay(title, thumbnail, videoUrl) {
    let overlay = document.getElementById('video-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'video-overlay';
        document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
        <a href="${videoUrl}" target="_blank">
            <img src="${thumbnail}" alt="${title}">
            <div class="video-title">${title}</div>
        </a>
    `;

    overlay.classList.remove('fade-out');
    overlay.classList.add('show');

    const timeoutId = setTimeout(() => {
        overlay.classList.remove('show');
        overlay.classList.add('fade-out');
        setTimeout(() => {
            overlay.classList.remove('fade-out');
        }, 500);
    }, 10000);

    overlay.addEventListener('click', () => {
        clearTimeout(timeoutId);
        overlay.classList.remove('show');
        overlay.classList.add('fade-out');
        setTimeout(() => {
            overlay.classList.remove('fade-out');
        }, 500);
    }, { once: true });
}

async function getVideo(latitude, longitude) {
    try {
        const response = await fetch(`/api/video/${latitude}/${longitude}`);
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
