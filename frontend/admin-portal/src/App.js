import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Container, Snackbar, Alert, CircularProgress } from '@mui/material';
import './App.css';

// Components
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import ZoneManagement from './components/ZoneManagement';
import PricingEngine from './components/PricingEngine';
import SystemHealth from './components/SystemHealth';
import Navigation from './components/Navigation';
import Login from './components/Login';
import Settings from './components/Settings';

// Services
import { authService } from './services/authService';
import { apiService } from './services/apiService';
import { websocketService } from './services/websocketService';

// Context
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeContext } from './contexts/ThemeContext';
import { NotificationProvider, useNotification } from './contexts/NotificationContext';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Enhanced theme configuration
const createAppTheme = (isDarkMode) => createTheme({
  palette: {
    mode: isDarkMode ? 'dark' : 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: isDarkMode ? '#121212' : '#f5f5f5',
      paper: isDarkMode ? '#1e1e1e' : '#ffffff',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
    },
    info: {
      main: '#2196f3',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

// Main App Component
function AppContent() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { showNotification } = useNotification();
  const [isDarkMode, setIsDarkMode] = useState(
    localStorage.getItem('theme') === 'dark' || 
    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
  );
  const [systemHealth, setSystemHealth] = useState(null);
  const [realTimeData, setRealTimeData] = useState({
    activeZones: 0,
    totalRequests: 0,
    averageSurge: 1.0,
    systemStatus: 'healthy'
  });

  const theme = useMemo(() => createAppTheme(isDarkMode), [isDarkMode]);

  // Initialize services
  useEffect(() => {
    const initializeServices = async () => {
      try {
        await apiService.initialize(API_BASE_URL);
        await websocketService.connect(API_BASE_URL.replace('http', 'ws'));
        
        websocketService.onMessage((data) => {
          if (data.type === 'system_health') {
            setSystemHealth(data.payload);
          } else if (data.type === 'real_time_update') {
            setRealTimeData(prev => ({
              ...prev,
              ...data.payload
            }));
          }
        });
        
        showNotification('Services initialized successfully', 'success');
      } catch (error) {
        console.error('Failed to initialize services:', error);
        showNotification('Failed to initialize services', 'error');
      }
    };

    if (isAuthenticated) {
      initializeServices();
    }

    return () => {
      websocketService.disconnect();
    };
  }, [isAuthenticated, showNotification]);

  // Theme toggle handler
  const toggleTheme = useCallback(() => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  }, [isDarkMode]);

  // System health monitoring
  useEffect(() => {
    const checkSystemHealth = async () => {
      try {
        const health = await apiService.getSystemHealth();
        setSystemHealth(health);
      } catch (error) {
        console.error('Failed to fetch system health:', error);
      }
    };

    if (isAuthenticated) {
      checkSystemHealth();
      const interval = setInterval(checkSystemHealth, 30000); // Every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Loading state
  if (authLoading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Login page
  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Login />
      </ThemeProvider>
    );
  }

  // Main application
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Navigation 
            user={user}
            systemHealth={systemHealth}
            realTimeData={realTimeData}
            isDarkMode={isDarkMode}
            onToggleTheme={toggleTheme}
          />
          
          <Box 
            component="main" 
            sx={{ 
              flexGrow: 1, 
              p: 3,
              backgroundColor: 'background.default',
              minHeight: '100vh'
            }}
          >
            <Container maxWidth="xl">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard realTimeData={realTimeData} />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/zones" element={<ZoneManagement />} />
                <Route path="/pricing" element={<PricingEngine />} />
                <Route path="/health" element={<SystemHealth systemHealth={systemHealth} />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

// Root App Component with Providers
function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <AppContent />
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;