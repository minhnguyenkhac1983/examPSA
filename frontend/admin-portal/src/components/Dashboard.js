import React, { useState, useEffect, useMemo } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  Badge
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  LocationOn,
  Speed,
  People,
  AttachMoney,
  Refresh,
  Warning,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { format } from 'date-fns';

const Dashboard = ({ realTimeData }) => {
  const [dashboardData, setDashboardData] = useState({
    metrics: {
      totalRequests: 0,
      activeZones: 0,
      averageSurge: 1.0,
      completionRate: 0,
      revenue: 0,
      activeDrivers: 0
    },
    trends: [],
    zonePerformance: [],
    alerts: []
  });
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Mock data for demonstration
  const mockData = useMemo(() => ({
    metrics: {
      totalRequests: realTimeData?.totalRequests || 1247,
      activeZones: realTimeData?.activeZones || 23,
      averageSurge: realTimeData?.averageSurge || 1.4,
      completionRate: 87.3,
      revenue: 45678.90,
      activeDrivers: 156
    },
    trends: [
      { time: '00:00', requests: 45, surge: 1.0 },
      { time: '01:00', requests: 32, surge: 1.0 },
      { time: '02:00', requests: 28, surge: 1.0 },
      { time: '03:00', requests: 35, surge: 1.0 },
      { time: '04:00', requests: 42, surge: 1.0 },
      { time: '05:00', requests: 58, surge: 1.1 },
      { time: '06:00', requests: 89, surge: 1.2 },
      { time: '07:00', requests: 156, surge: 1.5 },
      { time: '08:00', requests: 234, surge: 1.8 },
      { time: '09:00', requests: 198, surge: 1.6 },
      { time: '10:00', requests: 145, surge: 1.3 },
      { time: '11:00', requests: 167, surge: 1.4 },
      { time: '12:00', requests: 189, surge: 1.5 },
      { time: '13:00', requests: 178, surge: 1.4 },
      { time: '14:00', requests: 156, surge: 1.3 },
      { time: '15:00', requests: 167, surge: 1.4 },
      { time: '16:00', requests: 189, surge: 1.5 },
      { time: '17:00', requests: 234, surge: 1.8 },
      { time: '18:00', requests: 267, surge: 2.1 },
      { time: '19:00', requests: 245, surge: 1.9 },
      { time: '20:00', requests: 198, surge: 1.6 },
      { time: '21:00', requests: 167, surge: 1.4 },
      { time: '22:00', requests: 134, surge: 1.2 },
      { time: '23:00', requests: 89, surge: 1.1 }
    ],
    zonePerformance: [
      { zone: 'Downtown', requests: 234, surge: 1.8, completion: 89 },
      { zone: 'Airport', requests: 189, surge: 1.5, completion: 92 },
      { zone: 'University', requests: 167, surge: 1.4, completion: 85 },
      { zone: 'Mall', requests: 145, surge: 1.3, completion: 88 },
      { zone: 'Stadium', requests: 98, surge: 1.2, completion: 91 }
    ],
    alerts: [
      { id: 1, type: 'warning', message: 'High surge detected in Downtown zone', time: '2 min ago' },
      { id: 2, type: 'info', message: 'New driver joined in Airport zone', time: '5 min ago' },
      { id: 3, type: 'success', message: 'System performance optimal', time: '10 min ago' }
    ]
  }), [realTimeData]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setDashboardData(mockData);
        setLastUpdated(new Date());
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [mockData]);

  const getSurgeColor = (surge) => {
    if (surge >= 2.0) return '#f44336';
    if (surge >= 1.5) return '#ff9800';
    if (surge >= 1.2) return '#ffc107';
    return '#4caf50';
  };

  const getSurgeLevel = (surge) => {
    if (surge >= 2.0) return 'Critical';
    if (surge >= 1.5) return 'High';
    if (surge >= 1.2) return 'Medium';
    return 'Low';
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'warning': return <Warning color="warning" />;
      case 'error': return <Error color="error" />;
      case 'success': return <CheckCircle color="success" />;
      default: return <Info color="info" />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress sx={{ width: '100%' }} />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="body2" color="text.secondary">
            Last updated: {format(lastUpdated, 'HH:mm:ss')}
          </Typography>
          <IconButton onClick={() => window.location.reload()}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Requests
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.metrics.totalRequests.toLocaleString()}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <Speed />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Zones
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.metrics.activeZones}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  <LocationOn />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Avg Surge
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.metrics.averageSurge.toFixed(1)}x
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: getSurgeColor(dashboardData.metrics.averageSurge) }}>
                  <TrendingUp />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Completion Rate
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.metrics.completionRate}%
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircle />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Revenue
                  </Typography>
                  <Typography variant="h4">
                    ${dashboardData.metrics.revenue.toLocaleString()}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <AttachMoney />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Drivers
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.metrics.activeDrivers}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <People />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Analytics */}
      <Grid container spacing={3}>
        {/* Request Trends */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Request Trends & Surge Levels
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dashboardData.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <RechartsTooltip />
                  <Line 
                    yAxisId="left" 
                    type="monotone" 
                    dataKey="requests" 
                    stroke="#1976d2" 
                    strokeWidth={2}
                    name="Requests"
                  />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="surge" 
                    stroke="#dc004e" 
                    strokeWidth={2}
                    name="Surge Multiplier"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Zone Performance */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Zone Performance
              </Typography>
              <List>
                {dashboardData.zonePerformance.map((zone, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemIcon>
                        <LocationOn color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={zone.zone}
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              {zone.requests} requests • {zone.completion}% completion
                            </Typography>
                            <Chip
                              label={`${zone.surge.toFixed(1)}x ${getSurgeLevel(zone.surge)}`}
                              size="small"
                              sx={{ 
                                backgroundColor: getSurgeColor(zone.surge),
                                color: 'white',
                                mt: 0.5
                              }}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < dashboardData.zonePerformance.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* System Alerts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Alerts
              </Typography>
              <List>
                {dashboardData.alerts.map((alert) => (
                  <React.Fragment key={alert.id}>
                    <ListItem>
                      <ListItemIcon>
                        {getAlertIcon(alert.type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={alert.message}
                        secondary={alert.time}
                      />
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Surge Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Surge Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Low (1.0-1.2x)', value: 45, color: '#4caf50' },
                      { name: 'Medium (1.2-1.5x)', value: 30, color: '#ffc107' },
                      { name: 'High (1.5-2.0x)', value: 20, color: '#ff9800' },
                      { name: 'Critical (2.0x+)', value: 5, color: '#f44336' }
                    ]}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {[
                      { name: 'Low (1.0-1.2x)', value: 45, color: '#4caf50' },
                      { name: 'Medium (1.2-1.5x)', value: 30, color: '#ffc107' },
                      { name: 'High (1.5-2.0x)', value: 20, color: '#ff9800' },
                      { name: 'Critical (2.0x+)', value: 5, color: '#f44336' }
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
