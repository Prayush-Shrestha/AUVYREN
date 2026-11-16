/// Goal model returned by the goals API.
library;

enum GoalStatus {
  active,
  completed,
  archived;

  String get value {
    switch (this) {
      case GoalStatus.active:
        return 'active';
      case GoalStatus.completed:
        return 'completed';
      case GoalStatus.archived:
        return 'archived';
    }
  }

  static GoalStatus fromString(String value) {
    switch (value) {
      case 'completed':
        return GoalStatus.completed;
      case 'archived':
        return GoalStatus.archived;
      default:
        return GoalStatus.active;
    }
  }
}

extension GoalStatusExtension on GoalStatus {}

class Goal {
  final String id;
  final String userId;
  final String title;
  final String? description;
  final GoalStatus status;
  final String? targetDate;
  final String? createdAt;
  final String? updatedAt;

  Goal({
    required this.id,
    required this.userId,
    required this.title,
    this.description,
    required this.status,
    this.targetDate,
    this.createdAt,
    this.updatedAt,
  });

  factory Goal.fromJson(Map<String, dynamic> json) {
    return Goal(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      status: GoalStatus.fromString(json['status'] as String? ?? 'active'),
      targetDate: json['target_date'] as String?,
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'title': title,
      'description': description,
      'status': status.value,
      'target_date': targetDate,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}

class GoalCreate {
  final String title;
  final String? description;
  final String? targetDate;

  GoalCreate({
    required this.title,
    this.description,
    this.targetDate,
  });

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      if (description != null) 'description': description,
      if (targetDate != null) 'target_date': targetDate,
    };
  }
}
