import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class SyncProvider {
  final List<Map<String, dynamic>> _queue = [];

  Future<void> load() async {
    final preferences = await SharedPreferences.getInstance();
    final saved = preferences.getStringList('sync_queue') ?? [];
    _queue
      ..clear()
      ..addAll(saved.map((item) => Map<String, dynamic>.from(jsonDecode(item) as Map)));
  }

  Future<void> enqueue(Map<String, dynamic> payload) async {
    _queue.add(payload);
    await _save();
  }

  Future<void> retry(Future<void> Function(Map<String, dynamic>) sender) async {
    for (final item in List<Map<String, dynamic>>.from(_queue)) {
      try {
        await sender(item);
        _queue.remove(item);
        await _save();
      } catch (_) {
        break;
      }
    }
  }

  Future<void> _save() async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setStringList(
      'sync_queue',
      _queue.map(jsonEncode).toList(),
    );
  }

}
