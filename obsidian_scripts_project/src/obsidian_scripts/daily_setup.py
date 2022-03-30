#!/usr/bin/env python3

import argparse
import os
import shutil
import urllib.parse

from datetime import datetime, timedelta
from pathlib import Path
from random import choice
from sys import exit

from .constants import OBLIQUE_STRATEGIES, TIME_FORMAT
from .obsidian_commands import open_file, star_unstar_note_by_system_path
from .path_utils import build_paths, system_path_to_obsidian_path, system_path_to_bare_note_name


def main(args):

    if not args.date:
        today = datetime.today()
        today_string = today.strftime(TIME_FORMAT)
    else:
        today_string = args.date
        try:
            today = datetime.strptime(today_string, TIME_FORMAT)
        except ValueError as e:
            print(e.args[0])
            exit(1)

    paths = build_paths(args.vault, today_string)
    if not paths["vault_path"].exists():
        print(f'Vault does not exist at path {paths["vault_path"]}')
        exit(1)

    with paths['daily_note_index_path'].open('a') as f:
        f.write(f'\n* [[{system_path_to_obsidian_path(paths["daily_note_path"])}|'
                f'{system_path_to_bare_note_name(paths["daily_note_path"])}]]')
        print(f'Added a link to today\'s Daily Note in {paths["daily_note_index_path"]}')

    if paths['daily_note_path'].exists():
        print(f'Daily note path ({paths["daily_note_path"]}) already exists')
        exit(1)

    with paths['daily_note_path'].open('a') as f:
        f.write(f'# Daily note for {today_string}\n')
        f.write(f'[[{system_path_to_obsidian_path(paths["todo_path"])}|TODO note]]\n')
        f.write(f'Today\'s thought: {choice(OBLIQUE_STRATEGIES)}')
        print(f'Created {paths["daily_note_path"]}')

    if paths["todo_path"].exists():
        print(f'Target path ({paths["todo_path"]}) already exists.')
        exit(1)

    with paths["todo_path"].open('a') as f:
        f.write(f'[[{system_path_to_obsidian_path(paths["daily_note_path"])}|Main Daily Note]]\n')
        f.write(paths["template_path"].read_text())
        f.write('\n')
        f.write('---\n')
        # TODO - parse previous day's TODO's and add any uncompleted ones in here
        f.write('- [ ]\n---\n#TODO')
        print(f'Created {paths["todo_path"]}')

    open_file(args.vault, paths["todo_path"])
    star_unstar_note_by_system_path(args.vault, paths["todo_path"])
    # Unstar yesterday's TODO note.
    # TODO - search back for "preceding existing note" rather than assuming yesterday's exists
    star_unstar_note_by_system_path(args.vault, paths["previous_todo_path"])


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