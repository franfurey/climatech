// frontend/src/components/WildFiresMap.js
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const WildFiresMap = () => {
    const [wildFires, setWildFires] = useState([]);

    useEffect(() => {
        console.log('Fetching wildfire data...');
        fetch('/wildfires?satellite=MODIS_NRT&days=3') // Ajusta según tus necesidades
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Data received:', data);
                setWildFires(data);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, []);

    // Configuración del icono de incendio
    const fireIcon = new L.Icon({
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-icon.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34]
    });

    if (!Array.isArray(wildFires)) {
        console.error('Expected wildFires to be an array, received:', wildFires);
        return <div>Error: Data format incorrect.</div>;
    }

    return (
        <MapContainer center={[-34.6037, -58.3816]} zoom={5} style={{ height: '500px', width: '100%' }}>
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {wildFires.map(fire => (
                <Marker
                    key={fire.id}
                    position={[fire.latitude, fire.longitude]}
                    icon={fireIcon}>
                    <Popup>
                        Brillo: {fire.brightness}<br />
                        Fecha: {new Date(fire.acq_date).toLocaleDateString()}<br />
                        Hora: {fire.acq_time}<br />
                        Satélite: {fire.satellite}<br />
                        Confianza: {fire.confidence}
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
};

export default WildFiresMap;