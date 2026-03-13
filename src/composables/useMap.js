// src/composables/useMap.js
import L from 'leaflet'

// Color scheme per location type
const TYPE_COLORS = {
  shelter: '#3b82f6',      // blue
  vet_transit: '#22c55e',  // green
  bulletin: '#f97316',     // orange
}

export function useMap() {
  let map = null
  let markerLayer = null

  function initMap(containerId) {
    map = L.map(containerId).setView([24.15, 120.67], 12)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map)
    markerLayer = L.layerGroup().addTo(map)
  }

  function createCustomIcon(location) {
    const color = TYPE_COLORS[location.type] || '#6b7280'
    const { cat, dog } = location.counts
    const total = cat + dog

    // Determine emoji
    let emoji = '🐾'
    if (cat > 0 && dog === 0) emoji = '🐱'
    else if (dog > 0 && cat === 0) emoji = '🐶'

    const html = `
      <div style="
        position: relative;
        width: 40px;
        height: 40px;
      ">
        <div style="
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: ${color};
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          line-height: 1;
        ">${emoji}</div>
        <div style="
          position: absolute;
          top: -6px;
          right: -6px;
          background: #ef4444;
          color: white;
          border-radius: 999px;
          min-width: 18px;
          height: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
          padding: 0 4px;
          border: 1.5px solid white;
          line-height: 1;
        ">${total}</div>
      </div>
    `

    return L.divIcon({
      html,
      className: '',
      iconSize: [40, 40],
      iconAnchor: [20, 20],
      popupAnchor: [0, -24],
    })
  }

  function updateMarkers(locations, onMarkerClick) {
    if (!markerLayer) return
    markerLayer.clearLayers()
    locations.forEach(loc => {
      const marker = L.marker([loc.lat, loc.lng], {
        icon: createCustomIcon(loc),
      })
      marker.on('click', () => onMarkerClick(loc))
      markerLayer.addLayer(marker)
    })
  }

  function flyTo(lat, lng, zoom = 15) {
    map?.flyTo([lat, lng], zoom)
  }

  function invalidateSize() {
    map?.invalidateSize()
  }

  return { initMap, updateMarkers, flyTo, invalidateSize }
}
