/// Task model returned by the tasks API.
library;

enum TaskStatus {
  todo,
  inProgress,
  done,
  cancelled;

  String get value {
    switch (this) {
      case TaskStatus.todo:
        return 'todo';
      case TaskStatus.inProgress:
        return 'in_progress';
      case TaskStatus.done:
        return 'done';
      case TaskStatus.cancelled:
        return 'cancelled';
    }
  }

  static TaskStatus fromString(String value) {
    switch (value) {
      case 'todo':
        return TaskStatus.todo;
      case 'in_progress':
        return TaskStatus.inProgress;
      case 'done':
        return TaskStatus.done;
      case 'cancelled':
        return TaskStatus.cancelled;
      default:
        return TaskStatus.todo;
    }
  }
}

extension TaskStatusExtension on TaskStatus {}

class Task {
  final String id;
  final String userId;
  final String? projectId;
  final String title;
  final String? description;
  final TaskStatus status;
  final String? priority;
  final String? category;
  final String? dueAt;
  final String? plannedFor;
  final int? estimatedMinutes;
  final int? sortOrder;
  final String? completedAt;
  final String? deletedAt;
  final String createdAt;
  final String updatedAt;

  Task({
    required this.id,
    required this.userId,
    this.projectId,
    required this.title,
    this.description,
    required this.status,
    this.priority,
    this.category,
    this.dueAt,
    this.plannedFor,
    this.estimatedMinutes,
    this.sortOrder,
    this.completedAt,
    this.deletedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      projectId: json['project_id'] as String?,
      title: json['title'] as String,
      description: json['description'] as String?,
      status: TaskStatus.fromString(json['status'] as String? ?? 'todo'),
      priority: json['priority'] as String?,
      category: json['category'] as String?,
      dueAt: json['due_at'] as String?,
      plannedFor: json['planned_for'] as String?,
      estimatedMinutes: json['estimated_minutes'] as int?,
      sortOrder: json['sort_order'] as int?,
      completedAt: json['completed_at'] as String?,
      deletedAt: json['deleted_at'] as String?,
      createdAt: json['created_at'] as String,
      updatedAt: json['updated_at'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'project_id': projectId,
      'title': title,
      'description': description,
      'status': status.value,
      'priority': priority,
      'category': category,
      'due_at': dueAt,
      'planned_for': plannedFor,
      'estimated_minutes': estimatedMinutes,
      'sort_order': sortOrder,
      'completed_at': completedAt,
      'deleted_at': deletedAt,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}

class TaskCreate {
  final String title;
  final String? description;
  final String? projectId;
  final String? priority;
  final String? category;
  final String? dueAt;
  final String? plannedFor;
  final int? estimatedMinutes;

  TaskCreate({
    required this.title,
    this.description,
    this.projectId,
    this.priority,
    this.category,
    this.dueAt,
    this.plannedFor,
    this.estimatedMinutes,
  });

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      if (description != null) 'description': description,
      if (projectId != null) 'project_id': projectId,
      if (priority != null) 'priority': priority,
      if (category != null) 'category': category,
      if (dueAt != null) 'due_at': dueAt,
      if (plannedFor != null) 'planned_for': plannedFor,
      if (estimatedMinutes != null) 'estimated_minutes': estimatedMinutes,
    };
  }
}
