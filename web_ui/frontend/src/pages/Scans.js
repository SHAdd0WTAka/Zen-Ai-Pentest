import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    IconButton,
    Button,
    LinearProgress
} from '@mui/material';
import {
    Visibility as ViewIcon,
    Delete as DeleteIcon,
    PlayArrow as PlayIcon
} from '@mui/icons-material';
import axios from 'axios';

function Scans() {
    const navigate = useNavigate();
    const [scans, setScans] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchScans();
        const interval = setInterval(fetchScans, 3000);
        return () => clearInterval(interval);
    }, []);

    const fetchScans = async () => {
        try {
            const response = await axios.get('/api/scans');
            setScans(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching scans:', error);
        }
    };

    const handleDelete = async (scanId) => {
        try {
            await axios.delete(`/api/scans/${scanId}`);
            fetchScans();
        } catch (error) {
            console.error('Error deleting scan:', error);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return 'success';
            case 'running':
                return 'primary';
            case 'failed':
                return 'error';
            case 'pending':
                return 'warning';
            default:
                return 'default';
        }
    };

    if (loading) {
        return <LinearProgress />;
    }

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h4">
                    Scans
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={() => navigate('/scans/new')}
                >
                    New Scan
                </Button>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Target</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Progress</TableCell>
                            <TableCell>Findings</TableCell>
                            <TableCell>Start Time</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {scans.map((scan) => (
                            <TableRow key={scan.scan_id}>
                                <TableCell>{scan.target}</TableCell>
                                <TableCell>
                                    <Chip
                                        label={scan.status}
                                        color={getStatusColor(scan.status)}
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        <Box sx={{ width: '100%', mr: 1 }}>
                                            <LinearProgress
                                                variant="determinate"
                                                value={scan.progress}
                                            />
                                        </Box>
                                        <Box sx={{ minWidth: 35 }}>
                                            <Typography variant="body2" color="textSecondary">
                                                {`${Math.round(scan.progress)}%`}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </TableCell>
                                <TableCell>{scan.findings_count}</TableCell>
                                <TableCell>
                                    {scan.start_time ? new Date(scan.start_time).toLocaleString() : '-'}
                                </TableCell>
                                <TableCell>
                                    <IconButton
                                        onClick={() => navigate(`/scans/${scan.scan_id}`)}
                                    >
                                        <ViewIcon />
                                    </IconButton>
                                    {scan.status === 'running' && (
                                        <IconButton
                                            onClick={() => handleDelete(scan.scan_id)}
                                            color="error"
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}

export default Scans;
