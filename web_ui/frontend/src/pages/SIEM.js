/**
 * SIEM Integration Page
 * Q2 2026 Feature
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = '/api/v1';

export default function SIEM() {
  const [connections, setConnections] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    type: 'splunk',
    url: '',
    api_key: '',
    index: ''
  });

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await axios.get(`${API_BASE}/siem/status`);
      setConnections(response.data || []);
    } catch (error) {
      console.error('Failed to fetch SIEM connections:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/siem/connect`, formData);
      setShowForm(false);
      fetchConnections();
      setFormData({ name: '', type: 'splunk', url: '', api_key: '', index: '' });
    } catch (error) {
      alert('Failed to connect: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">SIEM Integration</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors"
        >
          {showForm ? 'Cancel' : '+ Add SIEM'}
        </button>
      </div>

      {/* Add SIEM Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Connect to SIEM</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="My Splunk Instance"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({...formData, type: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="splunk">Splunk</option>
                <option value="elastic">Elasticsearch</option>
                <option value="sentinel">Azure Sentinel</option>
                <option value="qradar">IBM QRadar</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({...formData, url: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="https://splunk.example.com:8088"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key / Token
              </label>
              <input
                type="password"
                value={formData.api_key}
                onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="your-api-key-here"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Index (Optional)
              </label>
              <input
                type="text"
                value={formData.index}
                onChange={(e) => setFormData({...formData, index: e.target.value})}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="security"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                className="bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-emerald-700 transition-colors"
              >
                Test & Connect
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Connected SIEMs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connections.map(conn => (
          <div key={conn.name} className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-gray-800">{conn.name}</h3>
                <p className="text-sm text-gray-500 capitalize">{conn.type}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                conn.connected 
                  ? 'bg-emerald-100 text-emerald-700' 
                  : 'bg-red-100 text-red-700'
              }`}>
                {conn.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <p className="text-sm text-gray-600 truncate">{conn.url}</p>
            <div className="mt-4 pt-4 border-t flex gap-2">
              <button className="text-sm text-emerald-600 hover:underline">
                Test Connection
              </button>
              <span className="text-gray-300">|</span>
              <button className="text-sm text-red-600 hover:underline">
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>

      {connections.length === 0 && !showForm && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">No SIEM integrations configured</p>
          <p className="text-sm">Connect to Splunk, Elastic, Sentinel, or QRadar</p>
        </div>
      )}
    </div>
  );
}
