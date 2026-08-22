import json
import logging

from datetime import datetime
from os import system
from pathlib import Path

from urllib.parse import quote, urlencode, urlunparse

from .obsidian_path import ObsidianPath

LOGGER = logging.getLogger(__name__)

def _advanced_uri(vault_name: str, path: ObsidianPath, in_split: bool) -> str:
    parameters = {
        'vault': vault_name,
        'filepath': path.inner_path
    }
    if in_split:
        # `split-or-focus` puts the note in a pane beside the current one, or focuses the
        # note where it is if it happens to be open already. A plain `split` would stack up
        # another pane every time it ran.
        parameters['openmode'] = 'split-or-focus'
    return urlunparse((
        'obsidian',
        'advanced-uri',
        '',
        '',
        urlencode(parameters, quote_via=quote),
        ''))


def open_file(vault_name: str, path: ObsidianPath, in_split: bool = False):
    command = f'open "{_advanced_uri(vault_name, path, in_split)}"'
    system(command)
    print(f'Opened {path.system_path}')


def _bookmark_entry_path(path: ObsidianPath) -> str:
    """Bookmarks record a vault-relative path that, unlike an ObsidianPath's
    `inner_path`, carries the extension."""
    return f'{path.inner_path}.md'


def bookmark_file(path: ObsidianPath):
    vault_path = Path(path.vault_path())
    bookmark_info_file = vault_path.joinpath('.obsidian').joinpath('bookmarks.json')
    bookmark_info = json.loads(bookmark_info_file.read_text())
    if _bookmark_entry_path(path) not in [item['path'] for item in bookmark_info['items']]:
        bookmark_info['items'].append({
            'type': 'file',
            'path': _bookmark_entry_path(path),
            'ctime': int(datetime.now().timestamp()*1000)
        })
        bookmark_info_file.write_text(json.dumps(bookmark_info))
    else:
        LOGGER.warning(f'{path.inner_path} is already bookmarked')


def unbookmark_file(path: ObsidianPath):
    vault_path = Path(path.vault_path())
    bookmark_info_file = vault_path.joinpath('.obsidian').joinpath('bookmarks.json')
    bookmark_info = json.loads(bookmark_info_file.read_text())
    for idx, elem in enumerate(bookmark_info['items']):
        if elem['path'] == _bookmark_entry_path(path):
            bookmark_info['items'].pop(idx)
            bookmark_info_file.write_text(json.dumps(bookmark_info))
            break
    else:
        LOGGER.warning(f'Could not unbookmark {path.inner_path}')
