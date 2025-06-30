#!/usr/bin/env python3

import argparse
import logging
import subprocess

from datetime import datetime
from pathlib import Path
from random import choice
from sys import stdout, exit

from .constants import OBLIQUE_STRATEGIES, TIME_FORMAT
from .obsidian_commands import open_file, bookmark_file, unbookmark_file
from .path_utils import build_paths
from .bookmark_utils import get_bookmarked_todos_in_date_order
from .project_summary import text_of_overview


logging.basicConfig(stream=stdout, level=logging.INFO)
LOGGER = logging.getLogger(__name__)

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
            LOGGER.info(e.args[0])
            exit(1)

    paths = build_paths(args.vault, today_string)
    if not paths["vault_path"].system_path.exists():
        LOGGER.info(f'Vault does not exist at path {paths["vault_path"]}')
        exit(1)

    with paths['daily_note_index_path'].system_path.open('a') as f:
        f.write(f'\n* [[{paths["daily_note_path"].inner_path}|'
                f'{paths["daily_note_path"].bare_note_name()}]]')
        LOGGER.info(f'Added a link to today\'s Daily Note in {paths["daily_note_index_path"]}')

    if paths['daily_note_path'].system_path.exists():
        LOGGER.info(f'Daily note path ({paths["daily_note_path"]}) already exists')
        exit(1)

    with paths['daily_note_path'].system_path.open('a') as f:
        f.write(f'[[{paths["todo_path"].inner_path}|TODO note]]\n')
        f.write(f'Today\'s thought: {thought_of_the_day}\n')
        f.write(f'# Daily Tracking\n## Who I Saw\n\n## What I Learned\n\n## What I Built\n\n## How I Helped\n')
        LOGGER.info(f'Created {paths["daily_note_path"].inner_path}')

    if paths["todo_path"].system_path.exists():
        LOGGER.info(f'Target path ({paths["todo_path"]}) already exists.')
        exit(1)

    with paths["todo_path"].system_path.open('a') as f:
        f.write(f'[[{'/'.join(paths["daily_note_path"].inner_path.split('/')[1:])}|Main Daily Note]]\n')
        prior_note_path = _random_prior_note_path(paths["vault_path"].system_path)
        prior_note_title = prior_note_path.stem
        f.write(f'A random prior note. Review it for refiling or expansion: "[[{prior_note_path}|{prior_note_title}]]"\n')
        f.write(paths["template_path"].system_path.read_text())
        f.write('\n')
        f.write('---\n')
        # TODO - parse previous day's TODO's and add any uncompleted ones in here
        f.write('**Personal**\n- [ ] \n---\n')
        f.write('**Work**\n- [ ] \n---\n')
        f.write('**Week-scale Tasks**\n- [ ] \n---\n')
        f.write('# Data\n\n```\ngmail:\n  start-count: \n  end-count: \nprotonmail:\n  start-count: \n  end-count: \n```\n---\n')
        f.write('\n#TODO')
        LOGGER.info(f'Created {paths["todo_path"].inner_path}')

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
    return choice([note for note in vault_path.glob('**/*.md') if note.parts[0] != 'Templates'])

def _is_weekend(d: datetime):
    return d.isoweekday() in (6, 7)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', default='scubbo-vault',
                        help='Name of the vault (vault\'s root directory is expected to be a sibling to this path)')
    parser.add_argument('--date', help='Optional argument that allows operation of the script as if today\'s date was different. Format YYYY-MM-DD')
    main(parser.parse_args())
