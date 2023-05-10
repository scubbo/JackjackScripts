#!/usr/bin/env python3

import argparse
import logging

from datetime import datetime
from pathlib import Path
from random import choice
from sys import stdout, exit

from .constants import OBLIQUE_STRATEGIES, TIME_FORMAT
from .obsidian_commands import open_file, bookmark_file, unbookmark_file
from .path_utils import build_paths
from .bookmark_utils import get_bookmarked_todos_in_date_order


logging.basicConfig(stream=stdout, level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def main(args):

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
        f.write(f'# Daily note for {today_string}\n')
        f.write(f'[[{paths["todo_path"].inner_path}|TODO note]]\n')
        f.write(f'Today\'s thought: {choice(OBLIQUE_STRATEGIES)}')
        LOGGER.info(f'Created {paths["daily_note_path"].inner_path}')

    if paths["todo_path"].system_path.exists():
        LOGGER.info(f'Target path ({paths["todo_path"]}) already exists.')
        exit(1)

    with paths["todo_path"].system_path.open('a') as f:
        f.write(f'[[{paths["daily_note_path"].inner_path}|Main Daily Note]]\n')
        f.write(paths["template_path"].system_path.read_text())
        f.write('\n')
        f.write('---\n')
        # TODO - parse previous day's TODO's and add any uncompleted ones in here
        f.write('**Personal**\n- [ ] \n---\n')
        f.write('**Work**\n- [ ] \n---\n')
        f.write('**Week-scale Tasks**\n- [ ] \n---\n')
        f.write('\n#TODO')
        LOGGER.info(f'Created {paths["todo_path"].inner_path}')

    open_file(args.vault, paths["todo_path"])
    # Unstar all TODOs except the most-recent previous one...
    for starred_todo in get_bookmarked_todos_in_date_order(Path(args.vault))[:-1]:
        LOGGER.info(f'DEBUG - unstarring {starred_todo}')
        unbookmark_file(starred_todo.obsidian_path)
    # ...and bookmark today's
    bookmark_file(paths["todo_path"])


def _is_weekend(d: datetime):
    return d.isoweekday() in (6, 7)


def _is_friday(d: datetime):
    return d.isoweekday() == 5


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', default='scubbo-vault',
                        help='Name of the vault (vault\'s root directory is expected to be a sibling to this path)')
    parser.add_argument('--date', help='Optional argument that allows operation of the script as if today\'s date was different. Format YYYY-MM-DD')
    main(parser.parse_args())
