import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { scansAPI } from '../services/api';
import { ScanLine, ArrowRight, ArrowLeft, AlertCircle } from 'lucide-react';
import './NewScan.css';

const steps = ['Target', 'Configuration', 'Review'];

function NewScan() {
    const navigate = useNavigate();
    const [activeStep, setActiveStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [scanConfig, setScanConfig] = useState({
        target: '',
        goal: '',
        scan_type: 'comprehensive',
        safety_level: 'non_destructive',
    });

    const handleNext = () => {
        setActiveStep((prevStep) => prevStep + 1);
    };

    const handleBack = () => {
        setActiveStep((prevStep) => prevStep - 1);
    };

    const handleChange = (field) => (e) => {
        setScanConfig({ ...scanConfig, [field]: e.target.value });
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await scansAPI.create(scanConfig);
            navigate(`/scans/${response.data.id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to start scan');
            setLoading(false);
        }
    };

    const renderStepContent = (step) => {
        switch (step) {
            case 0:
                return (
                    <div className="form-step">
                        <div className="form-group">
                            <label>Target *</label>
                            <input
                                type="text"
                                value={scanConfig.target}
                                onChange={handleChange('target')}
                                placeholder="e.g., example.com or 192.168.1.1"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Goal (Optional)</label>
                            <textarea
                                value={scanConfig.goal}
                                onChange={handleChange('goal')}
                                placeholder="e.g., Find all vulnerabilities"
                                rows={3}
                            />
                        </div>
                    </div>
                );
            case 1:
                return (
                    <div className="form-step">
                        <div className="form-group">
                            <label>Scan Type</label>
                            <select
                                value={scanConfig.scan_type}
                                onChange={handleChange('scan_type')}
                            >
                                <option value="quick">Quick (Port scan only)</option>
                                <option value="standard">Standard (Common vulnerabilities)</option>
                                <option value="comprehensive">Comprehensive (Full assessment)</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Safety Level</label>
                            <select
                                value={scanConfig.safety_level}
                                onChange={handleChange('safety_level')}
                            >
                                <option value="read_only">Read Only (Passive recon)</option>
                                <option value="non_destructive">Non-Destructive (Safe tests)</option>
                                <option value="destructive">Destructive (May modify data)</option>
                                <option value="exploit">Full Exploitation</option>
                            </select>
                        </div>
                    </div>
                );
            case 2:
                return (
                    <div className="form-step">
                        <div className="review-card">
                            <h3>Scan Configuration</h3>
                            <div className="review-item">
                                <span className="review-label">Target:</span>
                                <span className="review-value">{scanConfig.target}</span>
                            </div>
                            <div className="review-item">
                                <span className="review-label">Goal:</span>
                                <span className="review-value">{scanConfig.goal || 'Default comprehensive assessment'}</span>
                            </div>
                            <div className="review-item">
                                <span className="review-label">Scan Type:</span>
                                <span className="review-value">{scanConfig.scan_type}</span>
                            </div>
                            <div className="review-item">
                                <span className="review-label">Safety Level:</span>
                                <span className="review-value">{scanConfig.safety_level}</span>
                            </div>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="new-scan-page">
            <header className="page-header">
                <ScanLine size={28} />
                <h1>New Scan</h1>
            </header>

            {error && (
                <div className="error-alert">
                    <AlertCircle size={18} />
                    {error}
                </div>
            )}

            <div className="stepper">
                {steps.map((label, index) => (
                    <div 
                        key={label} 
                        className={`step ${index === activeStep ? 'active' : ''} ${index < activeStep ? 'completed' : ''}`}
                    >
                        <div className="step-number">{index + 1}</div>
                        <div className="step-label">{label}</div>
                    </div>
                ))}
            </div>

            <div className="step-content">
                {renderStepContent(activeStep)}
            </div>

            <div className="step-actions">
                {activeStep > 0 && (
                    <button onClick={handleBack} className="btn-secondary">
                        <ArrowLeft size={18} />
                        Back
                    </button>
                )}
                {activeStep < steps.length - 1 ? (
                    <button
                        onClick={handleNext}
                        disabled={!scanConfig.target}
                        className="btn-primary"
                    >
                        Next
                        <ArrowRight size={18} />
                    </button>
                ) : (
                    <button
                        onClick={handleSubmit}
                        disabled={loading}
                        className="btn-primary"
                    >
                        {loading ? (
                            <>
                                <span className="spinner-small"></span>
                                Starting...
                            </>
                        ) : (
                            <>
                                <ScanLine size={18} />
                                Start Scan
                            </>
                        )}
                    </button>
                )}
            </div>
        </div>
    );
}

export default NewScan;
