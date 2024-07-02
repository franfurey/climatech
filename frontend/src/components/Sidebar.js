// frontend/src/components/Sidebar.js
import React from 'react';
import { useNavigate } from 'react-router-dom';

const Sidebar = () => {
    const navigate = useNavigate();

    return (
        <div className="d-flex flex-column bg-light p-3" style={{width: '200px'}}>
            <button className="btn btn-secondary mb-2" onClick={() => navigate('')}>
                Manage Places
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/wildfires')}>
                Wild-Fires
            </button>
        </div>
    );
};

export default Sidebar;