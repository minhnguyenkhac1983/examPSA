import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ScrollView,
  SafeAreaView,
  StatusBar,
} from 'react-native';

const MobileApp = () => {
  const [pickupLocation, setPickupLocation] = useState('');
  const [dropoffLocation, setDropoffLocation] = useState('');
  const [priceEstimate, setPriceEstimate] = useState(null);
  const [loading, setLoading] = useState(false);

  const getPriceEstimate = async () => {
    if (!pickupLocation || !dropoffLocation) {
      Alert.alert('Error', 'Please enter both pickup and dropoff locations');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/v1/pricing/estimate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rider_id: 'mobile_user_001',
          pickup_location: {
            latitude: 37.7749,
            longitude: -122.4194
          },
          dropoff_location: {
            latitude: 37.7849,
            longitude: -122.4094
          },
          vehicle_type: 'standard'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setPriceEstimate(data);
      } else {
        Alert.alert('Error', 'Failed to get price estimate');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Text style={styles.title}>🚗 Equilibrium</Text>
          <Text style={styles.subtitle}>Dynamic Pricing Platform</Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.label}>Pickup Location</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter pickup address"
            value={pickupLocation}
            onChangeText={setPickupLocation}
          />

          <Text style={styles.label}>Dropoff Location</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter dropoff address"
            value={dropoffLocation}
            onChangeText={setDropoffLocation}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={getPriceEstimate}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? 'Getting Estimate...' : 'Get Price Estimate'}
            </Text>
          </TouchableOpacity>
        </View>

        {priceEstimate && (
          <View style={styles.result}>
            <Text style={styles.resultTitle}>💰 Price Estimate</Text>
            <Text style={styles.price}>${priceEstimate.fare_estimate?.toFixed(2) || 'N/A'}</Text>
            <Text style={styles.surge}>
              Surge Multiplier: {priceEstimate.surge_multiplier?.toFixed(2) || 'N/A'}x
            </Text>
            <Text style={styles.confidence}>
              Confidence: {priceEstimate.confidence_score?.toFixed(1) || 'N/A'}%
            </Text>
            <Text style={styles.validUntil}>
              Valid Until: {priceEstimate.valid_until || 'N/A'}
            </Text>
          </View>
        )}

        <View style={styles.features}>
          <Text style={styles.featuresTitle}>🌟 Features</Text>
          <Text style={styles.feature}>• Real-time dynamic pricing</Text>
          <Text style={styles.feature}>• Transparent surge pricing</Text>
          <Text style={styles.feature}>• Multi-zone support</Text>
          <Text style={styles.feature}>• Instant price estimates</Text>
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
  form: {
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
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 8,
    marginTop: 15,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f8f9fa',
  },
  button: {
    backgroundColor: '#3498db',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonDisabled: {
    backgroundColor: '#bdc3c7',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  result: {
    backgroundColor: '#2ecc71',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
  },
  price: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  surge: {
    fontSize: 14,
    color: 'white',
    marginBottom: 3,
  },
  confidence: {
    fontSize: 14,
    color: 'white',
    marginBottom: 3,
  },
  validUntil: {
    fontSize: 14,
    color: 'white',
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

export default MobileApp;
