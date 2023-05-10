import json
import pathlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

from .obsidian_path import ObsidianPath


@dataclass
class Bookmark:
    obsidian_path: ObsidianPath
    title: str


def get_bookmarks(
            vault_path: Path,
            filter_func: Callable[[Dict[str, Any]], bool] = lambda _: True)\
        -> Iterable[Bookmark]:

    bookmark_info = json.loads(vault_path.joinpath('.obsidian').joinpath('bookmarks.json').read_text())
    # Path construction is a little weird - the data within the JSON for Bookmarks
    # is a path relative to the the vault root, but includes the `.md` extension - hence the [:-3]
    return map(
        lambda json_item: Bookmark(
            obsidian_path=ObsidianPath.build_from_obsidian_path(json_item['path'][:-3],
                                                  vault_path),
            title=pathlib.Path(json_item['path']).name[:-3]
        ),
        filter(filter_func,
        # On 2023-03-29, Obsidian launched "Bookmarks" - https://forum.obsidian.md/t/obsidian-release-v1-2-7/59004 -
        # replacing the Starred plugin. The migration is reasonably seamless; but since bookmarks can refer to many
        # different types of content but this logic should only refer to files, we filter to just those.
        filter(lambda bookmark: bookmark['type'] == 'file', bookmark_info['items'])))


def get_bookmarked_todos(vault_path: Path) -> Iterable[Bookmark]:
    return get_bookmarks(vault_path, lambda item: item['path'].startswith('GTD/Daily TODOs'))


def get_bookmarked_todos_in_date_order(vault_path: Path) -> Iterable[Bookmark]:
    return sorted(get_bookmarked_todos(vault_path), key=_get_date_for_todo)


def _get_date_for_todo(todo: Bookmark) -> date:
    return date.fromisoformat(todo.title[-10:])
