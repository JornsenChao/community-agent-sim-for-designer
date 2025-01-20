// components/MarkMap.js
import React from 'react';
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function ClickHandler({ onClickMap }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      onClickMap && onClickMap(lat, lng);
    },
  });
  return null;
}

export default function MarkMap({ onClickMap }) {
  const center = [37.75, -122.3];
  const zoomLevel = 12;

  return (
    <MapContainer
      center={center}
      zoom={zoomLevel}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <ClickHandler onClickMap={onClickMap} />
    </MapContainer>
  );
}
