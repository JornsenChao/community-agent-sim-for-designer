// components/MapWithDraw.js
import React, { useRef } from 'react';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import { GeoJSON } from 'react-leaflet';

export default function MapWithDraw({ onGeometryCreated }) {
  const featureGroupRef = useRef(null);

  const center = [37.75, -122.3];
  const zoomLevel = 12;

  const onCreated = (e) => {
    const layerType = e.layerType;
    const layer = e.layer;

    // 将layer转为GeoJSON
    const geojsonFeature = layer.toGeoJSON(); // {type: 'Feature', geometry: {...}}
    const geometryOnly = geojsonFeature.geometry; // {type: 'Polygon', coordinates: [...]}

    onGeometryCreated && onGeometryCreated(geometryOnly);
  };

  return (
    <MapContainer
      center={center}
      zoom={zoomLevel}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="© OpenStreetMap contributors"
      />

      <FeatureGroup ref={featureGroupRef}>
        <EditControl
          position="topleft"
          draw={{
            rectangle: true,
            polygon: true, // 支持多边形
            circle: false,
            circlemarker: false,
            marker: false,
            polyline: false,
          }}
          edit={{
            edit: false,
            remove: false,
          }}
          onCreated={onCreated}
        />
      </FeatureGroup>
    </MapContainer>
  );
}
