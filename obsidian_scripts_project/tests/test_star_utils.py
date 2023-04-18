# TODO - fixture to add `src.obsidian_scripts` to `sys.path`
# (probably by using `conftest.py`)
import src.obsidian_scripts.star_utils as star_utils
from unittest import TestCase

from pathlib import Path
# TODO - provide this as a test fixture
VAULT_PATH = Path('.').parent.joinpath('testing-vault')


class TestStarUtils(TestCase):

    def test_get_starred(self):
        starred = list(star_utils.get_starred(VAULT_PATH))
        self.assertCountEqual(
            map(lambda todo: todo.title, starred),
            ['Starred TODO note - 2022-04-30',
             'Non-Todo Starred Note',
             'Starred New TODO note - 2022-07-08',
             'Starred Old TODO note - 2022-01-01'])

    def test_get_starred_todos(self):
        starred = list(star_utils.get_starred_todos(VAULT_PATH))
        self.assertCountEqual(
            map(lambda todo: todo.title, starred),
            ['Starred TODO note - 2022-04-30',
             'Starred New TODO note - 2022-07-08',
             'Starred Old TODO note - 2022-01-01'])

    def test_get_starred_todos_in_order(self):
        starred = list(star_utils.get_starred_todos_in_date_order(VAULT_PATH))
        # TODO - I haven't found a way to do equality-checking without
        # converting the `map` to a `list`?
        self.assertEqual(
            list(map(lambda todo: todo.title, starred)),
            ['Starred Old TODO note - 2022-01-01',
             'Starred TODO note - 2022-04-30',
             'Starred New TODO note - 2022-07-08'])
