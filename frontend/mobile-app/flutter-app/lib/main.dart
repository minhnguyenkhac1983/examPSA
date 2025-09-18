import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const MobileFlutterApp());
}

class MobileFlutterApp extends StatelessWidget {
  const MobileFlutterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Equilibrium Mobile (Flutter)',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const MobileHomeScreen(),
    );
  }
}

class MobileHomeScreen extends StatefulWidget {
  const MobileHomeScreen({super.key});

  @override
  State<MobileHomeScreen> createState() => _MobileHomeScreenState();
}

class _MobileHomeScreenState extends State<MobileHomeScreen> {
  final TextEditingController _pickupController = TextEditingController();
  final TextEditingController _dropoffController = TextEditingController();
  String _priceEstimate = '';
  bool _isLoading = false;
  WebSocketChannel? _pricingChannel;
  StreamSubscription? _pricingSubscription;
  String _livePricingInfo = '';
  
  // Authentication state
  bool _isLoggedIn = false;
  String _userEmail = '';
  String _userRole = '';
  String _accessToken = '';

  Future<void> _getPriceEstimate() async {
    if (_pickupController.text.isEmpty || _dropoffController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter both pickup and dropoff locations')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Real API call to pricing service
      final response = await http.post(
        Uri.parse('http://localhost:8001/api/v1/pricing/estimate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'pickup_location': {
            'latitude': 37.7749,
            'longitude': -122.4194
          },
          'dropoff_location': {
            'latitude': 37.7849,
            'longitude': -122.4094
          },
          'vehicle_type': 'standard'
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _priceEstimate = '\$${data['final_fare']} (${data['surge_multiplier']}x surge)';
          _isLoading = false;
        });
      } else {
        throw Exception('Failed to get price estimate');
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
             appBar: AppBar(
               title: const Text('📱 Equilibrium Mobile'),
               backgroundColor: Colors.blue,
               foregroundColor: Colors.white,
               actions: [
                 if (_isLoggedIn)
                   PopupMenuButton<String>(
                     onSelected: (value) {
                       if (value == 'logout') {
                         _logout();
                       }
                     },
                     itemBuilder: (context) => [
                       PopupMenuItem(
                         value: 'logout',
                         child: const Text('Logout'),
                       ),
                     ],
                     child: Padding(
                       padding: const EdgeInsets.all(8.0),
                       child: Column(
                         mainAxisSize: MainAxisSize.min,
                         children: [
                           const Icon(Icons.person, color: Colors.white),
                           Text(
                             _userRole.toUpperCase(),
                             style: const TextStyle(fontSize: 10, color: Colors.white),
                           ),
                         ],
                       ),
                     ),
                   )
                 else
                   IconButton(
                     icon: const Icon(Icons.login),
                     onPressed: _login,
                     tooltip: 'Login',
                   ),
               ],
             ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
                   Row(
                     mainAxisAlignment: MainAxisAlignment.center,
                     children: [
                       const Text(
                         'Mobile App (Flutter)',
                         style: TextStyle(
                           fontSize: 24,
                           fontWeight: FontWeight.bold,
                           color: Colors.blue,
                         ),
                       ),
                       if (_isLoggedIn) ...[
                         const SizedBox(width: 8),
                         Container(
                           padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                           decoration: BoxDecoration(
                             color: Colors.green,
                             borderRadius: BorderRadius.circular(12),
                           ),
                           child: Text(
                             'LOGGED IN',
                             style: const TextStyle(
                               color: Colors.white,
                               fontSize: 10,
                               fontWeight: FontWeight.bold,
                             ),
                           ),
                         ),
                       ],
                     ],
                   ),
            const SizedBox(height: 20),
            const Text(
              'Get instant price estimates for your ride',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 30),
            TextField(
              controller: _pickupController,
              decoration: const InputDecoration(
                labelText: 'Pickup Location',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.location_on),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _dropoffController,
              decoration: const InputDecoration(
                labelText: 'Dropoff Location',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.location_on),
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isLoading ? null : _getPriceEstimate,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _isLoading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text(
                      'Get Price Estimate',
                      style: TextStyle(fontSize: 16),
                    ),
            ),
            const SizedBox(height: 24),
            if (_priceEstimate.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  border: Border.all(color: Colors.green),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    const Text(
                      '💰 Price Estimate',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.green,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _priceEstimate,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.green,
                      ),
                    ),
                  ],
                ),
              ),
                   const SizedBox(height: 20),
                   if (_livePricingInfo.isNotEmpty)
                     Container(
                       padding: const EdgeInsets.all(12),
                       decoration: BoxDecoration(
                         color: Colors.blue.shade50,
                         border: Border.all(color: Colors.blue),
                         borderRadius: BorderRadius.circular(8),
                       ),
                       child: Row(
                         children: [
                           const Icon(Icons.wifi, color: Colors.blue, size: 20),
                           const SizedBox(width: 8),
                           Expanded(
                             child: Text(
                               _livePricingInfo,
                               style: const TextStyle(
                                 fontSize: 14,
                                 fontWeight: FontWeight.w600,
                                 color: Colors.blue,
                               ),
                             ),
                           ),
                         ],
                       ),
                     ),
                   const SizedBox(height: 20),
                   const Text(
                     '🌟 Mobile Features',
                     style: TextStyle(
                       fontSize: 18,
                       fontWeight: FontWeight.bold,
                     ),
                   ),
                   const SizedBox(height: 12),
                   const Text('• Real-time dynamic pricing'),
                   const Text('• Live WebSocket updates'),
                   const Text('• Location-based pricing'),
                   const Text('• Flutter cross-platform'),
                   const Text('• Native performance'),
          ],
        ),
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    _connectToPricingWebSocket();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    // Check if user is already logged in (in production, check stored token)
    setState(() {
      _isLoggedIn = false; // Default to not logged in
    });
  }

  Future<void> _login() async {
    try {
      final response = await http.post(
        Uri.parse('http://localhost:8006/api/v1/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': 'user@equilibrium.com',
          'password': 'secret'
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _isLoggedIn = true;
          _accessToken = data['access_token'];
        });
        
        // Get user info
        await _getUserInfo();
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Login successful!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Login failed')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Login error: $e')),
      );
    }
  }

  Future<void> _getUserInfo() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8006/api/v1/auth/me'),
        headers: {
          'Authorization': 'Bearer $_accessToken',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _userEmail = data['email'];
          _userRole = data['role'];
        });
      }
    } catch (e) {
      print('Error getting user info: $e');
    }
  }

  void _logout() {
    setState(() {
      _isLoggedIn = false;
      _userEmail = '';
      _userRole = '';
      _accessToken = '';
    });
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Logged out successfully')),
    );
  }

  void _connectToPricingWebSocket() {
    try {
      _pricingChannel = WebSocketChannel.connect(
        Uri.parse('ws://localhost:8005/ws/pricing'),
      );
      
      _pricingSubscription = _pricingChannel!.stream.listen(
        (data) {
          final message = jsonDecode(data);
          if (message['type'] == 'pricing_update') {
            setState(() {
              _livePricingInfo = 'Live: ${message['data']['zone_id']} - ${message['data']['surge_multiplier']}x surge';
            });
          }
        },
        onError: (error) {
          print('WebSocket error: $error');
        },
      );
    } catch (e) {
      print('Failed to connect to WebSocket: $e');
    }
  }

  @override
  void dispose() {
    _pricingSubscription?.cancel();
    _pricingChannel?.sink.close();
    _pickupController.dispose();
    _dropoffController.dispose();
    super.dispose();
  }
}
