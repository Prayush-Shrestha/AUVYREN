/// Sync provider: manages pull/push synchronization with the backend.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../core/api_client.dart';
import '../models/note.dart';
import '../models/task.dart';

/// A change record for sync.
class SyncEventEntry {
  final String? id;
  final String entityType;
  final String entityId;
  final String action;
  final int revision;
  final Map<String, dynamic>? payload;
  final String? createdAt;

  SyncEventEntry({
    this.id,
    required this.entityType,
    required this.entityId,
    required this.action,
    required this.revision,
    this.payload,
    this.createdAt,
  });

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'entity_type': entityType,
      'entity_id': entityId,
      'action': action,
      'revision': revision,
      if (payload != null) 'payload': payload,
      if (createdAt != null) 'created_at': createdAt,
    };
  }
}

class SyncProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient.instance;

  List<SyncEventEntry> _events = [];
  String? _serverTimestamp;
  bool _isLoading = false;
  String? _error;
  DateTime? _lastSync;

  List<SyncEventEntry> get events => _events;
  String? get serverTimestamp => _serverTimestamp;
  bool get isLoading => _isLoading;
  String? get error => _error;
  DateTime? get lastSync => _lastSync;

  /// Register the current device with the backend.
  Future<bool> registerDevice({
    required String deviceId,
    String? deviceName,
    String? platform,
    String? appVersion,
  }) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.post(
        '/sync/devices',
        body: {
          'device_id': deviceId,
          'device_name': ?deviceName,
          'platform': ?platform,
          'app_version': ?appVersion,
        },
      );

      if (response.statusCode == 201) {
        notifyListeners();
        return true;
      } else {
        _error = 'Failed to register device (${response.statusCode})';
        return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Pull incremental sync events since the last sync.
  Future<void> pull({String? since}) async {
    _setLoading(true);
    _error = null;
    try {
      final queryParams = <String, String>{};
      if (since != null) queryParams['since'] = since;

      final response = await _api.get('/sync/pull', queryParams: queryParams);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _serverTimestamp = data['server_timestamp'] as String?;
        final List<dynamic> eventsJson = data['events'] as List<dynamic>;
        _events = eventsJson.map((json) {
          return SyncEventEntry(
            id: json['id'] as String?,
            entityType: json['entity_type'] as String,
            entityId: json['entity_id'] as String,
            action: json['action'] as String,
            revision: json['revision'] as int,
            payload: json['payload'] as Map<String, dynamic>?,
            createdAt: json['created_at'] as String?,
          );
        }).toList();
        _lastSync = DateTime.now();
      } else {
        _error = 'Failed to pull sync events (${response.statusCode})';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  /// Push local sync events to the backend with conflict resolution.
  Future<Map<String, dynamic>?> push(List<SyncEventEntry> events) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.post(
        '/sync/push',
        body: {
          'events': events.map((e) => e.toJson()).toList(),
          'client_timestamp': DateTime.now().toIso8601String(),
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _serverTimestamp = data['server_timestamp'] as String?;
        _lastSync = DateTime.now();
        notifyListeners();
        return {
          'applied': data['applied'] as int,
          'conflicts': data['conflicts'] as List<dynamic>,
        };
      } else {
        _error = 'Failed to push sync events (${response.statusCode})';
        return null;
      }
    } catch (e) {
      _error = e.toString();
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Create a sync event entry from a task.
  static SyncEventEntry fromTask(Task task, String action, int revision) {
    return SyncEventEntry(
      entityType: 'task',
      entityId: task.id,
      action: action,
      revision: revision,
      payload: task.toJson(),
    );
  }

  /// Create a sync event entry from a note.
  static SyncEventEntry fromNote(Note note, String action, int revision) {
    return SyncEventEntry(
      entityType: 'note',
      entityId: note.id,
      action: action,
      revision: revision,
      payload: note.toJson(),
    );
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
