/// Secure storage for session and CSRF tokens.
///
/// Tokens are stored in the platform's encrypted keystore (Keychain on iOS,
/// Keystore on Android, encrypted local storage on web).
library;

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  SecureStorage._internal();
  static final SecureStorage instance = SecureStorage._internal();

  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static const String _sessionKey = 'auv_session';
  static const String _csrfKey = 'auv_csrf';

  /// Store the session cookie value.
  Future<void> setSession(String value) async {
    await _storage.write(key: _sessionKey, value: value);
  }

  /// Read the session cookie value.
  Future<String?> getSession() async => _storage.read(key: _sessionKey);

  /// Delete the session cookie value.
  Future<void> deleteSession() async => _storage.delete(key: _sessionKey);

  /// Store the CSRF token value.
  Future<void> setCsrf(String value) async {
    await _storage.write(key: _csrfKey, value: value);
  }

  /// Read the CSRF token value.
  Future<String?> getCsrf() async => _storage.read(key: _csrfKey);

  /// Delete the CSRF token value.
  Future<void> deleteCsrf() async => _storage.delete(key: _csrfKey);

  /// Clear all authentication tokens (logout).
  Future<void> clearAll() async {
    await deleteSession();
    await deleteCsrf();
  }
}
