import json
import logging

from datetime import datetime
from os import system

from urllib.parse import quote, urlencode, urlunparse

from .obsidian_path import ObsidianPath

LOGGER = logging.getLogger(__name__)

def open_file(vault_name: str, path: ObsidianPath):
    # TODO - extract
    obsidian_uri = urlunparse((
        'obsidian',
        'advanced-uri',
        '',
        '',
        urlencode({
            'vault': vault_name,
            'filepath': path.inner_path
        }, quote_via=quote),
        ''))
    command = f'open "{obsidian_uri}"'
    system(command)
    print(f'Opened {path.system_path}')


def bookmark_file(path: ObsidianPath):
    vault_path = path.vault_path()
    bookmark_info_file = vault_path.joinpath('.obsidian').joinpath('bookmarks.json')
    bookmark_info = json.loads(bookmark_info_file.read_text())
    if path.inner_path not in [item['path'] for item in bookmark_info['items']]:
        bookmark_info['items'].append({
            'type': 'file',
            'path': path.inner_path,
            'ctime': int(datetime.now().timestamp()*1000)
        })
        bookmark_info_file.write_text(json.dumps(bookmark_info))
    else:
        LOGGER.warning(f'{path.inner_path} is already bookmarked')


def unbookmark_file(path: ObsidianPath):
    vault_path = path.vault_path()
    bookmark_info_file = vault_path.joinpath('.obsidian').joinpath('bookmarks.json')
    bookmark_info = json.loads(bookmark_info_file.read_text())
    for idx, elem in enumerate(bookmark_info['items']):
        if elem['path'] == path.inner_path:
            bookmark_info['items'].pop(idx)
            bookmark_info_file.write_text(json.dumps(bookmark_info))
            break
    else:
        LOGGER.warning(f'Could not unbookmark {path.inner_path}')
