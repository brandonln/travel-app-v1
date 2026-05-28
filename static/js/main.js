function Location(lat, lon, name) {
    this.lat = lat;
    this.lon = lon;
    this.name = name;
}

let videoOrderBy = 'date';
let videoType = 'vlog';

const map = L.map('map', {
    maxBounds: L.latLngBounds([[-90, -180], [90, 180]])
}).setView([-25.96716, 27.66245], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    minZoom: 5,
    maxZoom: 11
}).addTo(map);

const OptionsControl = L.Control.extend({
    options: {
        label: '',
        name: '',
        options: [],
        onChange: null
    },
    onAdd: function(map) {
        const container = L.DomUtil.create('div', 'leaflet-control');
        const label = L.DomUtil.create('div', '', container);
        label.textContent = this.options.label;

        const onChange = this.options.onChange;
        this.options.options.forEach((opt, i) => {
            const optLabel = L.DomUtil.create('label', '', container);
            const input = L.DomUtil.create('input', '', optLabel);
            input.type = 'radio';
            input.name = this.options.name;
            input.value = opt.value;
            if (i === 0) input.checked = true;
            input.addEventListener('change', (e) => {
                onChange(e.target.value);
            });
            optLabel.appendChild(document.createTextNode(opt.label));
        });

        return container;
    }
});

new OptionsControl({
    position: 'bottomright',
    label: 'Order by:',
    name: 'videoOrder',
    options: [
        { value: 'date', label: 'Date' },
        { value: 'relevance', label: 'Relevance' }
    ],
    onChange: (value) => { videoOrderBy = value; }
}).addTo(map);

new OptionsControl({
    position: 'bottomright',
    label: 'Video Type:',
    name: 'videoType',
    options: [
        { value: 'vlog', label: 'Vlog' },
        { value: 'walking tour', label: 'Walking Tour' }
    ],
    onChange: (value) => { videoType = value; }
}).addTo(map);

map.on('dragstart', function() {
    document.getElementById('map').style.cursor = 'grabbing';
});

map.on('dragend', function() {
    document.getElementById('map').style.cursor = 'default';
});

function showNotification(message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.add('show');
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

async function getVideo(latitude, longitude, orderBy = videoOrderBy, type = videoType) {
    try {
        const response = await fetch(`/api/video/${latitude}/${longitude}?orderBy=${orderBy}&videoType=${type}`);
        const data = await response.json();
        if (response.ok && data.video_found) {
            window.open(data.url, '_blank')
        }
        else if (!data.location_found) {
            showNotification('Try a different location...');
        }

    } catch (error) {
        console.error(error);
    }
}

function handleMapInteraction(e) {
    getVideo(e.latlng.lat, e.latlng.lng);
}

map.on('click', handleMapInteraction);
map.on('tap', handleMapInteraction);
