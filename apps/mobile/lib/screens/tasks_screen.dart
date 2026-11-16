import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/task_provider.dart';
import '../models/task.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  @override
  void initState() {
    super.initState();
    context.read<TaskProvider>().loadTasks();
  }

  @override
  Widget build(BuildContext context) {
    final taskProvider = context.watch<TaskProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tasks'),
      ),
      body: taskProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : taskProvider.tasks.isEmpty
              ? const Center(
                  child: Text('No tasks yet. Create one to get started.'),
                )
              : ListView.builder(
                  itemCount: taskProvider.tasks.length,
                  itemBuilder: (context, index) {
                    final task = taskProvider.tasks[index];
                    return _TaskTile(task: task);
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: open create task screen
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _TaskTile extends StatelessWidget {
  final Task task;

  const _TaskTile({required this.task});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(task.title),
      subtitle: Text(task.description ?? ''),
      trailing: Checkbox(
        value: task.status == TaskStatus.done,
        onChanged: (value) async {
          await context.read<TaskProvider>().updateTaskStatus(
            task.id,
            value! ? 'done' : 'todo',
          );
        },
      ),
      onTap: () {
        // TODO: open task detail
      },
    );
  }
}
