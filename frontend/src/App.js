// frontend/src/App.js
import './styles.css';
import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import PlacesList from './PlacesList';
import MapComponent from './MapComponent';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<PlacesList />} exact />
        <Route path="/map/:placeId" element={<MapComponent />} />
      </Routes>
    </Router>
  );
};

export default App;
