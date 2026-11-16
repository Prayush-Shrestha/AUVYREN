/// Note provider: manages note list state and CRUD operations.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../core/api_client.dart';
import '../models/note.dart';

class NoteProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient.instance;

  List<Note> _notes = [];
  bool _isLoading = false;
  String? _error;

  List<Note> get notes => _notes;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch all notes for the authenticated user.
  Future<void> loadNotes() async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.get('/knowledge');
      if (response.statusCode == 200) {
        final List<dynamic> notesJson = jsonDecode(response.body) as List<dynamic>;
        _notes = notesJson.map((json) => Note.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        _error = 'Failed to load notes (${response.statusCode})';
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  /// Create a new note.
  Future<Note?> createNote({
    required String title,
    String? content,
    String kind = 'note',
    String? tags,
  }) async {
    _setLoading(true);
    _error = null;
    try {
      final response = await _api.post(
        '/knowledge',
        body: {
          'title': title,
          'content': ?content,
          'kind': kind,
          'tags': ?tags,
        },
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final note = Note.fromJson(data);
        _notes.insert(0, note);
        notifyListeners();
        return note;
      } else {
        _error = 'Failed to create note (${response.statusCode})';
        return null;
      }
    } catch (e) {
      _error = e.toString();
      return null;
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
