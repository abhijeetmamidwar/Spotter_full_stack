import React from "react";
import L from "leaflet";
import { MapContainer, TileLayer, Polyline, Marker, Popup } from "react-leaflet";
import ELDGrid from "./ELDGrid";

export default function TripLogs({ routeMap, geocoded, eldLogs }) {
  if (!routeMap || !geocoded || !eldLogs) return null;

  // Colored marker icons
  const currentIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const pickupIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const dropoffIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const fuelIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const restIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // Convert ORS [lng, lat] → Leaflet [lat, lng]
  const leg1Positions = routeMap.leg1 ? routeMap.leg1.map(([lng, lat]) => [lat, lng]) : [];
  const leg2Positions = routeMap.leg2 ? routeMap.leg2.map(([lng, lat]) => [lat, lng]) : [];

  // Compute bounds to fit all points
  const allPositions = [...leg1Positions, ...leg2Positions];
  let bounds;
  if (allPositions.length) {
    const lats = allPositions.map(p => p[0]);
    const lngs = allPositions.map(p => p[1]);
    bounds = [
      [Math.min(...lats), Math.min(...lngs)], // southwest
      [Math.max(...lats), Math.max(...lngs)]  // northeast
    ];
  }

  const getStopIcon = (type) => {
    if (type === "Destination") return dropoffIcon; 
    if (type && type.includes("Fuel")) return fuelIcon;
    return restIcon;
  };

  return (
    <div className="space-y-8">
      {/* Map */}
      <div className="h-96 w-full rounded-xl overflow-hidden shadow-lg border border-gray-200">
        <MapContainer bounds={bounds} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
          />

          {/* Leg 1: Current -> Pickup */}
          {leg1Positions.length > 1 && (
            <Polyline positions={leg1Positions} color="#3b82f6" weight={5} opacity={0.8} />
          )}

          {/* Leg 2: Pickup -> Dropoff */}
          {leg2Positions.length > 1 && (
            <Polyline positions={leg2Positions} color="#10b981" weight={5} opacity={0.8} />
          )}

          {/* Markers */}
          <Marker position={[geocoded.current.lat, geocoded.current.lng]} icon={currentIcon}>
            <Popup>Current Location</Popup>
          </Marker>

          <Marker position={[geocoded.pickup.lat, geocoded.pickup.lng]} icon={pickupIcon}>
            <Popup>Pickup Location</Popup>
          </Marker>

          <Marker position={[geocoded.dropoff.lat, geocoded.dropoff.lng]} icon={dropoffIcon}>
            <Popup>Dropoff Location</Popup>
          </Marker>

          {/* ELD Log Markers */}
          {eldLogs.map((log) => (
            log.stops.map((stop, idx) => {
                if (!stop.coord) return null;
                if (stop.type === "Dropoff") return null; // Already have dropoff marker
                if (stop.type === "Pickup") return null; // Already have pickup marker

                return (
                  <Marker 
                    key={`stop-${log.day_no}-${idx}`}
                    position={[stop.coord.lat, stop.coord.lng]} 
                    icon={getStopIcon(stop.type)}
                  >
                    <Popup>
                      <strong>{stop.type}</strong><br/>
                      Time: {stop.time}
                    </Popup>
                  </Marker>
                );
            })
          ))}

        </MapContainer>
      </div>

      {/* ELD Logs */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-800">Daily Logs</h2>
        {eldLogs.map((log) => (
            <div key={log.day_no} className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
                <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="font-semibold text-lg text-gray-700">Day {log.day_no} - {log.date}</h3>
                    <div className="text-sm text-gray-500 space-x-4">
                        <span>Drive: {log.summary.drive_hours}h</span>
                        <span>On Duty: {log.summary.on_duty_hours}h</span>
                        <span>Distance: {log.summary.distance_miles} mi</span>
                    </div>
                </div>
                
                <div className="p-6">
                    {/* Grid Visualization */}
                    <ELDGrid events={log.grid_events} date={log.date} />
                    
                    {/* Stops Table */}
                    <div className="mt-4">
                        <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Events & Stops</h4>
                        <table className="w-full text-sm text-left text-gray-600">
                            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                                <tr>
                                    <th className="px-4 py-2">Time</th>
                                    <th className="px-4 py-2">Type / Status</th>
                                    <th className="px-4 py-2">Location</th>
                                </tr>
                            </thead>
                            <tbody>
                                {log.stops.map((stop, i) => (
                                    <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                                        <td className="px-4 py-2 font-medium">{stop.time}</td>
                                        <td className="px-4 py-2">{stop.type}</td>
                                        <td className="px-4 py-2">
                                            {stop.coord ? `${stop.coord.lat.toFixed(4)}, ${stop.coord.lng.toFixed(4)}` : "N/A"}
                                        </td>
                                    </tr>
                                ))}
                                {log.stops.length === 0 && (
                                    <tr>
                                        <td colSpan="3" className="px-4 py-2 text-center text-gray-400 italic">No stops recorded for this day</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        ))}
      </div>
    </div>
  );
}
