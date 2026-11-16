/// Habit model returned by the habits API.
library;

class Habit {
  final String id;
  final String userId;
  final String title;
  final String? description;
  final String? schedule;
  final String? timezone;
  final String createdAt;
  final String updatedAt;

  Habit({
    required this.id,
    required this.userId,
    required this.title,
    this.description,
    this.schedule,
    this.timezone,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Habit.fromJson(Map<String, dynamic> json) {
    return Habit(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      schedule: json['schedule'] as String?,
      timezone: json['timezone'] as String?,
      createdAt: json['created_at'] as String,
      updatedAt: json['updated_at'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'title': title,
      'description': description,
      'schedule': schedule,
      'timezone': timezone,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}

class HabitCreate {
  final String title;
  final String? description;
  final String? schedule;
  final String? timezone;

  HabitCreate({
    required this.title,
    this.description,
    this.schedule,
    this.timezone,
  });

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      if (description != null) 'description': description,
      if (schedule != null) 'schedule': schedule,
      if (timezone != null) 'timezone': timezone,
    };
  }
}
