import src.obsidian_scripts.tasks as tasks
from unittest import TestCase


class TestTaskUtils(TestCase):
    def test_basic_list(self):
        lines = [
            '- [ ] task 1',
            '- [ ] task 2',
            '- [X] task 3'
        ]
        parsed = tasks.parse_task_list(lines)
        self.assertEqual(
            list(map(lambda task: task.content, parsed)),
            ['task 1', 'task 2', 'task 3']
        )
        self.assertEqual(
            list(map(lambda task: task.done, parsed)),
            [False, False, True]
        )

    def test_basic_string(self):
        parsed = tasks.parse_task_string('- [ ] task 1\n- [ ] task 2\n- [ ] task 3')
        self.assertEqual(
            list(map(lambda task: task.content, parsed)),
            ['task 1', 'task 2', 'task 3']
        )

    def test_sub_tasks(self):
        s = '''- [ ] task 1
- [ ] task 2
    - [ ] subtask 2-1
    - [ ] subtask 2-2
        - [ ] subsubtask alpha
    - [ ] subtask 2-3
- [ ] task 3
    - [ ] task 3-1
'''
        parsed = tasks.parse_task_string(s)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(len(parsed[0].subtasks), 0)
        self.assertEqual(len(parsed[1].subtasks), 3)
        self.assertEqual(parsed[1].subtasks[1].subtasks[0].content, 'subsubtask alpha')
