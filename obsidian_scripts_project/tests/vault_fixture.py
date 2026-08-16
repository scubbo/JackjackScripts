from os import chdir, getcwd
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from unittest import TestCase

FIXTURE_VAULT = Path('testing-vault')
VAULT_NAME = 'vault'


class TemporaryVaultTestCase(TestCase):
    """Provides a throwaway copy of the testing vault, for tests that write to one.

    Vault paths are resolved relative to the working directory, so each test chdirs into
    a temporary directory that the copy lives in. Working on a copy keeps a partial run
    from leaving marks on the committed fixture.
    """

    def setUp(self):
        self.original_working_directory = getcwd()
        self.temporary_directory = TemporaryDirectory()
        self.vault_path = Path(self.temporary_directory.name).joinpath(VAULT_NAME)
        copytree(FIXTURE_VAULT, self.vault_path)
        chdir(self.temporary_directory.name)

    def tearDown(self):
        chdir(self.original_working_directory)
        self.temporary_directory.cleanup()

    def given_todo_notes(self, *note_names):
        """Adds empty TODO notes to the copied vault, named without their extension."""
        todos_directory = self.vault_path.joinpath('GTD', 'Daily TODOs')
        for note_name in note_names:
            todos_directory.joinpath(f'{note_name}.md').write_text('')
