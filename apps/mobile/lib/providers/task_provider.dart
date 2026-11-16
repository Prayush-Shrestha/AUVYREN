/// Task provider: manages task list state and CRUD operations.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../core/api_client.dart';
import '../models/task.dart';

class TaskProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient.instance;

  List<Task> _tasks = [];
  bool _isLoading = false;
  String? _error;

  List<Task> get tasks => _tasks;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch all tasks for the authenticated user.
  Future<void> loadTasks({String? status, String? projectId}) async {
    _setLoading(true);
    _error = null;
    try {
      final queryParams = <String, String>{};
      if (status != null) queryParams['status'] = status;
      if (projectId != null) queryParams['project_id'] = projectId;

      final response = await _api.get('/tasks', queryParams: queryParams);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final List<dynamic> tasksJson = data['tasks'] as List<dynamic>;
        _tasks = tasksJson.map((json) => Task.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        _error = 'Failed to load tasks (${response.statusCode})';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  /// Create a new task.
  Future<Task?> createTask({
    required String title,
    String? description,
    String? projectId,
    String? priority,
    String? category,
    String? dueAt,
    String? plannedFor,
    int? estimatedMinutes,
  }) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.post(
        '/tasks',
        body: {
          'title': title,
          'description': ?description,
          'project_id': ?projectId,
          'priority': ?priority,
          'category': ?category,
          'due_at': ?dueAt,
          'planned_for': ?plannedFor,
          'estimated_minutes': ?estimatedMinutes,
        },
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final task = Task.fromJson(data);
        _tasks.insert(0, task);
        notifyListeners();
        return task;
      } else {
        _error = 'Failed to create task (${response.statusCode})';
        return null;
      }
    } catch (e) {
      _error = e.toString();
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Update a task's status.
  Future<bool> updateTaskStatus(String taskId, String status) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.patch(
        '/tasks/$taskId/status',
        body: {'status': status},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final updated = Task.fromJson(data);
        _tasks = _tasks.map((t) => t.id == taskId ? updated : t).toList();
        notifyListeners();
        return true;
      } else {
        _error = 'Failed to update task (${response.statusCode})';
        return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Soft-delete a task.
  Future<bool> deleteTask(String taskId) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.delete('/tasks/$taskId');

      if (response.statusCode == 204) {
        _tasks.removeWhere((t) => t.id == taskId);
        notifyListeners();
        return true;
      } else {
        _error = 'Failed to delete task (${response.statusCode})';
        return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _setLoading(false);
    }
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
