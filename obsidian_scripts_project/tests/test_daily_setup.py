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
        with patch.object(daily_setup, 'open_file') as opened, \
                patch.object(daily_setup, 'stderr', reported_errors), \
                redirect_stdout(StringIO()):
            self.opened = opened
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

    def todo_contents(self):
        return self.vault_path \
            .joinpath('GTD', 'Daily TODOs', f'Todo - {DATE_WITHOUT_NOTES}.md').read_text()

    def test_todo_note_includes_the_template(self):
        template_text = self.vault_path \
            .joinpath('Templates', '2025', 'Morning Routine.md').read_text()

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertIn(template_text, self.todo_contents())

    def notes_opened(self):
        """Each `open_file` call as (note, whether it asked for a pane of its own)."""
        return [(call.args[1].inner_path, call.kwargs.get('in_split', False))
                for call in self.opened.call_args_list]

    def test_shows_the_previous_todo_note_beside_todays_and_keeps_focus_on_todays(self):
        self.given_todo_notes('Todo - 2025-06-06', 'Todo - 2025-06-10')

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        today = f'GTD/Daily TODOs/Todo - {DATE_WITHOUT_NOTES}'
        self.assertEqual(self.notes_opened(),
                         [(today, False),
                          ('GTD/Daily TODOs/Todo - 2025-06-10', True),
                          (today, False)])

    def test_opens_only_todays_note_when_no_earlier_one_exists(self):
        self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertEqual(self.notes_opened(),
                         [(f'GTD/Daily TODOs/Todo - {DATE_WITHOUT_NOTES}', False)])

    def test_todo_note_has_no_recurring_section_without_a_recurring_tasks_note(self):
        exit_code, reported_errors = self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertIsNone(exit_code)
        self.assertEqual(reported_errors, '')
        self.assertNotIn('**Recurring**', self.todo_contents())

    def test_links_the_random_prior_note_without_its_extension(self):
        self.run_daily_setup(DATE_WITHOUT_NOTES)

        prior_note_line, = [line for line in self.todo_contents().splitlines()
                            if line.startswith('A random prior note')]
        self.assertRegex(prior_note_line, r'"\[\[[^\]|]+\|[^\]|]+\]\]"')
        self.assertNotIn('.md', prior_note_line)


class TestRecurringTasks(DailySetupTestCase):
    """`GTD/Recurring Tasks.md` lists tasks that every day's TODO note should carry.
    An item may limit its own lifetime with a `| until: YYYY-MM-DD` qualifier."""

    todo_contents = TestDailySetup.todo_contents

    def given_recurring_tasks(self, text):
        self.vault_path.joinpath('GTD', 'Recurring Tasks.md').write_text(text)

    def test_recurring_tasks_appear_as_checkboxes_in_the_recurring_section(self):
        self.given_recurring_tasks('- Read a chapter of Crafting Interpreters\n')

        exit_code, reported_errors = self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertIsNone(exit_code)
        self.assertEqual(reported_errors, '')
        self.assertIn('**Recurring**\n- [ ] Read a chapter of Crafting Interpreters\n---\n',
                      self.todo_contents())

    def test_recurring_section_comes_before_the_personal_section(self):
        self.given_recurring_tasks('- Read a chapter of Crafting Interpreters\n')

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        contents = self.todo_contents()
        self.assertLess(contents.index('**Recurring**'), contents.index('**Personal**'))

    def test_expired_items_are_left_out(self):
        self.given_recurring_tasks('- Water the plants | until: 2025-06-10\n'
                                   '- Read a chapter of Crafting Interpreters\n')

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertNotIn('Water the plants', self.todo_contents())
        self.assertIn('Read a chapter of Crafting Interpreters', self.todo_contents())

    def test_an_item_is_included_on_its_until_day(self):
        self.given_recurring_tasks('- Water the plants | until: 2025-06-11\n')

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertIn('- [ ] Water the plants\n', self.todo_contents())
        self.assertNotIn('until', self.todo_contents())

    def test_non_bullet_lines_are_ignored(self):
        self.given_recurring_tasks('# Recurring tasks\n'
                                   '\n'
                                   'Anything bulleted below gets added to each day.\n'
                                   '* Read a chapter of Crafting Interpreters\n')

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        contents = self.todo_contents()
        self.assertIn('- [ ] Read a chapter of Crafting Interpreters\n', contents)
        self.assertNotIn('Anything bulleted below', contents)

    def test_all_items_expired_leaves_no_recurring_section(self):
        self.given_recurring_tasks('- Water the plants | until: 2025-06-01\n')

        self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertNotIn('**Recurring**', self.todo_contents())

    def test_unparseable_until_date_aborts_before_anything_is_written(self):
        self.given_recurring_tasks('- Water the plants | until: June 10th\n')
        index_before = self.index_contents()
        notes_before = self.notes_in_vault()

        exit_code, reported_errors = self.run_daily_setup(DATE_WITHOUT_NOTES)

        self.assertEqual(exit_code, 1)
        self.assertIn('Recurring Tasks', reported_errors)
        self.assertEqual(self.index_contents(), index_before)
        self.assertEqual(self.notes_in_vault(), notes_before)
