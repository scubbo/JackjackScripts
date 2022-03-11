from datetime import datetime, timedelta
from os import sep
from pathlib import Path

from .constants import TIME_FORMAT


# TODO - implement a properly typed return (or at least a namedtuple) for this
def build_paths(vault_name, today_string):

    # Sucks to be parsing this string to a datetime here _and_ in `main`, but the alternative
    # would be passing two dependent variables into this method, which feels worse.
    # (Note we don't need to do error-checking here because it's already done in `main`, and because
    # this is just a personal utility script rather than an Enterprise Product(tm))
    today = datetime.strptime(today_string, TIME_FORMAT)

    vault_path = Path(vault_name)
    template_path = Path(vault_path.joinpath('Templates'))
    routine_template_path = template_path.joinpath('Morning Routine - 2022.md')
    friday_template_path = template_path.joinpath('Morning Routine (Friday) - 2022.md')
    weekend_template_path = template_path.joinpath('Morning Routine (Weekend) - 2022.md')

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
    daily_note_index_path = vault_path.joinpath('Daily Note Index.md')
    daily_note_path = daily_notes_dir_path.joinpath(f'{today_string}.md')
    todo_path = _date_to_todo_path(today)
    # Unstar the TODO from 2 days prior, so we have today's and yesterday's for reference
    previous_todo_path = _date_to_todo_path(today - timedelta(2))
    template_path = _get_template_path(today)
    return {
        'daily_note_index_path': daily_note_index_path,
        'daily_note_path': daily_note_path,
        'todo_path': todo_path,
        'previous_todo_path': previous_todo_path,
        'template_path': template_path,
        'vault_path': vault_path
    }


def system_path_to_obsidian_path(path: Path):
    # [1:] removes the `scubbo-vault` path part
    # [:-3] removes `.md` suffix
    return sep.join(path.parts[1:])[:-3]


def system_path_to_bare_note_name(path: Path):
    return path.name[:-len(path.suffix)]


def _is_weekend(d: datetime):
    return d.isoweekday() in (6, 7)


def _is_friday(d: datetime):
    return d.isoweekday() == 5
