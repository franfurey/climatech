// frontend/src/AddPlaceModal.js
import React, { useState } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const AddPlaceModal = ({ show, handleClose }) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [file, setFile] = useState(null);
    const navigate = useNavigate();

    const handleSubmit = (event) => {
        event.preventDefault();

        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        formData.append('geojson', file);

        fetch('/places/add_place', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert('Place added successfully!');
            handleClose(); // Close the modal
            navigate('/'); // Navigate to the homepage or refresh
        })
        .catch(error => {
            console.error('Error adding place:', error);
            alert('Error adding place');
        });
    };

    return (
        <Modal show={show} onHide={handleClose}>
            <Modal.Header closeButton>
                <Modal.Title>Add a New Place</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-3" controlId="formBasicEmail">
                        <Form.Label>Name</Form.Label>
                        <Form.Control type="text" placeholder="Enter place name" onChange={e => setName(e.target.value)} required />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicPassword">
                        <Form.Label>Description</Form.Label>
                        <Form.Control type="text" placeholder="Description" onChange={e => setDescription(e.target.value)} required />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicFile">
                        <Form.Label>GeoJSON File</Form.Label>
                        <Form.Control type="file" onChange={e => setFile(e.target.files[0])} required />
                    </Form.Group>
                    <Button variant="primary" type="submit">
                        Submit
                    </Button>
                </Form>
            </Modal.Body>
        </Modal>
    );
};

export default AddPlaceModal;
