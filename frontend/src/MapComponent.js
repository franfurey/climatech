import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import 'leaflet.heat';
import 'leaflet/dist/leaflet.css';
import { useParams, useNavigate } from 'react-router-dom';

const MapComponent = () => {
  const { placeId } = useParams();
  const navigate = useNavigate();
  const [dates, setDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const mapRef = useRef(null); // Usamos useRef para mantener una referencia al mapa

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map('map', {
        center: [0, 0], // Sets a default center
        zoom: 13
      });

      // Base layers
      const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapRef.current);

      const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
      }).addTo(mapRef.current);

      L.control.layers({ "OpenStreetMap": osmLayer, "Satellite": satelliteLayer }).addTo(mapRef.current);
    }

    fetch(`/terrain/${placeId}`)
      .then(response => response.json())
      .then(data => {
        const geoJSON = typeof data.geojson === 'string' ? JSON.parse(data.geojson) : data.geojson;
        L.geoJSON(geoJSON).addTo(mapRef.current);
        mapRef.current.fitBounds(L.geoJSON(geoJSON).getBounds());
      });

    fetch(`/ndvi/dates/${placeId}`)
      .then(response => response.json())
      .then(data => {
        setDates(data.dates);
      });

    // Aseguramos de limpiar el mapa al desmontar el componente
    return () => {
      mapRef.current && mapRef.current.remove();
    };
  }, [placeId]);

  const fetchNDVI = () => {
    fetch(`/ndvi/${placeId}`)
        .then(response => response.json())
        .then(data => {
            alert(`NDVI Data: ${data.ndvi}`);
        })
        .catch(error => {
            console.error('Error fetching NDVI data:', error);
            alert('Failed to fetch NDVI data');
        });
  };

  const showNDVIHeatmap = () => {
    if (!selectedDate) {
      console.log('No date selected');
      alert('Please select a date first.');
      return;
    }

    console.log(`Fetching NDVI heatmap data for date: ${selectedDate}`);
    fetch(`/ndvi/heatmap/${placeId}?date=${selectedDate}`)
        .then(response => response.json())
        .then(data => {
            const heatData = data.data.map(d => [d.latitude, d.longitude, d.ndvi]);
            L.heatLayer(heatData, {
                radius: 25,
                blur: 15,
                gradient: {0.4: 'blue', 0.65: 'lime', 1: 'red'}
            }).addTo(mapRef.current);
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
        <select value={selectedDate} onChange={e => setSelectedDate(e.target.value)} className="form-select">
          <option value="">Select a Date</option>
          {dates.map(date => (
            <option key={date} value={date}>{new Date(date).toLocaleDateString()}</option>
          ))}
        </select>
        <button className="btn btn-success" onClick={showNDVIHeatmap}>
          Show NDVI
        </button>
      </div>
      <div className="flex-grow-1" id="map"></div>
    </div>
  );
};

export default MapComponent;
