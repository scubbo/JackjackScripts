from os import system
from pathlib import Path

from urllib.parse import quote, urlencode, urlunparse

from .path_utils import system_path_to_obsidian_path


def open_file(vault_name: str, system_path: Path):
    # TODO - extract
    obsidian_uri = urlunparse((
        'obsidian',
        'advanced-uri',
        '',
        '',
        urlencode({
            'vault': vault_name,
            # TODO - should we simply pass Obsidian Path to these methods?
            # And/or have a "Paths" object that encapsulates both?
            'filepath': system_path_to_obsidian_path(system_path)
        }, quote_via=quote),
        ''))
    command = f'open "{obsidian_uri}"'
    system(command)
    print(f'Opened {system_path}')

def star_unstar_note_by_system_path(vault_name: str, system_path: Path):
    obsidian_uri = urlunparse((
        'obsidian',  # scheme
        'advanced-uri',  # netloc.
        '',  # path
        '',  # params
        urlencode({  # query
            'vault': vault_name,
            'commandname': 'Starred: Star/unstar current file',
            'filepath': system_path_to_obsidian_path(system_path),
            'mode': 'append'
        }, quote_via=quote),
        ''))  # fragment
    command = f'open "{obsidian_uri}"'  # TODO - Mac-specific
    system(command)
    print(f'Star/Unstarred {system_path}')
