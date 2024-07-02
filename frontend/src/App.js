// frontend/src/App.js
import './styles.css';
import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter as Router, Route, Routes, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import PlacesList from './components/PlacesList';
import MapComponent from './components/MapComponent';
import WildFiresMap from './components/WildFiresMap';

const Layout = () => {
  const location = useLocation();
  // Check if the current path contains '/map/' and has any id parameters
  const showSidebar = !location.pathname.startsWith("/map/");

  return (
    <div className="d-flex">
      {showSidebar && <Sidebar />}
      <div className="flex-grow-1">
        <Routes>
          <Route path="/" element={<PlacesList />} />
          <Route path="/map/:placeId" element={<MapComponent />} />
          <Route path="/wildfires" element={<WildFiresMap />} />
        </Routes>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <Layout />
    </Router>
  );
};

export default App;
