// src/composables/useMap.js
import L from 'leaflet'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

// Color scheme per location type
const TYPE_COLORS = {
  shelter: '#1d4ed8',      // blue-700
  vet_transit: '#15803d',  // green-700
  yiqi: '#6d28d9',         // violet-700
  bulletin: '#c2410c',     // orange-700
}

export function useMap() {
  let map = null
  let clusterGroup = null
  let userLocationMarker = null

  function initMap(containerId) {
    map = L.map(containerId).setView([24.15, 120.67], 12)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map)

    clusterGroup = L.markerClusterGroup({
      // Custom cluster icon styling
      iconCreateFunction(cluster) {
        const count = cluster.getChildCount()
        const size = count < 10 ? 36 : count < 50 ? 44 : 52
        return L.divIcon({
          html: `<div style="
            width:${size}px;height:${size}px;
            border-radius:50%;
            background:rgba(29,78,216,0.85);
            border:3px solid white;
            box-shadow:0 3px 10px rgba(0,0,0,0.35);
            display:flex;align-items:center;justify-content:center;
            font-size:${count < 10 ? 13 : 12}px;font-weight:700;
            color:white;
            backdrop-filter:blur(4px);
          ">${count}</div>`,
          className: '',
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        })
      },
      maxClusterRadius: 60,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      disableClusteringAtZoom: 15,
    })

    map.addLayer(clusterGroup)
  }

  function createCustomIcon(location) {
    const color = TYPE_COLORS[location.type] || '#4b5563'
    const { cat = 0, dog = 0 } = location.counts ?? {}
    const total = cat + dog

    let emoji = '🐾'
    if (cat > 0 && dog === 0) emoji = '🐱'
    else if (dog > 0 && cat === 0) emoji = '🐶'

    const html = `
      <div style="position:relative;width:44px;height:44px;">
        <div style="
          width:44px;height:44px;border-radius:50%;
          background:${color};
          border:4px solid white;
          box-shadow:0 3px 8px rgba(0,0,0,0.45),0 1px 3px rgba(0,0,0,0.3);
          display:flex;align-items:center;justify-content:center;
          font-size:20px;line-height:1;
        ">${emoji}</div>
        <div style="
          position:absolute;top:-6px;right:-6px;
          background:#dc2626;color:white;
          border-radius:999px;min-width:20px;height:20px;
          display:flex;align-items:center;justify-content:center;
          font-size:11px;font-weight:700;padding:0 4px;
          border:2px solid white;
          box-shadow:0 1px 3px rgba(0,0,0,0.3);
          line-height:1;
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
    if (!clusterGroup) return
    clusterGroup.clearLayers()
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

      clusterGroup.addLayer(marker)
    })
  }

  function flyTo(lat, lng, zoom = 15) {
    map?.flyTo([lat, lng], zoom)
  }

  function invalidateSize() {
    map?.invalidateSize()
  }

  // Locate and fly to user's current position, place a marker
  function locateUser(onSuccess, onError) {
    if (!navigator.geolocation) {
      onError?.('您的瀏覽器不支援定位功能')
      return
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        const { latitude: lat, longitude: lng } = pos.coords

        // Remove existing user marker
        if (userLocationMarker) {
          map.removeLayer(userLocationMarker)
        }

        userLocationMarker = L.marker([lat, lng], {
          icon: L.divIcon({
            html: `<div style="
              width:18px;height:18px;border-radius:50%;
              background:#2563eb;
              border:3px solid white;
              box-shadow:0 0 0 6px rgba(37,99,235,0.25),0 2px 8px rgba(0,0,0,0.3);
            "></div>`,
            className: '',
            iconSize: [18, 18],
            iconAnchor: [9, 9],
          }),
          zIndexOffset: 2000,
        }).addTo(map)

        map.flyTo([lat, lng], 14, { duration: 1.4 })
        onSuccess?.({ lat, lng })
      },
      err => {
        const messages = {
          1: '請允許瀏覽器存取您的位置',
          2: '無法取得位置資訊',
          3: '定位請求逾時',
        }
        onError?.(messages[err.code] || '定位失敗')
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  return { initMap, updateMarkers, flyTo, invalidateSize, locateUser }
}
