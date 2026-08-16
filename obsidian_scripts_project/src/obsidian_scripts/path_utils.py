import re

from datetime import datetime, timedelta
from os import sep
from pathlib import Path
from typing import Dict, Optional

from .constants import TIME_FORMAT
from .obsidian_path import ObsidianPath

TODO_NOTE_NAME = re.compile(r'Todo - (\d{4}-\d{2}-\d{2})')


def _todos_dir(vault_path: Path) -> Path:
    return vault_path.joinpath('GTD').joinpath('Daily TODOs')


def most_recent_todo_before(vault_name: str, today_string: str) -> Optional[ObsidianPath]:
    """The latest TODO note dated earlier than `today_string`, if there is one.

    Not simply yesterday's note - days without one are routine, weekends especially.
    Dropbox leaves conflicted copies whose names carry a second date, so only notes
    named exactly for their day are considered.
    """
    today = datetime.strptime(today_string, TIME_FORMAT)
    earlier_notes = []
    for note in _todos_dir(Path(vault_name)).glob('Todo - *.md'):
        note_name = TODO_NOTE_NAME.fullmatch(note.stem)
        if not note_name:
            continue
        note_date = datetime.strptime(note_name.group(1), TIME_FORMAT)
        if note_date < today:
            earlier_notes.append((note_date, note))
    if not earlier_notes:
        return None
    return ObsidianPath.build_from_system_path(max(earlier_notes)[1])


# TODO - implement a properly typed return (or at least a namedtuple) for this
def build_paths(vault_name, today_string) -> Dict[str, ObsidianPath]:

    # Sucks to be parsing this string to a datetime here _and_ in `main`, but the alternative
    # would be passing two dependent variables into this method, which feels worse.
    # (Note we don't need to do error-checking here because it's already done in `main`, and because
    # this is just a personal utility script rather than an Enterprise Product(tm))
    today = datetime.strptime(today_string, TIME_FORMAT)

    vault_path = Path(vault_name)
    template_path = Path(vault_path.joinpath('Templates', str(today.year)))
    routine_template_path = template_path.joinpath('Morning Routine.md')
    weekend_template_path = template_path.joinpath('Morning Routine (Weekend).md')

    def _get_template_path(d: datetime):
        if _is_weekend(d):
            return weekend_template_path
        return routine_template_path

    gtd_todos_dir_path = _todos_dir(vault_path)

    def _date_to_todo_path(d: datetime):
        return gtd_todos_dir_path.joinpath(f'Todo - {d.strftime(TIME_FORMAT)}.md')

    daily_notes_dir_path = vault_path.joinpath('Daily Notes')
    daily_note_index_path =\
        ObsidianPath.build_from_system_path(vault_path.joinpath('Daily Note Index.md'))
    daily_note_path =\
        ObsidianPath.build_from_system_path(daily_notes_dir_path.joinpath(f'{today_string}.md'))
    todo_path =\
        ObsidianPath.build_from_system_path(_date_to_todo_path(today))
    template_obsidian_path =\
        ObsidianPath.build_from_system_path(_get_template_path(today))
    return {
        'daily_note_index_path': daily_note_index_path,
        'daily_note_path': daily_note_path,
        'todo_path': todo_path,
        'template_path': template_obsidian_path,
        'vault_path': ObsidianPath(vault_path, ''),
        'project_root': ObsidianPath(vault_path.joinpath('GTD').joinpath('Projects'), 'GTD/Projects')
    }


def _is_weekend(d: datetime):
    return d.isoweekday() in (6, 7)
