/// API configuration constants for the Auvyren mobile client.
///
/// The API is served through Caddy at https://localhost:8443 in development.
/// On Android emulators, `localhost` refers to the emulator itself, so the
/// host machine is reachable at 10.0.2.2.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'AUVYREN_API_BASE_URL',
    defaultValue: 'https://localhost:8443',
  );

  static const String apiV1 = '$baseUrl/api/v1';

  /// Whether to accept self-signed certificates (development only).
  static const bool allowSelfSigned = true;
}
