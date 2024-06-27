// BaseLayout.js
import React from 'react';
import 'leaflet/dist/leaflet.css';
import 'bootstrap/dist/css/bootstrap.min.css';

const BaseLayout = ({ children }) => {
  return (
    <div className="container">
      {children}
    </div>
  );
};

export default BaseLayout;
