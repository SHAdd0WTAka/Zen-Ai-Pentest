import React from 'react';
import {
    Box,
    Typography,
    Paper,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Button,
    Divider,
    Alert
} from '@mui/material';

function Settings() {
    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Settings
            </Typography>

            <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                    API Configuration
                </Typography>
                
                <TextField
                    fullWidth
                    label="OpenRouter API Key"
                    type="password"
                    margin="normal"
                    placeholder="sk-or-..."
                />
                
                <TextField
                    fullWidth
                    label="OpenAI API Key"
                    type="password"
                    margin="normal"
                    placeholder="sk-..."
                />

                <Divider sx={{ my: 3 }} />

                <Typography variant="h6" gutterBottom>
                    Safety Settings
                </Typography>
                
                <FormControl fullWidth margin="normal">
                    <InputLabel>Default Safety Level</InputLabel>
                    <Select label="Default Safety Level" defaultValue="non_destructive">
                        <MenuItem value="read_only">Read Only</MenuItem>
                        <MenuItem value="non_destructive">Non-Destructive</MenuItem>
                        <MenuItem value="destructive">Destructive</MenuItem>
                        <MenuItem value="exploit">Full Exploitation</MenuItem>
                    </Select>
                </FormControl>

                <Alert severity="info" sx={{ mt: 2 }}>
                    Higher safety levels restrict what tools can be executed automatically.
                </Alert>

                <Divider sx={{ my: 3 }} />

                <Typography variant="h6" gutterBottom>
                    Notification Settings
                </Typography>
                
                <TextField
                    fullWidth
                    label="Slack Webhook URL"
                    margin="normal"
                    placeholder="https://hooks.slack.com/services/..."
                />
                
                <TextField
                    fullWidth
                    label="Email for Alerts"
                    margin="normal"
                    placeholder="security@example.com"
                />

                <Box sx={{ mt: 3 }}>
                    <Button variant="contained" color="primary">
                        Save Settings
                    </Button>
                </Box>
            </Paper>
        </Box>
    );
}

export default Settings;
