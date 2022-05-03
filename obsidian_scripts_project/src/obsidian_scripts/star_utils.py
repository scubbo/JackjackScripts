import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

from .obsidian_path import ObsidianPath


@dataclass
class StarredItem:
    obsidian_path: ObsidianPath


def get_starred(
            vault_path: Path,
            filter_func: Callable[[Dict[str, Any]], bool] = lambda _: True)\
        -> Iterable[StarredItem]:

    starred_info = json.loads(vault_path.joinpath('.obsidian').joinpath('starred.json').read_text())
    # Path construction is a little weird - the data within the JSON for Starred Items
    # is a path relative to the the vault root, but includes the `.md` extension - hence the [:-3]
    return map(
        lambda json_item: StarredItem(
            ObsidianPath.build_from_obsidian_path(json_item['path'][:-3],
                                                  vault_path)),
        filter(filter_func, starred_info['items']))


def get_starred_todos(vault_path: Path) -> Iterable[StarredItem]:
    return get_starred(vault_path, lambda item: item['path'].startswith('GTD/Daily TODOs'))


def get_starred_todos_in_date_order(vault_path: Path) -> Iterable[StarredItem]:
    return sorted(get_starred_todos(vault_path), key=_get_date_for_todo)


def _get_date_for_todo(todo: StarredItem) -> date:
    return date.fromisoformat(todo.obsidian_path.inner_path[-10:])
