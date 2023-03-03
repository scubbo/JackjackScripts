from datetime import datetime, timedelta
from os import sep
from pathlib import Path
from typing import Dict

from .constants import TIME_FORMAT
from .obsidian_path import ObsidianPath


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
    friday_template_path = template_path.joinpath('Morning Routine (Friday).md')
    weekend_template_path = template_path.joinpath('Morning Routine (Weekend).md')

    def _get_template_path(d: datetime):
        if _is_weekend(d):
            return weekend_template_path
        if _is_friday(d):
            return friday_template_path
        return routine_template_path

    gtd_dir_path = vault_path.joinpath('GTD')
    gtd_todos_dir_path = gtd_dir_path.joinpath('Daily TODOs')

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
        'vault_path': ObsidianPath(vault_path, '')
    }


def _is_weekend(d: datetime):
    return d.isoweekday() in (6, 7)


def _is_friday(d: datetime):
    return d.isoweekday() == 5
