// components/MapWithDraw.js

import React, { useRef } from 'react';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';

// (1) 导入 leaflet 基础样式 + leaflet-draw 样式
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';

// (2) 再导入 react-leaflet-draw
import { EditControl } from 'react-leaflet-draw';
console.log({ FeatureGroup, EditControl });
export default function MapWithDraw({ onBoundsChange }) {
  const featureGroupRef = useRef(null);

  const center = [37.75, -122.3];
  const zoomLevel = 12;

  const onCreated = (e) => {
    const layerType = e.layerType;
    const layer = e.layer;

    if (layerType === 'rectangle') {
      const bounds = layer.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();

      const minx = sw.lng;
      const miny = sw.lat;
      const maxx = ne.lng;
      const maxy = ne.lat;

      onBoundsChange && onBoundsChange({ minx, miny, maxx, maxy });
    }
  };

  const onEdited = (e) => {
    // 如果只允许画一个矩形，可以在这里更新 onBoundsChange
  };

  const onDeleted = (e) => {
    // 如果把矩形删了，就清空
    onBoundsChange && onBoundsChange(null);
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
            polygon: false,
            circle: false,
            circlemarker: false,
            marker: false,
            polyline: false,
          }}
          edit={{
            edit: true,
            remove: true,
          }}
          onCreated={onCreated}
          onEdited={onEdited}
          onDeleted={onDeleted}
        />
      </FeatureGroup>
    </MapContainer>
  );
}
