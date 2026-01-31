import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Paper,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
    Chip,
    Divider,
    Grid
} from '@mui/material';
import axios from 'axios';

function ScanDetail() {
    const { scanId } = useParams();
    const [scan, setScan] = useState(null);
    const [findings, setFindings] = useState([]);
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        fetchScanDetails();
        const interval = setInterval(fetchScanDetails, 2000);
        return () => clearInterval(interval);
    }, [scanId]);

    const fetchScanDetails = async () => {
        try {
            const [scanRes, findingsRes, logsRes] = await Promise.all([
                axios.get(`/api/scans/${scanId}`),
                axios.get(`/api/scans/${scanId}/findings`),
                axios.get(`/api/scans/${scanId}/logs`)
            ]);
            setScan(scanRes.data);
            setFindings(findingsRes.data);
            setLogs(logsRes.data);
        } catch (error) {
            console.error('Error fetching scan details:', error);
        }
    };

    const getSeverityColor = (severity) => {
        switch (severity?.toUpperCase()) {
            case 'CRITICAL':
                return 'error';
            case 'HIGH':
                return 'warning';
            case 'MEDIUM':
                return 'info';
            case 'LOW':
                return 'success';
            default:
                return 'default';
        }
    };

    if (!scan) {
        return <LinearProgress />;
    }

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Scan Details
            </Typography>

            {/* Overview */}
            <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6">Overview</Typography>
                <Grid container spacing={2}>
                    <Grid item xs={6}>
                        <Typography><strong>Target:</strong> {scan.request?.target}</Typography>
                        <Typography><strong>Status:</strong> 
                            <Chip 
                                label={scan.status} 
                                color={scan.status === 'completed' ? 'success' : 'primary'}
                                size="small"
                                sx={{ ml: 1 }}
                            />
                        </Typography>
                    </Grid>
                    <Grid item xs={6}>
                        <Typography><strong>Progress:</strong> {scan.progress}%</Typography>
                        <LinearProgress variant="determinate" value={scan.progress} sx={{ mt: 1 }} />
                    </Grid>
                </Grid>
            </Paper>

            {/* Findings */}
            <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Findings ({findings.length})
                </Typography>
                <List>
                    {findings.map((finding, index) => (
                        <React.Fragment key={index}>
                            <ListItem>
                                <ListItemText
                                    primary={
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Typography variant="subtitle1">
                                                {finding.title || finding.type}
                                            </Typography>
                                            <Chip
                                                label={finding.severity}
                                                color={getSeverityColor(finding.severity)}
                                                size="small"
                                            />
                                        </Box>
                                    }
                                    secondary={
                                        <>
                                            <Typography variant="body2" color="textSecondary">
                                                {finding.description}
                                            </Typography>
                                            {finding.risk_score && (
                                                <Typography variant="body2" sx={{ mt: 1 }}>
                                                    Risk Score: {finding.risk_score.risk_score}/10
                                                </Typography>
                                            )}
                                        </>
                                    }
                                />
                            </ListItem>
                            <Divider />
                        </React.Fragment>
                    ))}
                </List>
            </Paper>

            {/* Logs */}
            <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Execution Logs
                </Typography>
                <Box sx={{ maxHeight: 300, overflow: 'auto', bgcolor: 'background.paper', p: 1 }}>
                    {logs.map((log, index) => (
                        <Typography key={index} variant="body2" sx={{ fontFamily: 'monospace' }}>
                            [{new Date(log.timestamp).toLocaleTimeString()}] {log.message}
                        </Typography>
                    ))}
                </Box>
            </Paper>
        </Box>
    );
}

export default ScanDetail;
