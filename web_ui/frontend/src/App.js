import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import Login from './components/auth/Login';
import Dashboard from './pages/Dashboard';
import Scans from './pages/Scans';
import ScanDetail from './pages/ScanDetail';
import NewScan from './pages/NewScan';
import Findings from './pages/Findings';
import Scheduler from './pages/Scheduler';
import Settings from './pages/Settings';
import Layout from './components/Layout';
import './App.css';

function PrivateRoute({ children }) {
  const { isAuthenticated, checkAuth } = useAuthStore();
  
  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return isAuthenticated ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="scans" element={<Scans />} />
          <Route path="scans/new" element={<NewScan />} />
          <Route path="scans/:id" element={<ScanDetail />} />
          <Route path="findings" element={<Findings />} />
          <Route path="scheduler" element={<Scheduler />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
