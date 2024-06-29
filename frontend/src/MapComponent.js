// frontend/src/MapComponent.js
import L from 'leaflet';
import 'leaflet.heat';
import 'leaflet/dist/leaflet.css';
import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const MapComponent = () => {
  const { placeId } = useParams();
  const navigate = useNavigate();
  let map;

  useEffect(() => {
    map = L.map('map', {
      center: [0, 0], // Sets a default center
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

    return () => map.remove(); // Clean the map when disassembling the component
  }, [placeId]);

  const fetchNDVI = () => {
    fetch(`/ndvi/${placeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.ndvi) {
                alert(`NDVI Data: ${data.ndvi}`);
            } else {
                alert('NDVI data is not available');
            }
        })
        .catch(error => {
            console.error('Error fetching NDVI data:', error);
            alert('Failed to fetch NDVI data');
        });
  };

  const showNDVIHeatmap = () => {
    fetch(`/ndvi/heatmap/${placeId}`)  // Asegúrate de que este endpoint está disponible en tu backend
        .then(response => response.json())
        .then(data => {
            const heatData = data.map(d => [d.latitude, d.longitude, d.ndvi]);
            const heatLayer = L.heatLayer(heatData, {
                radius: 25,
                blur: 15,
                gradient: {0.4: 'blue', 0.65: 'lime', 1: 'red'}
            }).addTo(map);
        })
        .catch(error => {
            console.error('Error fetching NDVI heatmap data:', error);
            alert('Failed to fetch NDVI heatmap data');
        });
  };

  return (
    <div className="d-flex" style={{ height: '100vh' }}>
      <div className="flex-shrink-0 bg-light sidebar">
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          Go Back
        </button>
        <button className="btn btn-primary" onClick={fetchNDVI}>
          Get NDVI
        </button>
        <button className="btn btn-success" onClick={showNDVIHeatmap}>
          Show NDVI
        </button>
      </div>
      <div className="flex-grow-1" id="map"></div>
    </div>
  );
};

export default MapComponent;
