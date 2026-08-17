#!/usr/bin/env python3

import argparse
import logging
import subprocess

from datetime import datetime
from pathlib import Path
from random import choice
from sys import stderr, stdout, exit

from .constants import OBLIQUE_STRATEGIES, TIME_FORMAT
from .obsidian_commands import open_file, bookmark_file, unbookmark_file
from .obsidian_path import ObsidianPath
from .path_utils import build_paths, most_recent_todo_before
from .bookmark_utils import get_bookmarked_todos_in_date_order
from .project_summary import text_of_overview


logging.basicConfig(stream=stdout, level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def _abort(message: str):
    """Reports on stderr and exits non-zero, so that a caller which only surfaces
    error streams - such as Obsidian's Shell commands plugin - shows the reason."""
    print(message, file=stderr)
    exit(1)


def _check_nothing_is_in_the_way(paths):
    """Validates every path `main` depends on before a single byte is written.

    Triggering setup is a one-click action, so it gets repeated by accident. Aborting
    partway through used to leave a duplicated index entry behind, or a daily note with
    no matching TODO note."""
    if not paths['vault_path'].system_path.exists():
        _abort(f'Vault does not exist at path {paths["vault_path"].system_path}')

    # Templates are filed per-year, so this is the check that fires each 1st of January
    if not paths['template_path'].system_path.exists():
        _abort(f'No template to build today\'s TODO note from, expected it at '
               f'{paths["template_path"].system_path}')

    for description, path in (('Daily note', paths['daily_note_path']),
                              ('TODO note', paths['todo_path'])):
        if path.system_path.exists():
            _abort(f'{description} already exists at {path.system_path} '
                   f'- has today already been set up?')


def _recurring_tasks_section(vault_path: Path, today: datetime) -> str:
    """Renders the still-active items of `GTD/Recurring Tasks.md` as a checkbox section.

    Bulleted lines become checkboxes; anything else in the note is commentary. An item
    may limit its own lifetime with a trailing `| until: YYYY-MM-DD` (inclusive)."""
    recurring_path = vault_path.joinpath('GTD', 'Recurring Tasks.md')
    if not recurring_path.exists():
        return ''
    items = []
    for line in recurring_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped.startswith(('- ', '* ')):
            continue
        item, _, qualifier = (part.strip() for part in stripped[2:].partition('|'))
        if qualifier.startswith('until:'):
            until_string = qualifier.removeprefix('until:').strip()
            try:
                until = datetime.strptime(until_string, TIME_FORMAT)
            except ValueError:
                _abort(f'Unparseable until-date "{until_string}" in '
                       f'{recurring_path} (expected YYYY-MM-DD)')
            if today.date() > until.date():
                continue
        items.append(f'- [ ] {item}')
    if not items:
        return ''
    return '**Recurring**\n' + '\n'.join(items) + '\n---\n'


def main(args):

    thought_of_the_day = choice(OBLIQUE_STRATEGIES)

    if not args.date:
        today = datetime.today()
        today_string = today.strftime(TIME_FORMAT)
    else:
        today_string = args.date
        try:
            today = datetime.strptime(today_string, TIME_FORMAT)
        except ValueError as e:
            _abort(e.args[0])

    paths = build_paths(args.vault, today_string)
    _check_nothing_is_in_the_way(paths)
    # Rendered up-front so a malformed entry aborts before a single byte is written
    recurring_tasks_section = _recurring_tasks_section(paths['vault_path'].system_path, today)

    with paths['daily_note_index_path'].system_path.open('a') as f:
        f.write(f'\n* [[{paths["daily_note_path"].inner_path}|'
                f'{paths["daily_note_path"].bare_note_name()}]]')
        LOGGER.info(f'Added a link to today\'s Daily Note in {paths["daily_note_index_path"]}')

    with paths['daily_note_path'].system_path.open('a') as f:
        f.write(f'[[{paths["todo_path"].inner_path}|TODO note]]\n')
        f.write(f'Today\'s thought: {thought_of_the_day}\n')
        LOGGER.info(f'Created {paths["daily_note_path"].inner_path}')

    with paths["todo_path"].system_path.open('a') as f:
        f.write(f'[[{paths["daily_note_path"].inner_path}|Main Daily Note]]\n')
        prior_note = ObsidianPath.build_from_system_path(
            _random_prior_note_path(paths["vault_path"].system_path))
        f.write(f'A random prior note. Review it for refiling or expansion: '
                f'"[[{prior_note.inner_path}|{prior_note.bare_note_name()}]]"\n')
        f.write(paths["template_path"].system_path.read_text())
        f.write('\n')
        f.write('---\n')
        f.write(recurring_tasks_section)
        # TODO - parse previous day's TODO's and add any uncompleted ones in here
        f.write('**Personal**\n- [ ] \n---\n')
        f.write('**Work**\n- [ ] \n---\n')
        f.write('**Week-scale Tasks**\n- [ ] \n---\n')
        f.write('# Data\n\n```\ngmail:\n  start-count: \n  end-count: \nprotonmail:\n  start-count: \n  end-count: \n```\n---\n')
        f.write('\n#TODO')
        LOGGER.info(f'Created {paths["todo_path"].inner_path}')

    open_file(args.vault, paths["todo_path"])
    # The previous TODO note goes beside today's, to carry leftovers across from. Today's
    # is opened again afterwards because the pane opened last is the one that takes focus.
    previous_todo = most_recent_todo_before(args.vault, today_string)
    if previous_todo:
        open_file(args.vault, previous_todo, new_pane=True)
        open_file(args.vault, paths["todo_path"])

    # Unstar all TODOs except the most-recent previous one...
    for starred_todo in get_bookmarked_todos_in_date_order(Path(args.vault))[:-1]:
        LOGGER.info(f'DEBUG - unstarring {starred_todo}')
        unbookmark_file(starred_todo.obsidian_path)
    # ...and bookmark today's
    bookmark_file(paths["todo_path"])

    LOGGER.info('Creating/updating the Project Overview page')
    with open(paths['project_root'].system_path.joinpath('Overview.md'), 'w') as f:
        f.write(text_of_overview(
            paths['project_root'],
            ['Overview', 'Someday or Maybe', 'README']
        ))

def _random_prior_note_path(vault_path: Path) -> Path:
    found_note = choice([note for note in vault_path.glob('**/*.md') if
                         note.parts[1] != 'Templates' and
                         # Filter out TODO notes
                         not(len(note.parts) > 2 and note.parts[2] == 'Daily TODOs') and
                         # Filter out Comms
                         not(len(note.parts) > 1 and note.parts[1] == 'Comms') and
                         # Filter out daily notes
                         not(len(note.parts) > 1 and note.parts[1] == 'Daily Notes')])
    # Debug logging here because it's not filtering out the daily todo notes and I'd like to know why :P
    LOGGER.info(f'Found note: {found_note}')
    return found_note

def _is_weekend(d: datetime):
    return d.isoweekday() in (6, 7)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', default='scubbo-vault',
                        help='Name of the vault (vault\'s root directory is expected to be a sibling to this path)')
    parser.add_argument('--date', help='Optional argument that allows operation of the script as if today\'s date was different. Format YYYY-MM-DD')
    main(parser.parse_args())
