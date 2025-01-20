// components/AgentMap.js
import React, { useRef, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  useMapEvents,
  Marker,
  Popup,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet 默认的Marker icon需要修正路径
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function ClickHandler({ onClickMap }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      onClickMap && onClickMap(lat, lng);
    },
  });
  return null;
}

// 用来生成不同颜色的 Marker icon
function createColoredIcon(color) {
  // 这里你可以自行选择换个Marker图标底图, 也可以套leaflet-color-marker
  // 暂且我们做一个 hack: 用 CSS filter 改颜色(并不很准确), 或使用其他图标
  // 这里演示用 text label. 也可贴图.
  return new L.DivIcon({
    html: `<div style="
      background-color:${color};
      width:20px; 
      height:20px; 
      border-radius:50%; 
      border:2px solid #fff
    "></div>`,
    className: '',
  });
}

export default function AgentMap({ agents, onClickMap }) {
  const center = [37.75, -122.3];
  const zoomLevel = 12;

  // 颜色数组，用于区分不同Agent
  const colorPalette = [
    'red',
    'blue',
    'green',
    'purple',
    'orange',
    'brown',
    'gray',
  ];

  return (
    <MapContainer
      center={center}
      zoom={zoomLevel}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {/* 点击事件 */}
      <ClickHandler onClickMap={onClickMap} />

      {/* 为每个Agent放置2个marker: home, work */}
      {agents.map((ag, idx) => {
        const color = colorPalette[idx % colorPalette.length] || 'red';
        const homePos = [ag.home.lat, ag.home.lng];
        const workPos = [ag.work.lat, ag.work.lng];

        return (
          <React.Fragment key={ag.agentId}>
            <Marker position={homePos} icon={createColoredIcon(color)}>
              <Popup>Agent {ag.agentId} - Home</Popup>
            </Marker>
            <Marker position={workPos} icon={createColoredIcon(color)}>
              <Popup>Agent {ag.agentId} - Work</Popup>
            </Marker>
          </React.Fragment>
        );
      })}
    </MapContainer>
  );
}
