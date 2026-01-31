import React, { useEffect, useState } from 'react';
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
    TextField,
    MenuItem,
    FormControl,
    InputLabel,
    Select
} from '@mui/material';
import axios from 'axios';

function Findings() {
    const [findings, setFindings] = useState([]);
    const [filteredFindings, setFilteredFindings] = useState([]);
    const [severityFilter, setSeverityFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchFindings();
    }, []);

    useEffect(() => {
        filterFindings();
    }, [findings, severityFilter, searchTerm]);

    const fetchFindings = async () => {
        try {
            // Get all scans and extract findings
            const scansRes = await axios.get('/api/scans');
            const allFindings = [];
            
            for (const scan of scansRes.data) {
                if (scan.findings_count > 0) {
                    const findingsRes = await axios.get(`/api/scans/${scan.scan_id}/findings`);
                    allFindings.push(...findingsRes.data.map(f => ({
                        ...f,
                        scan_id: scan.scan_id,
                        target: scan.target
                    })));
                }
            }
            
            setFindings(allFindings);
        } catch (error) {
            console.error('Error fetching findings:', error);
        }
    };

    const filterFindings = () => {
        let filtered = findings;

        if (severityFilter !== 'all') {
            filtered = filtered.filter(f => 
                f.severity?.toUpperCase() === severityFilter.toUpperCase()
            );
        }

        if (searchTerm) {
            filtered = filtered.filter(f =>
                f.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                f.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                f.target?.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        setFilteredFindings(filtered);
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

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Findings
            </Typography>

            {/* Filters */}
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                    label="Search"
                    variant="outlined"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    sx={{ flexGrow: 1 }}
                />
                <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel>Severity</InputLabel>
                    <Select
                        value={severityFilter}
                        onChange={(e) => setSeverityFilter(e.target.value)}
                        label="Severity"
                    >
                        <MenuItem value="all">All</MenuItem>
                        <MenuItem value="CRITICAL">Critical</MenuItem>
                        <MenuItem value="HIGH">High</MenuItem>
                        <MenuItem value="MEDIUM">Medium</MenuItem>
                        <MenuItem value="LOW">Low</MenuItem>
                    </Select>
                </FormControl>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Target</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Severity</TableCell>
                            <TableCell>Risk Score</TableCell>
                            <TableCell>Description</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredFindings.map((finding, index) => (
                            <TableRow key={index}>
                                <TableCell>{finding.target}</TableCell>
                                <TableCell>{finding.type}</TableCell>
                                <TableCell>
                                    <Chip
                                        label={finding.severity}
                                        color={getSeverityColor(finding.severity)}
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell>
                                    {finding.risk_score ? (
                                        <Chip
                                            label={`${finding.risk_score.risk_score}/10`}
                                            color={getSeverityColor(finding.severity)}
                                            size="small"
                                        />
                                    ) : '-'}
                                </TableCell>
                                <TableCell>{finding.description}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}

export default Findings;
