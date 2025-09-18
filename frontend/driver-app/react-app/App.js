import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  SafeAreaView,
  StatusBar,
  Switch,
} from 'react-native';

const DriverApp = () => {
  const [isOnline, setIsOnline] = useState(false);
  const [currentLocation, setCurrentLocation] = useState({
    latitude: 37.7749,
    longitude: -122.4194
  });
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(false);

  const updateDriverLocation = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/drivers/location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver_id: 'driver_001',
          location: currentLocation,
          status: isOnline ? 'available' : 'offline',
          timestamp: new Date().toISOString()
        }),
      });

      if (response.ok) {
        Alert.alert('Success', 'Location updated successfully');
      } else {
        Alert.alert('Error', 'Failed to update location');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error: ' + error.message);
    }
  };

  const getHeatmapData = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/v1/pricing/heatmap', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setHeatmapData(data);
      } else {
        Alert.alert('Error', 'Failed to get heatmap data');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOnline) {
      updateDriverLocation();
      getHeatmapData();
    }
  }, [isOnline]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Text style={styles.title}>🚕 Driver Portal</Text>
          <Text style={styles.subtitle}>Equilibrium Dynamic Pricing</Text>
        </View>

        <View style={styles.statusCard}>
          <View style={styles.statusHeader}>
            <Text style={styles.statusTitle}>Driver Status</Text>
            <Switch
              value={isOnline}
              onValueChange={setIsOnline}
              trackColor={{ false: '#e74c3c', true: '#2ecc71' }}
              thumbColor={isOnline ? '#ffffff' : '#ffffff'}
            />
          </View>
          <Text style={[styles.statusText, { color: isOnline ? '#2ecc71' : '#e74c3c' }]}>
            {isOnline ? '🟢 Online - Available for rides' : '🔴 Offline'}
          </Text>
        </View>

        <View style={styles.locationCard}>
          <Text style={styles.cardTitle}>📍 Current Location</Text>
          <Text style={styles.locationText}>
            Lat: {currentLocation.latitude.toFixed(4)}
          </Text>
          <Text style={styles.locationText}>
            Lng: {currentLocation.longitude.toFixed(4)}
          </Text>
          <TouchableOpacity style={styles.button} onPress={updateDriverLocation}>
            <Text style={styles.buttonText}>Update Location</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.heatmapCard}>
          <View style={styles.heatmapHeader}>
            <Text style={styles.cardTitle}>🔥 Demand Heatmap</Text>
            <TouchableOpacity 
              style={styles.refreshButton} 
              onPress={getHeatmapData}
              disabled={loading}
            >
              <Text style={styles.refreshButtonText}>
                {loading ? 'Loading...' : 'Refresh'}
              </Text>
            </TouchableOpacity>
          </View>
          
          {heatmapData && heatmapData.zones ? (
            <View style={styles.heatmapData}>
              {heatmapData.zones.slice(0, 5).map((zone, index) => (
                <View key={index} style={styles.zoneItem}>
                  <Text style={styles.zoneName}>{zone.zone_name}</Text>
                  <View style={styles.zoneMetrics}>
                    <Text style={styles.metric}>
                      Surge: {zone.surge_multiplier?.toFixed(2) || 'N/A'}x
                    </Text>
                    <Text style={styles.metric}>
                      Demand: {zone.demand_level || 'N/A'}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.noData}>No heatmap data available</Text>
          )}
        </View>

        <View style={styles.features}>
          <Text style={styles.featuresTitle}>🚀 Driver Features</Text>
          <Text style={styles.feature}>• Real-time demand visualization</Text>
          <Text style={styles.feature}>• Dynamic surge pricing insights</Text>
          <Text style={styles.feature}>• Location-based recommendations</Text>
          <Text style={styles.feature}>• Earnings optimization</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContainer: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
    paddingTop: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
  },
  statusCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
  },
  locationCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 15,
  },
  locationText: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 5,
  },
  button: {
    backgroundColor: '#3498db',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 15,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  heatmapCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  heatmapHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  refreshButton: {
    backgroundColor: '#e74c3c',
    padding: 8,
    borderRadius: 6,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  heatmapData: {
    marginTop: 10,
  },
  zoneItem: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  zoneName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 5,
  },
  zoneMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    fontSize: 12,
    color: '#7f8c8d',
  },
  noData: {
    fontSize: 14,
    color: '#7f8c8d',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  features: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 15,
  },
  feature: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 8,
  },
});

export default DriverApp;
