import React, { useEffect, useState } from 'react';
import {
    Grid,
    Paper,
    Typography,
    Box,
    Card,
    CardContent,
    LinearProgress
} from '@mui/material';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts';
import axios from 'axios';

const COLORS = ['#ff1744', '#ff9100', '#ffc400', '#00e676', '#00b0ff'];

function Dashboard() {
    const [stats, setStats] = useState(null);
    const [recentScans, setRecentScans] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
        const interval = setInterval(fetchDashboardData, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchDashboardData = async () => {
        try {
            const [statsRes, scansRes] = await Promise.all([
                axios.get('/api/dashboard/stats'),
                axios.get('/api/scans')
            ]);
            setStats(statsRes.data);
            setRecentScans(scansRes.data.slice(0, 5));
            setLoading(false);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    };

    if (loading) {
        return <LinearProgress />;
    }

    const severityData = [
        { name: 'Critical', value: stats?.critical_findings || 0 },
        { name: 'High', value: stats?.high_findings || 0 },
        { name: 'Total', value: stats?.total_findings || 0 },
    ];

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Dashboard
            </Typography>

            {/* Stats Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Total Scans
                            </Typography>
                            <Typography variant="h3">
                                {stats?.total_scans || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Active Scans
                            </Typography>
                            <Typography variant="h3" color="primary">
                                {stats?.active_scans || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Total Findings
                            </Typography>
                            <Typography variant="h3" color="error">
                                {stats?.total_findings || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Critical
                            </Typography>
                            <Typography variant="h3" sx={{ color: '#ff1744' }}>
                                {stats?.critical_findings || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Findings by Severity
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={severityData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                    label
                                >
                                    {severityData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Recent Scans
                        </Typography>
                        {recentScans.map((scan) => (
                            <Box key={scan.scan_id} sx={{ mb: 2, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                                <Typography variant="subtitle1">
                                    {scan.target}
                                </Typography>
                                <Typography variant="body2" color="textSecondary">
                                    Status: {scan.status} | Findings: {scan.findings_count}
                                </Typography>
                                <LinearProgress 
                                    variant="determinate" 
                                    value={scan.progress} 
                                    sx={{ mt: 1 }}
                                />
                            </Box>
                        ))}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
}

export default Dashboard;
