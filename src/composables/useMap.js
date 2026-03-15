// src/composables/useMap.js
import L from 'leaflet'

// Color scheme per location type — deeper tones for contrast against OSM basemap
const TYPE_COLORS = {
  shelter: '#1d4ed8',      // blue-700 (deeper than OSM water)
  vet_transit: '#15803d',  // green-700
  yiqi: '#6d28d9',         // violet-700
  bulletin: '#c2410c',     // orange-700
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
    const color = TYPE_COLORS[location.type] || '#4b5563'
    const { cat, dog } = location.counts
    const total = cat + dog

    // Determine emoji
    let emoji = '🐾'
    if (cat > 0 && dog === 0) emoji = '🐱'
    else if (dog > 0 && cat === 0) emoji = '🐶'

    const html = `
      <div style="
        position: relative;
        width: 44px;
        height: 44px;
      ">
        <div style="
          width: 44px;
          height: 44px;
          border-radius: 50%;
          background: ${color};
          border: 4px solid white;
          box-shadow: 0 3px 8px rgba(0,0,0,0.45), 0 1px 3px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          line-height: 1;
          transition: transform 0.15s ease;
        ">${emoji}</div>
        <div style="
          position: absolute;
          top: -6px;
          right: -6px;
          background: #dc2626;
          color: white;
          border-radius: 999px;
          min-width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 700;
          padding: 0 4px;
          border: 2px solid white;
          box-shadow: 0 1px 3px rgba(0,0,0,0.3);
          line-height: 1;
        ">${total}</div>
      </div>
    `

    return L.divIcon({
      html,
      className: '',
      iconSize: [44, 44],
      iconAnchor: [22, 22],
      popupAnchor: [0, -26],
    })
  }

  function updateMarkers(locations, onMarkerClick, onMarkerHover) {
    if (!markerLayer) return
    markerLayer.clearLayers()
    locations.forEach(loc => {
      const marker = L.marker([loc.lat, loc.lng], {
        icon: createCustomIcon(loc),
      })
      marker.on('click', () => onMarkerClick(loc))

      if (onMarkerHover) {
        marker.on('mouseover', () => {
          const point = map.latLngToContainerPoint([loc.lat, loc.lng])
          onMarkerHover(loc, { x: point.x, y: point.y })
        })
        marker.on('mouseout', () => {
          onMarkerHover(null, null)
        })
      }

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
