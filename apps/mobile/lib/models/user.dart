/// User model returned by the auth API.
library;

class User {
  final String id;
  final String email;
  final String? fullName;
  final bool isActive;
  final bool emailVerified;
  final String? lastLoginAt;
  final String? createdAt;
  final Map<String, dynamic>? settings;

  User({
    required this.id,
    required this.email,
    this.fullName,
    required this.isActive,
    required this.emailVerified,
    this.lastLoginAt,
    this.createdAt,
    this.settings,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String?,
      isActive: json['is_active'] as bool? ?? false,
      emailVerified: json['email_verified'] as bool? ?? false,
      lastLoginAt: json['last_login_at'] as String?,
      createdAt: json['created_at'] as String?,
      settings: json['settings'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'is_active': isActive,
      'email_verified': emailVerified,
      'last_login_at': lastLoginAt,
      'created_at': createdAt,
      'settings': settings,
    };
  }
}
