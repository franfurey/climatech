// frontend/src/MapComponent.js
import React, { useEffect } from 'react';
import L from 'leaflet';
import { useParams, useNavigate } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';

const MapComponent = () => {
  const { placeId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const map = L.map('map', {
      center: [0, 0], // Establece un centro por defecto
      zoom: 13
    });

    // Base layers
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles © Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }).addTo(map);

    L.control.layers({ "OpenStreetMap": osmLayer, "Satellite": satelliteLayer }).addTo(map);

    fetch(`/terrain/${placeId}`)
      .then(response => response.json())
      .then(data => {
        const geoJSON = typeof data.geojson === 'string' ? JSON.parse(data.geojson) : data.geojson;
        const geoJSONLayer = L.geoJSON(geoJSON).addTo(map);
        map.fitBounds(geoJSONLayer.getBounds());
      });

    return () => map.remove(); // Limpiar el mapa al desmontar el componente
  }, [placeId]);

  return (
    <div className="d-flex" style={{ height: '100vh' }}>
      <div className="flex-shrink-0 p-3 bg-light" style={{ width: '280px' }}>
        <button className="btn btn-primary mb-3" onClick={() => navigate('/')}>
          Volver
        </button>
        {/* Aquí puedes agregar más botones o contenido a la barra lateral */}
      </div>
      <div className="flex-grow-1" id="map"></div>
    </div>
  );
};

export default MapComponent;