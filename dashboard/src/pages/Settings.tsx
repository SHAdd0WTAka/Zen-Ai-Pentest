import { useState } from 'react'
import { Save, User, Shield, Bell, Database } from 'lucide-react'

export function Settings() {
  const [activeTab, setActiveTab] = useState('profile')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account and application settings
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar */}
        <div className="lg:w-64">
          <nav className="space-y-1">
            {[
              { id: 'profile', name: 'Profile', icon: User },
              { id: 'security', name: 'Security', icon: Shield },
              { id: 'notifications', name: 'Notifications', icon: Bell },
              { id: 'api', name: 'API Keys', icon: Database },
            ].map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === item.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Profile Settings</h2>
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Username</label>
                    <input type="text" defaultValue="admin" className="input mt-1" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input type="email" defaultValue="admin@example.com" className="input mt-1" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">First Name</label>
                    <input type="text" className="input mt-1" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Name</label>
                    <input type="text" className="input mt-1" />
                  </div>
                </div>
                <div className="flex justify-end">
                  <button className="btn-primary">
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Security Settings</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Current Password</label>
                  <input type="password" className="input mt-1" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Password</label>
                  <input type="password" className="input mt-1" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                  <input type="password" className="input mt-1" />
                </div>
                <div className="flex justify-end">
                  <button className="btn-primary">
                    <Save className="h-4 w-4 mr-2" />
                    Update Password
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Notification Preferences</h2>
              <div className="space-y-4">
                {[
                  { id: 'email_scan', label: 'Email me when scan completes' },
                  { id: 'email_vuln', label: 'Email me when vulnerability is found' },
                  { id: 'slack', label: 'Send Slack notifications' },
                  { id: 'webhook', label: 'Webhook notifications' },
                ].map((item) => (
                  <div key={item.id} className="flex items-center">
                    <input
                      type="checkbox"
                      id={item.id}
                      className="h-4 w-4 text-primary-600 rounded border-gray-300"
                    />
                    <label htmlFor={item.id} className="ml-3 text-sm text-gray-700">
                      {item.label}
                    </label>
                  </div>
                ))}
                <div className="flex justify-end pt-4">
                  <button className="btn-primary">
                    <Save className="h-4 w-4 mr-2" />
                    Save Preferences
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">API Keys</h2>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">Production API Key</p>
                      <p className="text-xs text-gray-500">Created on Jan 1, 2024</p>
                    </div>
                    <button className="text-danger-600 hover:text-danger-700 text-sm font-medium">
                      Revoke
                    </button>
                  </div>
                  <div className="mt-2 p-2 bg-gray-100 rounded font-mono text-sm">
                    zen_live_xxxxxxxxxxxxxxxx
                  </div>
                </div>
                <button className="btn-primary">
                  Generate New API Key
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}