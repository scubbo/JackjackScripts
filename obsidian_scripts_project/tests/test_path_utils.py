import src.obsidian_scripts.path_utils as path_utils

from vault_fixture import TemporaryVaultTestCase, VAULT_NAME

TODAY = '2026-08-15'
TODOS = 'GTD/Daily TODOs'


class TestMostRecentTodoBefore(TemporaryVaultTestCase):

    def test_finds_the_latest_earlier_note(self):
        self.given_todo_notes('Todo - 2026-08-10', 'Todo - 2026-08-14', 'Todo - 2026-08-12')

        found = path_utils.most_recent_todo_before(VAULT_NAME, TODAY)

        self.assertEqual(found.inner_path, f'{TODOS}/Todo - 2026-08-14')

    def test_skips_over_days_that_have_no_note(self):
        """Weekends are routinely skipped, so the previous note is rarely yesterday's."""
        self.given_todo_notes('Todo - 2026-08-07', 'Todo - 2026-08-03')

        found = path_utils.most_recent_todo_before(VAULT_NAME, '2026-08-10')

        self.assertEqual(found.inner_path, f'{TODOS}/Todo - 2026-08-07')

    def test_ignores_the_given_day_and_later_ones(self):
        self.given_todo_notes('Todo - 2026-08-14', f'Todo - {TODAY}', 'Todo - 2026-08-16')

        found = path_utils.most_recent_todo_before(VAULT_NAME, TODAY)

        self.assertEqual(found.inner_path, f'{TODOS}/Todo - 2026-08-14')

    def test_ignores_conflicted_copies(self):
        """Dropbox leaves these alongside the originals, and their names carry two dates."""
        self.given_todo_notes('Todo - 2026-08-10',
                              'Todo - 2026-08-14 (conflict 2026-08-14-16-46-58)')

        found = path_utils.most_recent_todo_before(VAULT_NAME, TODAY)

        self.assertEqual(found.inner_path, f'{TODOS}/Todo - 2026-08-10')

    def test_finds_nothing_when_every_note_is_later(self):
        self.given_todo_notes(f'Todo - {TODAY}', 'Todo - 2026-08-16')

        self.assertIsNone(path_utils.most_recent_todo_before(VAULT_NAME, TODAY))

    def test_finds_nothing_in_a_vault_without_todo_notes(self):
        self.assertIsNone(path_utils.most_recent_todo_before(VAULT_NAME, TODAY))
