/**
 * Settings Page
 */

import React from 'react';

export default function Settings() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Settings</h2>
      
      <div className="space-y-6">
        {/* General Settings */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">General</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dashboard Refresh Interval
              </label>
              <select className="border rounded-lg px-3 py-2 w-full max-w-xs">
                <option>30 seconds</option>
                <option>1 minute</option>
                <option>5 minutes</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="notifications" className="rounded" />
              <label htmlFor="notifications" className="text-sm text-gray-700">
                Enable browser notifications
              </label>
            </div>
          </div>
        </div>

        {/* API Settings */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">API Configuration</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Endpoint
              </label>
              <input
                type="text"
                value="http://localhost:8000"
                className="border rounded-lg px-3 py-2 w-full max-w-md"
                readOnly
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Version
              </label>
              <p className="text-sm text-gray-600">v1.0</p>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">About</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Version:</strong> 2.1.0</p>
            <p><strong>React Dashboard:</strong> v2.1.0</p>
            <p><strong>API:</strong> v1.0</p>
            <p className="mt-4 text-gray-500">
              © 2026 Zen AI Pentest. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
