from dataclasses import dataclass

from re import compile
from typing import List, Optional


@dataclass
class Task:
    content: str
    done: bool
    subtasks: List['Task']


REGEX = compile('( *)- \\[(.)\\] (.*)')


def parse_task_string(content: str):
    lines = content.splitlines()
    return parse_task_list(lines)


def parse_task_list(lines: List[str]) -> List[Task]:
    top_level_tasks = []
    last_task_of_indent_value = {}
    for line in lines:
        print(line)
        match = REGEX.match(line)
        indent = len(match.group(1)) / 4
        done = match.group(2) == 'X'
        content = match.group(3)
        task = Task(content, done, [])
        last_task_of_indent_value[indent] = task
        if indent > 0:
            last_task_of_indent_value[indent-1].subtasks.append(task)
        else:
            top_level_tasks.append(task)
    return top_level_tasks



    length = len(lines)
    return_tasks = []
    for i in range(length):
        match = REGEX.match(lines[i])
        t = Task(content=match.group(2), done=match.group(1) == 'X', subtasks=[])
        if i < length - 1:
            sub_indent = lines[i+1].find('-')
            if sub_indent != 0:
                i += 1
                sub_lines = []
                while lines[i].find('-') >= sub_indent and i < length - 1:
                    sub_lines.append(lines[i])
                    i += 1
                t.subtasks = parse_task_list([line[sub_indent:] for line in sub_lines])
        return_tasks.append(t)
    return return_tasks
