import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable


def get_starred(
            vault_path: Path,
            filter_func: Callable[[Dict[str, Any]], bool] = lambda _: True)\
        -> Iterable[Dict[str, Any]]:

    starred_info = json.loads(vault_path.joinpath('.obsidian').joinpath('starred.json').read_text())
    return filter(filter_func, starred_info['items'])


def get_starred_todos(vault_path: Path):
    return get_starred(vault_path, lambda item: item['path'].startswith('GTD/Daily TODOs'))
