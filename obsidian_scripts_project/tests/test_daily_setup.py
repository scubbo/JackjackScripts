import src.obsidian_scripts.daily_setup as daily_setup

from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from vault_fixture import TemporaryVaultTestCase, VAULT_NAME

# A weekday, so that `build_paths` looks for the weekday template that the fixture provides
DATE_WITHOUT_NOTES = '2025-06-11'
# The fixture already contains `Daily Notes/2025-10-30.md`
DATE_WITH_EXISTING_DAILY_NOTE = '2025-10-30'


class DailySetupTestCase(TemporaryVaultTestCase):

    def run_daily_setup(self, date, vault=VAULT_NAME):
        """Returns the exit code (None if the run completed) and anything sent to stderr."""
        reported_errors = StringIO()
        # `open_file` shells out to `open obsidian://...`, which would raise a real Obsidian window
        with patch.object(daily_setup, 'open_file'), \
                patch.object(daily_setup, 'stderr', reported_errors), \
                redirect_stdout(StringIO()):
            try:
                daily_setup.main(Namespace(vault=vault, date=date))
            except SystemExit as abort:
                return abort.code, reported_errors.getvalue()
        return None, reported_errors.getvalue()

    def index_contents(self):
        return self.vault_path.joinpath('Daily Note Index.md').read_text()

    def notes_in_vault(self):
        return sorted(str(note.relative_to(self.vault_path))
                      for note in self.vault_path.glob('**/*.md'))


class TestPreconditions(DailySetupTestCase):
    """A single click of an Obsidian button is easy to repeat by accident, so a run that
    cannot complete must leave the vault exactly as it found it."""

    def test_existing_daily_note_is_reported_on_stderr(self):
        exit_code, reported_errors = self.run_daily_setup(DATE_WITH_EXISTING_DAILY_NOTE)
        self.assertEqual(exit_code, 1)
        self.assertIn(DATE_WITH_EXISTING_DAILY_NOTE, reported_errors)

    def test_existing_daily_note_does_not_add_an_index_entry(self):
        index_before = self.index_contents()
        self.run_daily_setup(DATE_WITH_EXISTING_DAILY_NOTE)
        self.assertEqual(self.index_contents(), index_before)

    def test_existing_daily_note_creates_no_notes(self):
        notes_before = self.notes_in_vault()
        self.run_daily_setup(DATE_WITH_EXISTING_DAILY_NOTE)
        self.assertEqual(self.notes_in_vault(), notes_before)

    def test_missing_template_is_reported_before_anything_is_written(self):
        self.vault_path.joinpath('Templates', '2025', 'Morning Routine.md').unlink()
        index_before = self.index_contents()
        notes_before = self.notes_in_vault()

        exit_code, reported_errors = self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertEqual(exit_code, 1)
        self.assertIn('Morning Routine', reported_errors)
        self.assertEqual(self.index_contents(), index_before)
        self.assertEqual(self.notes_in_vault(), notes_before)

    def test_absent_vault_is_reported_on_stderr(self):
        exit_code, reported_errors = self.run_daily_setup(DATE_WITHOUT_NOTES, vault='no-such-vault')
        self.assertEqual(exit_code, 1)
        self.assertIn('no-such-vault', reported_errors)

    def test_unparseable_date_is_reported_on_stderr(self):
        exit_code, reported_errors = self.run_daily_setup('11th June')
        self.assertEqual(exit_code, 1)
        self.assertNotEqual(reported_errors, '')


class TestDailySetup(DailySetupTestCase):

    def test_creates_the_daily_note_and_todo_note(self):
        exit_code, reported_errors = self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertIsNone(exit_code)
        self.assertEqual(reported_errors, '')
        self.assertTrue(self.vault_path
                        .joinpath('Daily Notes', f'{DATE_WITHOUT_NOTES}.md').exists())
        self.assertTrue(self.vault_path
                        .joinpath('GTD', 'Daily TODOs', f'Todo - {DATE_WITHOUT_NOTES}.md').exists())

    def test_links_the_daily_note_from_the_index(self):
        self.run_daily_setup(DATE_WITHOUT_NOTES)
        self.assertIn(f'* [[Daily Notes/{DATE_WITHOUT_NOTES}|{DATE_WITHOUT_NOTES}]]',
                      self.index_contents())

    def test_todo_note_includes_the_template(self):
        template_text = self.vault_path \
            .joinpath('Templates', '2025', 'Morning Routine.md').read_text()

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        todo_text = self.vault_path \
            .joinpath('GTD', 'Daily TODOs', f'Todo - {DATE_WITHOUT_NOTES}.md').read_text()
        self.assertIn(template_text, todo_text)
