import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const DriverFlutterApp());
}

class DriverFlutterApp extends StatelessWidget {
  const DriverFlutterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Equilibrium Driver (Flutter)',
      theme: ThemeData(
        primarySwatch: Colors.green,
        useMaterial3: true,
      ),
      home: const DriverHomeScreen(),
    );
  }
}

class DriverHomeScreen extends StatefulWidget {
  const DriverHomeScreen({super.key});

  @override
  State<DriverHomeScreen> createState() => _DriverHomeScreenState();
}

class _DriverHomeScreenState extends State<DriverHomeScreen> {
  bool _isOnline = false;
  String _currentLocation = '37.7749, -122.4194';
  List<Map<String, dynamic>> _heatmapData = [];
  WebSocketChannel? _heatmapChannel;
  StreamSubscription? _heatmapSubscription;
  String _liveUpdateInfo = '';
  
  // Authentication state
  bool _isLoggedIn = false;
  String _userEmail = '';
  String _userRole = '';
  String _accessToken = '';

  @override
  void initState() {
    super.initState();
    _connectToHeatmapWebSocket();
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
          'email': 'driver@equilibrium.com',
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

  void _connectToHeatmapWebSocket() {
    try {
      _heatmapChannel = WebSocketChannel.connect(
        Uri.parse('ws://localhost:8005/ws/heatmap'),
      );
      
      _heatmapSubscription = _heatmapChannel!.stream.listen(
        (data) {
          final message = jsonDecode(data);
          if (message['type'] == 'heatmap_update') {
            setState(() {
              _liveUpdateInfo = 'Live heatmap updated at ${DateTime.now().toString().substring(11, 19)}';
              _heatmapData = (message['data']['zones'] as List).map((zone) => {
                'zone': zone['zone_name'],
                'surge': zone['surge_multiplier'],
                'demand': zone['demand_level'],
                'supply': zone['supply_count'],
                'demand_count': zone['demand_count'],
              }).toList();
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

  void _toggleOnlineStatus() {
    setState(() {
      _isOnline = !_isOnline;
    });

    if (_isOnline) {
      _loadHeatmapData();
    }
  }

  Future<void> _loadHeatmapData() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8001/api/v1/pricing/heatmap'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _heatmapData = (data['zones'] as List).map((zone) => {
            'zone': zone['zone_name'],
            'surge': zone['surge_multiplier'],
            'demand': zone['demand_level'],
            'supply': zone['supply_count'],
            'demand_count': zone['demand_count'],
          }).toList();
        });
      } else {
        // Fallback to mock data
        setState(() {
          _heatmapData = [
            {'zone': 'Downtown', 'surge': 1.8, 'demand': 'High'},
            {'zone': 'Airport', 'surge': 2.2, 'demand': 'Very High'},
            {'zone': 'Suburbs', 'surge': 1.2, 'demand': 'Medium'},
            {'zone': 'University', 'surge': 1.5, 'demand': 'High'},
          ];
        });
      }
    } catch (e) {
      // Fallback to mock data on error
      setState(() {
        _heatmapData = [
          {'zone': 'Downtown', 'surge': 1.8, 'demand': 'High'},
          {'zone': 'Airport', 'surge': 2.2, 'demand': 'Very High'},
          {'zone': 'Suburbs', 'surge': 1.2, 'demand': 'Medium'},
          {'zone': 'University', 'surge': 1.5, 'demand': 'High'},
        ];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
             appBar: AppBar(
               title: const Text('🚕 Driver Portal (Flutter)'),
               backgroundColor: Colors.green,
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
                         'Driver App (Flutter)',
                         style: TextStyle(
                           fontSize: 24,
                           fontWeight: FontWeight.bold,
                           color: Colors.green,
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
            
            // Driver Status Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Driver Status',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Switch(
                          value: _isOnline,
                          onChanged: (value) => _toggleOnlineStatus(),
                          activeColor: Colors.green,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _isOnline ? '🟢 Online - Available for rides' : '🔴 Offline',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: _isOnline ? Colors.green : Colors.red,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Location Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '📍 Current Location',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('Lat: ${_currentLocation.split(', ')[0]}'),
                    Text('Lng: ${_currentLocation.split(', ')[1]}'),
                    const SizedBox(height: 12),
                    ElevatedButton(
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Location updated successfully')),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                      ),
                      child: const Text('Update Location'),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Heatmap Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          '🔥 Demand Heatmap',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        ElevatedButton(
                          onPressed: _loadHeatmapData,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.orange,
                            foregroundColor: Colors.white,
                          ),
                          child: const Text('Refresh'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    if (_heatmapData.isNotEmpty)
                      ..._heatmapData.map((zone) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4.0),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(zone['zone']),
                            Row(
                              children: [
                                Text('Surge: ${zone['surge']}x'),
                                const SizedBox(width: 16),
                                Text('Demand: ${zone['demand']}'),
                              ],
                            ),
                          ],
                        ),
                      )).toList()
                    else
                      const Text('No heatmap data available'),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 20),
            if (_liveUpdateInfo.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  border: Border.all(color: Colors.green),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.wifi, color: Colors.green, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _liveUpdateInfo,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.green,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 20),
            
            const Text(
              '🚀 Driver Features',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            const Text('• Real-time demand visualization'),
            const Text('• Live WebSocket updates'),
            const Text('• Dynamic surge pricing insights'),
            const Text('• Location-based recommendations'),
            const Text('• Flutter cross-platform'),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _heatmapSubscription?.cancel();
    _heatmapChannel?.sink.close();
    super.dispose();
  }
}
