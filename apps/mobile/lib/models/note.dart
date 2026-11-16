/// Note model returned by the knowledge API.
library;

enum NoteKind {
  note,
  journal,
  decision,
  review;

  String get value {
    switch (this) {
      case NoteKind.note:
        return 'note';
      case NoteKind.journal:
        return 'journal';
      case NoteKind.decision:
        return 'decision';
      case NoteKind.review:
        return 'review';
    }
  }

  static NoteKind fromString(String value) {
    switch (value) {
      case 'journal':
        return NoteKind.journal;
      case 'decision':
        return NoteKind.decision;
      case 'review':
        return NoteKind.review;
      default:
        return NoteKind.note;
    }
  }
}

extension NoteKindExtension on NoteKind {}

class Note {
  final String id;
  final String userId;
  final String title;
  final String? content;
  final NoteKind kind;
  final String? sourceType;
  final String? sourceId;
  final String? tags;
  final String? deletedAt;
  final String createdAt;
  final String updatedAt;

  Note({
    required this.id,
    required this.userId,
    required this.title,
    this.content,
    required this.kind,
    this.sourceType,
    this.sourceId,
    this.tags,
    this.deletedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      title: json['title'] as String,
      content: json['content'] as String?,
      kind: NoteKind.fromString(json['kind'] as String? ?? 'note'),
      sourceType: json['source_type'] as String?,
      sourceId: json['source_id'] as String?,
      tags: json['tags'] as String?,
      deletedAt: json['deleted_at'] as String?,
      createdAt: json['created_at'] as String,
      updatedAt: json['updated_at'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'title': title,
      'content': content,
      'kind': kind.value,
      'source_type': sourceType,
      'source_id': sourceId,
      'tags': tags,
      'deleted_at': deletedAt,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}

class NoteCreate {
  final String title;
  final String? content;
  final NoteKind kind;
  final String? tags;

  NoteCreate({
    required this.title,
    this.content,
    this.kind = NoteKind.note,
    this.tags,
  });

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      if (content != null) 'content': content,
      'kind': kind.value,
      if (tags != null) 'tags': tags,
    };
  }
}
