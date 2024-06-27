// frontend/src/AddPlaceForm.js
import React, { useState } from 'react';

const AddPlaceForm = ({ onAddPlace }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [geojson, setGeojson] = useState(null);

  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('geojson', geojson);

    onAddPlace(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="name">Nombre del Lugar</label>
        <input
          type="text"
          className="form-control"
          id="name"
          value={name}
          onChange={e => setName(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="description">Descripción</label>
        <textarea
          className="form-control"
          id="description"
          value={description}
          onChange={e => setDescription(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="geojson">Archivo GeoJSON</label>
        <input
          type="file"
          className="form-control"
          id="geojson"
          onChange={e => setGeojson(e.target.files[0])}
          required
        />
      </div>
      <button type="submit" className="btn btn-primary">Agregar Lugar</button>
    </form>
  );
};

export default AddPlaceForm;