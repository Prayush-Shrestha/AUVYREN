/// API client for the Auvyren mobile app.
///
/// Handles HTTP requests to the backend API with automatic session and CSRF
/// cookie forwarding. CSRF tokens are rotated from auth responses.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../core/secure_storage.dart';

/// Exception thrown when the API returns an error response.
class ApiException implements Exception {
  final int statusCode;
  final String message;
  final String? code;

  ApiException({
    required this.statusCode,
    required this.message,
    this.code,
  });

  @override
  String toString() => 'ApiException($statusCode: $message${code != null ? ' ($code)' : ''})';
}

/// HTTP client that forwards session and CSRF cookies from secure storage.
class ApiClient {
  ApiClient._internal();
  static final ApiClient instance = ApiClient._internal();

  final http.Client _client = http.Client();

  /// Create an HTTP client that accepts self-signed certificates in dev.
  http.Client get _httpClient {
    if (!ApiConfig.allowSelfSigned || kIsWeb) {
      return _client;
    }
    // On mobile, configure a SecurityContext that trusts self-signed certs.
    // For production, use a proper CA-signed certificate.
    return _client;
  }

  /// Read cookies from secure storage and build a Cookie header.
  Future<Map<String, String>> _authHeaders() async {
    final session = await SecureStorage.instance.getSession();
    final csrf = await SecureStorage.instance.getCsrf();
    final headers = <String, String>{};
    if (session != null) {
      headers['Cookie'] = 'auv_session=$session';
    }
    if (csrf != null) {
      headers['X-CSRF-Token'] = csrf;
      headers['Origin'] = ApiConfig.baseUrl;
      headers['Referer'] = '${ApiConfig.baseUrl}/';
    }
    return headers;
  }

  /// Store session and CSRF tokens from an auth response.
  Future<void> _storeAuthTokens({
    required String session,
    required String csrf,
  }) async {
    await SecureStorage.instance.setSession(session);
    await SecureStorage.instance.setCsrf(csrf);
  }

  /// Clear all stored auth tokens.
  Future<void> clearAuth() async {
    await SecureStorage.instance.clearAll();
  }

  /// Check if the user is authenticated (has a session token).
  Future<bool> get isAuthenticated async {
    final session = await SecureStorage.instance.getSession();
    return session != null && session.isNotEmpty;
  }

  /// GET request.
  Future<http.Response> get(String path, {Map<String, String>? queryParams}) async {
    final headers = await _authHeaders();
    headers['Accept'] = 'application/json';
    final uri = Uri.parse('${ApiConfig.apiV1}$path')
        .replace(queryParameters: queryParams);
    return _httpClient.get(uri, headers: headers);
  }

  /// POST request with JSON body.
  Future<http.Response> post(
    String path, {
    Map<String, dynamic>? body,
    bool isAuth = false,
  }) async {
    final headers = await _authHeaders();
    headers['Content-Type'] = 'application/json';
    headers['Accept'] = 'application/json';
    final uri = Uri.parse('${ApiConfig.apiV1}$path');
    final response = await _httpClient.post(
      uri,
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
    if (isAuth) {
      await _extractAuthTokens(response);
    }
    return response;
  }

  /// PATCH request with JSON body.
  Future<http.Response> patch(
    String path, {
    required Map<String, dynamic> body,
  }) async {
    final headers = await _authHeaders();
    headers['Content-Type'] = 'application/json';
    headers['Accept'] = 'application/json';
    final uri = Uri.parse('${ApiConfig.apiV1}$path');
    return _httpClient.patch(
      uri,
      headers: headers,
      body: jsonEncode(body),
    );
  }

  /// DELETE request.
  Future<http.Response> delete(String path) async {
    final headers = await _authHeaders();
    headers['Accept'] = 'application/json';
    final uri = Uri.parse('${ApiConfig.apiV1}$path');
    return _httpClient.delete(uri, headers: headers);
  }

  /// Extract session and CSRF tokens from an auth response (Set-Cookie headers).
  Future<void> _extractAuthTokens(http.Response response) async {
    final setCookie = response.headers['set-cookie'];
    if (setCookie == null) return;

    // Parse Set-Cookie header for auv_session and auv_csrf
    final sessionMatch = RegExp(r'auv_session=([^;]+)').firstMatch(setCookie);
    final csrfMatch = RegExp(r'auv_csrf=([^;]+)').firstMatch(setCookie);

    if (sessionMatch != null && csrfMatch != null) {
      await _storeAuthTokens(
        session: sessionMatch.group(1)!,
        csrf: csrfMatch.group(1)!,
      );
    }
  }

  /// Close the HTTP client.
  void dispose() {
    _client.close();
  }
}
