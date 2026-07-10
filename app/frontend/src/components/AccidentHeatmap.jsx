import { useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet.heat';
import L from 'leaflet';

const DEFAULT_CENTER = [37.5, -96];

const HeatmapLayer = ({ points }) => {
  const map = useMap();
  const heatLayerRef = useRef(null);

  const heatData = useMemo(() => {
    if (!points.length) {
      return [];
    }
    const max = Math.max(...points.map((p) => p.total_accidents));
    return points.map((point) => [
      point.start_lat,
      point.start_lng,
      max ? Math.max(0.1, point.total_accidents / max) : 0.1,
    ]);
  }, [points]);

  useEffect(() => {
    if (!map) return undefined;

    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }

    if (!heatData.length) {
      return undefined;
    }

    const layer = L.heatLayer(heatData, {
      radius: 28,
      blur: 30,
      minOpacity: 0.25,
      maxZoom: 10,
      gradient: {
        0.0: '#1e293b',
        0.2: '#2563eb',
        0.4: '#22d3ee',
        0.6: '#facc15',
        0.8: '#f97316',
        1.0: '#dc2626',
      },
    }).addTo(map);

    heatLayerRef.current = layer;

    return () => {
      if (layer) {
        map.removeLayer(layer);
      }
    };
  }, [map, heatData]);

  return null;
};

const FitBounds = ({ points }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    if (!points.length) {
      map.setView(DEFAULT_CENTER, 4);
      return;
    }

    const bounds = L.latLngBounds(points.map((p) => [p.start_lat, p.start_lng]));
    map.fitBounds(bounds, { padding: [30, 30] });
  }, [map, points]);

  return null;
};

const AccidentHeatmap = ({ points, isInteractive = true }) => {
  return (
    <MapContainer
      className="leaflet-map"
      center={DEFAULT_CENTER}
      zoom={4}
      minZoom={3}
      maxZoom={12}
      scrollWheelZoom={isInteractive}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <HeatmapLayer points={points} />
      <FitBounds points={points} />
    </MapContainer>
  );
};

export default AccidentHeatmap;


