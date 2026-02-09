import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scansAPI, toolsAPI } from '../services/api';
import { 
  ScanLine, 
  ArrowRight, 
  ArrowLeft, 
  AlertCircle,
  Check,
  Target,
  Shield,
  Zap,
  Globe,
  Server,
  Wifi,
  FileSearch,
  Lock
} from 'lucide-react';
import './NewScan.css';

const STEPS = ['Target', 'Configuration', 'Tools', 'Review'];

const SCAN_TYPES = [
  { 
    id: 'quick', 
    name: 'Quick Scan', 
    description: 'Fast port scan and basic reconnaissance',
    icon: Zap,
    color: '#3b82f6',
    estimatedTime: '~5 min'
  },
  { 
    id: 'standard', 
    name: 'Standard Scan', 
    description: 'Common vulnerabilities and misconfigurations',
    icon: Shield,
    color: '#eab308',
    estimatedTime: '~15 min'
  },
  { 
    id: 'comprehensive', 
    name: 'Comprehensive', 
    description: 'Full assessment with all tools',
    icon: Lock,
    color: '#8b5cf6',
    estimatedTime: '~30 min'
  }
];

const SAFETY_LEVELS = [
  { id: 'read_only', name: 'Read Only', description: 'Passive reconnaissance only', icon: FileSearch },
  { id: 'non_destructive', name: 'Non-Destructive', description: 'Safe tests without modification', icon: Shield },
  { id: 'destructive', name: 'Destructive', description: 'May modify data (test systems only)', icon: AlertCircle },
  { id: 'exploit', name: 'Full Exploitation', description: 'Full exploitation attempts', icon: Zap }
];

const TOOL_CATEGORIES = {
  network: { name: 'Network', icon: Server, color: '#3b82f6' },
  web: { name: 'Web Security', icon: Globe, color: '#22c55e' },
  exploitation: { name: 'Exploitation', icon: Zap, color: '#ef4444' },
  brute_force: { name: 'Brute Force', icon: Lock, color: '#f59e0b' },
  recon: { name: 'Reconnaissance', icon: FileSearch, color: '#8b5cf6' },
  ad: { name: 'Active Directory', icon: Shield, color: '#ec4899' },
  wireless: { name: 'Wireless', icon: Wifi, color: '#06b6d4' }
};

function NewScan() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [availableTools, setAvailableTools] = useState([]);
  const [scanConfig, setScanConfig] = useState({
    target: '',
    name: '',
    goal: '',
    scan_type: 'comprehensive',
    safety_level: 'non_destructive',
    selected_tools: [],
    schedule: null
  });

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await toolsAPI.getAll();
      setAvailableTools(response.data?.tools || []);
    } catch (error) {
      console.error('Error fetching tools:', error);
    }
  };

  const handleNext = () => {
    if (validateStep()) {
      setActiveStep(prev => prev + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
    setError(null);
  };

  const validateStep = () => {
    switch (activeStep) {
      case 0:
        if (!scanConfig.target.trim()) {
          setError('Please enter a target');
          return false;
        }
        return true;
      case 2:
        if (scanConfig.selected_tools.length === 0) {
          setError('Please select at least one tool');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await scansAPI.create({
        target: scanConfig.target,
        name: scanConfig.name || `${scanConfig.scan_type} scan of ${scanConfig.target}`,
        scan_type: scanConfig.scan_type,
        safety_level: scanConfig.safety_level,
        tools: scanConfig.selected_tools,
        goal: scanConfig.goal
      });
      navigate(`/scans/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan');
      setLoading(false);
    }
  };

  const toggleTool = (toolName) => {
    setScanConfig(prev => ({
      ...prev,
      selected_tools: prev.selected_tools.includes(toolName)
        ? prev.selected_tools.filter(t => t !== toolName)
        : [...prev.selected_tools, toolName]
    }));
  };

  const selectAllTools = (category) => {
    const categoryTools = availableTools
      .filter(t => t.category === category)
      .map(t => t.name);
    
    setScanConfig(prev => ({
      ...prev,
      selected_tools: [...new Set([...prev.selected_tools, ...categoryTools])]
    }));
  };

  const getCategoryIcon = (category) => {
    const cat = TOOL_CATEGORIES[category];
    if (cat) {
      const IconComponent = cat.icon;
      return <IconComponent size={18} style={{ color: cat.color }} />;
    }
    return <Server size={18} />;
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <div className="step-content-form">
            <div className="form-section">
              <label className="section-label">
                <Target size={20} />
                Target Information
              </label>
              <div className="form-group large">
                <label>Target Host *</label>
                <input
                  type="text"
                  value={scanConfig.target}
                  onChange={(e) => setScanConfig({...scanConfig, target: e.target.value})}
                  placeholder="e.g., example.com, 192.168.1.1, https://target.com"
                  required
                  autoFocus
                />
                <span className="help-text">
                  Enter a domain, IP address, or URL to scan
                </span>
              </div>
              <div className="form-group">
                <label>Scan Name (optional)</label>
                <input
                  type="text"
                  value={scanConfig.name}
                  onChange={(e) => setScanConfig({...scanConfig, name: e.target.value})}
                  placeholder="e.g., Production Server Assessment"
                />
              </div>
            </div>

            <div className="form-section">
              <label className="section-label">
                <FileSearch size={20} />
                Objective
              </label>
              <div className="form-group">
                <textarea
                  value={scanConfig.goal}
                  onChange={(e) => setScanConfig({...scanConfig, goal: e.target.value})}
                  placeholder="What do you want to achieve with this scan? e.g., Find all SQL injection vulnerabilities, Perform comprehensive security assessment..."
                  rows={4}
                />
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="step-content-form">
            <div className="form-section">
              <label className="section-label">Scan Profile</label>
              <div className="scan-type-cards">
                {SCAN_TYPES.map((type) => {
                  const Icon = type.icon;
                  return (
                    <div
                      key={type.id}
                      className={`scan-type-card ${scanConfig.scan_type === type.id ? 'selected' : ''}`}
                      onClick={() => setScanConfig({...scanConfig, scan_type: type.id})}
                    >
                      <div className="scan-type-icon" style={{ backgroundColor: `${type.color}20`, color: type.color }}>
                        <Icon size={24} />
                      </div>
                      <div className="scan-type-info">
                        <h4>{type.name}</h4>
                        <p>{type.description}</p>
                        <span className="estimated-time">{type.estimatedTime}</span>
                      </div>
                      {scanConfig.scan_type === type.id && (
                        <div className="check-badge">
                          <Check size={16} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="form-section">
              <label className="section-label">Safety Level</label>
              <div className="safety-levels">
                {SAFETY_LEVELS.map((level) => {
                  const Icon = level.icon;
                  return (
                    <div
                      key={level.id}
                      className={`safety-card ${scanConfig.safety_level === level.id ? 'selected' : ''}`}
                      onClick={() => setScanConfig({...scanConfig, safety_level: level.id})}
                    >
                      <Icon size={20} />
                      <div>
                        <h4>{level.name}</h4>
                        <p>{level.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-content-form">
            <div className="form-section">
              <div className="tools-header">
                <label className="section-label">Select Tools</label>
                <span className="selected-count">
                  {scanConfig.selected_tools.length} selected
                </span>
              </div>
              
              <div className="tools-by-category">
                {Object.entries(TOOL_CATEGORIES).map(([category, info]) => {
                  const categoryTools = availableTools.filter(t => t.category === category);
                  if (categoryTools.length === 0) return null;
                  
                  const allSelected = categoryTools.every(t => 
                    scanConfig.selected_tools.includes(t.name)
                  );
                  
                  return (
                    <div key={category} className="tool-category">
                      <div className="category-header">
                        <div className="category-title">
                          {getCategoryIcon(category)}
                          <span>{info.name}</span>
                          <span className="tool-count">({categoryTools.length})</span>
                        </div>
                        <button
                          type="button"
                          className="select-all-btn"
                          onClick={() => selectAllTools(category)}
                        >
                          {allSelected ? 'Deselect All' : 'Select All'}
                        </button>
                      </div>
                      <div className="tools-grid">
                        {categoryTools.map((tool) => (
                          <div
                            key={tool.name}
                            className={`tool-card ${scanConfig.selected_tools.includes(tool.name) ? 'selected' : ''}`}
                            onClick={() => toggleTool(tool.name)}
                          >
                            <div className="tool-checkbox">
                              {scanConfig.selected_tools.includes(tool.name) && <Check size={14} />}
                            </div>
                            <div className="tool-info">
                              <span className="tool-name">{tool.name}</span>
                              <span className="tool-desc">{tool.description?.substring(0, 50)}...</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-content-form">
            <div className="review-card">
              <h3>Review Configuration</h3>
              
              <div className="review-section">
                <h4>Target</h4>
                <div className="review-item">
                  <span className="label">Target:</span>
                  <span className="value highlight">{scanConfig.target}</span>
                </div>
                {scanConfig.name && (
                  <div className="review-item">
                    <span className="label">Name:</span>
                    <span className="value">{scanConfig.name}</span>
                  </div>
                )}
                {scanConfig.goal && (
                  <div className="review-item">
                    <span className="label">Goal:</span>
                    <span className="value">{scanConfig.goal}</span>
                  </div>
                )}
              </div>

              <div className="review-section">
                <h4>Configuration</h4>
                <div className="review-item">
                  <span className="label">Scan Type:</span>
                  <span className="value">
                    {SCAN_TYPES.find(t => t.id === scanConfig.scan_type)?.name}
                  </span>
                </div>
                <div className="review-item">
                  <span className="label">Safety Level:</span>
                  <span className={`value safety-${scanConfig.safety_level}`}>
                    {SAFETY_LEVELS.find(l => l.id === scanConfig.safety_level)?.name}
                  </span>
                </div>
              </div>

              <div className="review-section">
                <h4>Tools ({scanConfig.selected_tools.length})</h4>
                <div className="selected-tools-list">
                  {scanConfig.selected_tools.map(tool => (
                    <span key={tool} className="tool-tag">{tool}</span>
                  ))}
                </div>
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

      <div className="stepper">
        {STEPS.map((label, index) => (
          <div 
            key={label} 
            className={`step ${index === activeStep ? 'active' : ''} ${index < activeStep ? 'completed' : ''}`}
          >
            <div className="step-number">
              {index < activeStep ? <Check size={16} /> : index + 1}
            </div>
            <div className="step-label">{label}</div>
          </div>
        ))}
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      <div className="step-content-wrapper">
        {renderStepContent()}
      </div>

      <div className="step-actions-bar">
        <button 
          onClick={handleBack} 
          className="btn-secondary"
          disabled={activeStep === 0}
        >
          <ArrowLeft size={18} />
          Back
        </button>
        
        {activeStep < STEPS.length - 1 ? (
          <button onClick={handleNext} className="btn-primary">
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
                Starting Scan...
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
