from os import system
from pathlib import Path

from urllib.parse import quote, urlencode, urlunparse

from .path_utils import system_path_to_obsidian_path


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
