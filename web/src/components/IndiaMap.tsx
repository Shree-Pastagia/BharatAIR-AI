import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface Station {
  id: string
  name: string
  city: string
  state: string
  operator: string
  lat: number
  lon: number
  best_mae_1h: number | null
  best_model_1h: string
  best_mae_24h: number | null
  best_model_24h: string
}

interface City {
  name: string
  lat: number
  lon: number
  station_count: number
  median_mae_1h: number
  median_mae_24h: number
}

interface IndiaMapProps {
  cities: City[]
  stations: Station[]
  selectedCity: string
  selectedStationId: string
  onSelectCity: (cityName: string) => void
  onSelectStation: (stationId: string) => void
}

function getMarkerColor(city: string) {
  const c = city.toLowerCase()
  if (c === 'delhi') return '#ef4444' // Red / Severe
  if (c === 'mumbai') return '#06b6d4' // Cyan / Coastal
  if (c === 'bengaluru') return '#10b981' // Green / Good
  if (c === 'chennai') return '#06b6d4' // Cyan
  if (c === 'kolkata') return '#f97316' // Orange
  if (c === 'hyderabad') return '#eab308' // Yellow
  if (c === 'ahmedabad') return '#f59e0b' // Amber
  return '#22d3ee'
}

export default function IndiaMap({
  cities,
  stations,
  selectedCity,
  selectedStationId,
  onSelectCity,
  onSelectStation
}: IndiaMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const markersLayerRef = useRef<L.LayerGroup | null>(null)

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return

    const map = L.map(mapContainerRef.current, {
      center: [22.3511, 78.6677], // India geographic center
      zoom: 5,
      minZoom: 4,
      maxZoom: 14,
      zoomControl: true
    })

    // Esri World Dark Gray Canvas (Clean, keyless, zero watermarks)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri &copy; OpenStreetMap contributors',
      maxZoom: 16
    }).addTo(map)

    // Esri Dark Labels & Boundaries Overlay
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16
    }).addTo(map)

    const markersGroup = L.layerGroup().addTo(map)
    markersLayerRef.current = markersGroup
    mapInstanceRef.current = map

    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [])

  // Update Markers and View
  useEffect(() => {
    const map = mapInstanceRef.current
    const markersGroup = markersLayerRef.current
    if (!map || !markersGroup) return

    markersGroup.clearLayers()

    // 1. Plot all 107 stations
    stations.forEach(st => {
      const isSelected = st.id === selectedStationId
      const color = getMarkerColor(st.city)

      const marker = L.circleMarker([st.lat, st.lon], {
        radius: isSelected ? 8 : 4.5,
        fillColor: color,
        color: isSelected ? '#ffffff' : color,
        weight: isSelected ? 2.5 : 1,
        opacity: 0.9,
        fillOpacity: isSelected ? 1 : 0.75
      })

      marker.bindPopup(`
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 12px; color: #f8fafc; min-width: 190px;">
          <div style="font-weight: 700; color: #38bdf8; margin-bottom: 2px;">${st.name}</div>
          <div style="font-family: monospace; font-size: 11px; color: #94a3b8; margin-bottom: 6px;">${st.id} • ${st.operator}</div>
          <div style="border-top: 1px solid #334155; padding-top: 5px; font-size: 11px; color: #cbd5e1;">
            <div><strong>+1h Model:</strong> <span style="color: #22d3ee;">${st.best_model_1h.toUpperCase()}</span> (±${st.best_mae_1h} µg)</div>
            <div><strong>+24h Model:</strong> <span style="color: #34d399;">${st.best_model_24h.toUpperCase()}</span> (±${st.best_mae_24h} µg)</div>
          </div>
          <button id="btn-${st.id}" style="margin-top: 8px; width: 100%; background: #0284c7; color: white; border: none; border-radius: 6px; padding: 5px 8px; font-size: 11px; font-weight: 600; cursor: pointer;">
            Select Station
          </button>
        </div>
      `)

      marker.on('popupopen', () => {
        const btn = document.getElementById(`btn-${st.id}`)
        if (btn) {
          btn.onclick = () => {
            onSelectCity(st.city)
            onSelectStation(st.id)
          }
        }
      })

      marker.on('click', () => {
        onSelectCity(st.city)
        onSelectStation(st.id)
      })

      markersGroup.addLayer(marker)
    })

    // 2. City Pulse Rings
    cities.forEach(c => {
      const isCitySelected = c.name.toLowerCase() === selectedCity.toLowerCase()
      if (isCitySelected) {
        const cityRing = L.circleMarker([c.lat, c.lon], {
          radius: 20,
          fillColor: '#22d3ee',
          color: '#22d3ee',
          weight: 1.5,
          opacity: 0.4,
          fillOpacity: 0.1,
          dashArray: '3, 6'
        })
        markersGroup.addLayer(cityRing)
      }
    })
  }, [stations, cities, selectedCity, selectedStationId, onSelectCity, onSelectStation])

  // Fly to selected station or city
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    const st = stations.find(s => s.id === selectedStationId)
    if (st && st.lat && st.lon) {
      map.flyTo([st.lat, st.lon], 11, { duration: 1.2 })
    } else {
      const city = cities.find(c => c.name.toLowerCase() === selectedCity.toLowerCase())
      if (city) {
        map.flyTo([city.lat, city.lon], 9, { duration: 1.2 })
      }
    }
  }, [selectedCity, selectedStationId])

  return (
    <div className="relative w-full h-[420px] rounded-2xl overflow-hidden border border-slate-800/80 bg-slate-950 shadow-inner">
      {/* Map Container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Floating City Badges on Map */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-wrap gap-1.5 max-w-sm pointer-events-auto bg-slate-950/80 p-2 rounded-xl border border-slate-800/80 backdrop-blur-md">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block w-full mb-1">
          Fly To Regional Cluster:
        </span>
        {cities.map(c => {
          const isSelected = c.name.toLowerCase() === selectedCity.toLowerCase()
          return (
            <button
              key={c.name}
              onClick={() => {
                onSelectCity(c.name)
                const first = stations.find(s => s.city.toLowerCase() === c.name.toLowerCase())
                if (first) onSelectStation(first.id)
              }}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                isSelected
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                  : 'bg-slate-900/90 text-slate-300 hover:text-white border border-slate-800'
              }`}
            >
              {c.name}
            </button>
          )
        })}
      </div>

      {/* Floating Map Legend */}
      <div className="absolute bottom-3 right-3 z-[1000] bg-slate-950/90 p-2.5 rounded-xl border border-slate-800 backdrop-blur-md text-[11px] font-mono space-y-1">
        <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Station Telemetry Legend</div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          <span className="text-slate-300">Bengaluru (Good/Clean)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
          <span className="text-slate-300">Mumbai / Chennai (Marine)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
          <span className="text-slate-300">Hyderabad / Ahmedabad</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
          <span className="text-slate-300">Delhi (Winter Inversion)</span>
        </div>
      </div>
    </div>
  )
}
