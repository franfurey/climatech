// frontend/src/PlacesList.js
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AddPlaceModal from './AddPlaceModal';

const PlacesList = () => {
    const [places, setPlaces] = useState([]);
    const [showModal, setShowModal] = useState(false); // Estado para controlar la visibilidad del modal
    const navigate = useNavigate();

    useEffect(() => {
        fetch('/api/places')  // Llamada a la API para obtener los lugares
            .then(response => response.json())
            .then(data => setPlaces(data))
            .catch(console.error);
    }, []);

    const handleDelete = (placeId) => {  // Manejador para borrar un lugar
        console.log('Deleting place:', placeId);
        if (window.confirm("¿Estás seguro de que deseas eliminar este lugar?")) {
            fetch(`/delete_place/${placeId}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setPlaces(places.filter(place => place.id !== placeId)); // Actualiza el estado para reflejar el lugar eliminado
                })
                .catch(error => {
                    console.error('Error al eliminar el lugar:', error);
                    alert('Error al eliminar el lugar');
                });
        }
    };

    return (
        <div className="container mt-4">
            <h1 className="mb-4 text-center">Mis Lugares</h1>
            <button className="btn btn-success mb-3" onClick={() => setShowModal(true)}>Agregar Lugar</button>
            <div className="row">
                {places.map(place => (
                    <div key={place.id} className="col-md-4 mb-4">
                        <div className="card shadow-sm">
                            <div className="card-body">
                                <h5 className="card-title">{place.name}</h5>
                                <p className="card-text">{place.description}</p>
                                <Link to={`/map/${place.id}`} className="btn btn-primary">Ver Mapa</Link>
                                <button className="btn btn-danger ms-2" onClick={() => handleDelete(place.id)}>Eliminar</button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            <AddPlaceModal show={showModal} handleClose={() => setShowModal(false)} />
        </div>
    );
};

export default PlacesList;