from os import system

from urllib.parse import quote, urlencode, urlunparse

from .obsidian_path import ObsidianPath


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


def star_unstar_note(vault_name: str, path: ObsidianPath):
    obsidian_uri = urlunparse((
        'obsidian',  # scheme
        'advanced-uri',  # netloc.
        '',  # path
        '',  # params
        urlencode({  # query
            'vault': vault_name,
            'commandname': 'Starred: Star/unstar current file',
            'filepath': path.inner_path,
            'mode': 'append'
        }, quote_via=quote),
        ''))  # fragment
    command = f'open "{obsidian_uri}"'  # TODO - Mac-specific
    system(command)
    print(f'Star/Unstarred {path.system_path}')
