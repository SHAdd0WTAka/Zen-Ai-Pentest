import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { Settings as SettingsIcon, User, Bell, Shield, Slack, Mail } from 'lucide-react';
import './Settings.css';

function Settings() {
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState('profile');
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="settings-page">
            <header className="page-header">
                <div className="header-title">
                    <SettingsIcon size={28} />
                    <h1>Settings</h1>
                </div>
            </header>

            <div className="settings-layout">
                <aside className="settings-sidebar">
                    <button 
                        className={activeTab === 'profile' ? 'active' : ''}
                        onClick={() => setActiveTab('profile')}
                    >
                        <User size={18} />
                        Profile
                    </button>
                    <button 
                        className={activeTab === 'notifications' ? 'active' : ''}
                        onClick={() => setActiveTab('notifications')}
                    >
                        <Bell size={18} />
                        Notifications
                    </button>
                    <button 
                        className={activeTab === 'security' ? 'active' : ''}
                        onClick={() => setActiveTab('security')}
                    >
                        <Shield size={18} />
                        Security
                    </button>
                </aside>

                <div className="settings-content">
                    {activeTab === 'profile' && (
                        <div className="settings-section">
                            <h2>Profile Settings</h2>
                            <div className="form-group">
                                <label>Username</label>
                                <input type="text" value={user?.username || ''} disabled />
                            </div>
                            <div className="form-group">
                                <label>Email</label>
                                <input type="email" placeholder="your@email.com" />
                            </div>
                            <div className="form-group">
                                <label>Role</label>
                                <input type="text" value={user?.role || 'Operator'} disabled />
                            </div>
                            <button className="btn-primary" onClick={handleSave}>
                                {saved ? 'Saved!' : 'Save Changes'}
                            </button>
                        </div>
                    )}

                    {activeTab === 'notifications' && (
                        <div className="settings-section">
                            <h2>Notification Settings</h2>
                            
                            <div className="setting-item">
                                <div className="setting-info">
                                    <Mail size={20} />
                                    <div>
                                        <label>Email Notifications</label>
                                        <p>Receive scan completion emails</p>
                                    </div>
                                </div>
                                <label className="toggle">
                                    <input type="checkbox" defaultChecked />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="setting-item">
                                <div className="setting-info">
                                    <Slack size={20} />
                                    <div>
                                        <label>Slack Integration</label>
                                        <p>Send notifications to Slack</p>
                                    </div>
                                </div>
                                <label className="toggle">
                                    <input type="checkbox" />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="setting-item">
                                <div className="setting-info">
                                    <Bell size={20} />
                                    <div>
                                        <label>Critical Alerts</label>
                                        <p>Notify on critical findings</p>
                                    </div>
                                </div>
                                <label className="toggle">
                                    <input type="checkbox" defaultChecked />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <button className="btn-primary" onClick={handleSave}>
                                {saved ? 'Saved!' : 'Save Changes'}
                            </button>
                        </div>
                    )}

                    {activeTab === 'security' && (
                        <div className="settings-section">
                            <h2>Security Settings</h2>
                            
                            <div className="form-group">
                                <label>Current Password</label>
                                <input type="password" placeholder="••••••••" />
                            </div>
                            <div className="form-group">
                                <label>New Password</label>
                                <input type="password" placeholder="••••••••" />
                            </div>
                            <div className="form-group">
                                <label>Confirm New Password</label>
                                <input type="password" placeholder="••••••••" />
                            </div>

                            <button className="btn-primary" onClick={handleSave}>
                                {saved ? 'Saved!' : 'Update Password'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Settings;
