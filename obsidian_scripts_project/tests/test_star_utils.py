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
        assert len(starred) == 2
        self.assertCountEqual(
            map(lambda x: x['title'], starred),
            ['Starred TODO note', 'Non-Todo Starred Note'])

    def test_get_starred_todos(self):
        starred = list(star_utils.get_starred_todos(VAULT_PATH))
        assert len(starred) == 1
        self.assertCountEqual(
            map(lambda x: x['title'], starred),
            ['Starred TODO note'])
