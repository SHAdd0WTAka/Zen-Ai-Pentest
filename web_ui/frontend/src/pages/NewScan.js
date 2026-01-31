import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Paper,
    Stepper,
    Step,
    StepLabel,
    Alert,
    CircularProgress
} from '@mui/material';
import axios from 'axios';

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
        scope: {}
    });

    const handleNext = () => {
        setActiveStep((prevStep) => prevStep + 1);
    };

    const handleBack = () => {
        setActiveStep((prevStep) => prevStep - 1);
    };

    const handleChange = (field) => (event) => {
        setScanConfig({ ...scanConfig, [field]: event.target.value });
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.post('/api/scans', scanConfig);
            navigate(`/scans/${response.data.scan_id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to start scan');
            setLoading(false);
        }
    };

    const renderStepContent = (step) => {
        switch (step) {
            case 0:
                return (
                    <Box sx={{ mt: 2 }}>
                        <TextField
                            fullWidth
                            label="Target"
                            value={scanConfig.target}
                            onChange={handleChange('target')}
                            placeholder="e.g., example.com or 192.168.1.1"
                            margin="normal"
                            required
                        />
                        <TextField
                            fullWidth
                            label="Goal (Optional)"
                            value={scanConfig.goal}
                            onChange={handleChange('goal')}
                            placeholder="e.g., Find all vulnerabilities"
                            margin="normal"
                            multiline
                            rows={2}
                        />
                    </Box>
                );
            case 1:
                return (
                    <Box sx={{ mt: 2 }}>
                        <FormControl fullWidth margin="normal">
                            <InputLabel>Scan Type</InputLabel>
                            <Select
                                value={scanConfig.scan_type}
                                onChange={handleChange('scan_type')}
                                label="Scan Type"
                            >
                                <MenuItem value="quick">Quick (Port scan only)</MenuItem>
                                <MenuItem value="standard">Standard (Common vulnerabilities)</MenuItem>
                                <MenuItem value="comprehensive">Comprehensive (Full assessment)</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth margin="normal">
                            <InputLabel>Safety Level</InputLabel>
                            <Select
                                value={scanConfig.safety_level}
                                onChange={handleChange('safety_level')}
                                label="Safety Level"
                            >
                                <MenuItem value="read_only">Read Only (Passive recon)</MenuItem>
                                <MenuItem value="non_destructive">Non-Destructive (Safe tests)</MenuItem>
                                <MenuItem value="destructive">Destructive (May modify data)</MenuItem>
                                <MenuItem value="exploit">Full Exploitation</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                );
            case 2:
                return (
                    <Box sx={{ mt: 2 }}>
                        <Paper sx={{ p: 2 }}>
                            <Typography variant="h6">Scan Configuration</Typography>
                            <Typography><strong>Target:</strong> {scanConfig.target}</Typography>
                            <Typography><strong>Goal:</strong> {scanConfig.goal || 'Default comprehensive assessment'}</Typography>
                            <Typography><strong>Scan Type:</strong> {scanConfig.scan_type}</Typography>
                            <Typography><strong>Safety Level:</strong> {scanConfig.safety_level}</Typography>
                        </Paper>
                    </Box>
                );
            default:
                return null;
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                New Scan
            </Typography>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
                {steps.map((label) => (
                    <Step key={label}>
                        <StepLabel>{label}</StepLabel>
                    </Step>
                ))}
            </Stepper>

            <Paper sx={{ p: 3 }}>
                {renderStepContent(activeStep)}

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                    {activeStep > 0 && (
                        <Button onClick={handleBack} sx={{ mr: 1 }}>
                            Back
                        </Button>
                    )}
                    {activeStep < steps.length - 1 ? (
                        <Button
                            variant="contained"
                            onClick={handleNext}
                            disabled={!scanConfig.target}
                        >
                            Next
                        </Button>
                    ) : (
                        <Button
                            variant="contained"
                            onClick={handleSubmit}
                            disabled={loading}
                            startIcon={loading && <CircularProgress size={20} />}
                        >
                            Start Scan
                        </Button>
                    )}
                </Box>
            </Paper>
        </Box>
    );
}

export default NewScan;
