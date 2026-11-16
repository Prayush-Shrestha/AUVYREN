/// Authentication provider: manages session, CSRF, and user state.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../core/api_client.dart';
import '../models/user.dart';

class AuthProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient.instance;

  User? _user;
  bool _isLoading = false;
  String? _error;
  bool _initialized = false;

  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;
  bool get isInitialized => _initialized;

  /// Check if there's a stored session and validate it with the API.
  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    final authenticated = await _api.isAuthenticated;
    if (!authenticated) {
      notifyListeners();
      return;
    }

    await _fetchCurrentUser();
  }

  /// Fetch the current user from /auth/me.
  Future<void> _fetchCurrentUser() async {
    _setLoading(true);
    try {
      final response = await _api.get('/auth/me');
      if (response.statusCode == 200) {
        _user = User.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        await _api.clearAuth();
        _user = null;
      } else {
        _error = 'Failed to load profile (${response.statusCode})';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  /// Register a new account.
  Future<bool> register({
    required String email,
    required String password,
    String? fullName,
  }) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.post(
        '/auth/register',
        body: {
          'email': email,
          'password': password,
          'full_name': fullName,
        },
        isAuth: true,
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _user = User.fromJson(data['user'] as Map<String, dynamic>);
        notifyListeners();
        return true;
      } else if (response.statusCode == 409) {
        _error = 'An account with this email already exists.';
      } else {
        _error = 'Registration failed (${response.statusCode})';
      }
      return false;
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Sign in with email and password.
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.post(
        '/auth/login',
        body: {
          'email': email,
          'password': password,
        },
        isAuth: true,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _user = User.fromJson(data['user'] as Map<String, dynamic>);
        notifyListeners();
        return true;
      } else {
        _error = 'Invalid email or password.';
        return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Sign out and clear all tokens.
  Future<void> logout() async {
    await _api.post('/auth/logout');
    await _api.clearAuth();
    _user = null;
    _error = null;
    notifyListeners();
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
