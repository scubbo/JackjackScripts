import src.obsidian_scripts.reminders as reminders

from datetime import datetime

from vault_fixture import TemporaryVaultTestCase

TODAY = datetime(2026, 8, 22)

PREAMBLE = ('# Reminders\n'
            '\n'
            'Maintained by the daily setup script - the lines below are parsed.\n'
            'Format: `<reminder date> - <capture date> - <text>`\n'
            '\n')


def reminders_file(live='', sent=''):
    return f'{PREAMBLE}## Live\n\n{live}\n## Sent\n\n{sent}'


class ReminderTestCase(TemporaryVaultTestCase):

    def given_reminders(self, live='', sent=''):
        self.given_reminders_file(reminders_file(live, sent))

    def given_reminders_file(self, contents):
        self.reminders_path = self.vault_path.joinpath('GTD', 'Reminders.md')
        self.reminders_path.write_text(contents)

    def due(self, today=TODAY):
        return reminders.reminders_due(self.vault_path, today)

    def file_contents(self):
        return self.reminders_path.read_text()

    def live_and_sent(self):
        """The file either side of the Sent header, for asserting what moved."""
        live, _, sent = self.file_contents().partition('## Sent')
        return live, sent


class TestReadingReminders(ReminderTestCase):

    def test_a_reminder_dated_before_today_is_due(self):
        self.given_reminders('- 2026-08-20 - 2026-07-01 - Chase the roofer\n')

        due, problems = self.due()

        self.assertEqual(problems, [])
        self.assertEqual([reminder.text for reminder in due], ['Chase the roofer'])

    def test_a_reminder_dated_later_is_not_due(self):
        self.given_reminders('- 2026-09-15 - 2026-07-01 - Book the checkup\n')

        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertEqual(problems, [])

    def test_a_reminder_dated_today_is_due(self):
        """The reminder date is the day it should surface on, so it is inclusive."""
        self.given_reminders('- 2026-08-22 - 2026-07-01 - Chase the roofer\n')

        due, _ = self.due()

        self.assertEqual([reminder.text for reminder in due], ['Chase the roofer'])

    def test_reminder_text_may_contain_the_field_separator(self):
        self.given_reminders('- 2026-08-20 - 2026-07-01 - Chase the roofer - he never called\n')

        due, _ = self.due()

        self.assertEqual([reminder.text for reminder in due],
                         ['Chase the roofer - he never called'])

    def test_non_bullet_lines_are_ignored(self):
        self.given_reminders('Anything bulleted below surfaces on its reminder date.\n'
                             '* 2026-08-20 - 2026-07-01 - Chase the roofer\n')

        due, problems = self.due()

        self.assertEqual(problems, [])
        self.assertEqual([reminder.text for reminder in due], ['Chase the roofer'])

    def test_already_sent_reminders_are_not_sent_again(self):
        self.given_reminders(
            sent='- 2026-08-20 - 2026-07-01 - Chase the roofer | sent: 2026-08-21\n')

        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertEqual(problems, [])

    def test_an_absent_note_is_not_a_problem(self):
        """Most vaults will never have this note, and that must stay unremarkable."""
        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertEqual(problems, [])


class TestUnreadableReminders(ReminderTestCase):
    """A reminder that cannot be read is reported and left live - never dropped."""

    def test_an_unparseable_date_is_reported(self):
        self.given_reminders('- June 1st - 2026-07-01 - Renew the passport\n')

        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertEqual(len(problems), 1)
        self.assertIn('June 1st', problems[0])

    def test_a_line_with_too_few_fields_is_reported(self):
        self.given_reminders('- 2026-08-20 - Chase the roofer\n')

        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertEqual(len(problems), 1)
        self.assertIn('Chase the roofer', problems[0])

    def test_a_readable_reminder_survives_an_unreadable_neighbour(self):
        self.given_reminders('- June 1st - 2026-07-01 - Renew the passport\n'
                             '- 2026-08-20 - 2026-07-01 - Chase the roofer\n')

        due, problems = self.due()

        self.assertEqual([reminder.text for reminder in due], ['Chase the roofer'])
        self.assertEqual(len(problems), 1)

    def test_a_missing_live_header_is_reported(self):
        self.given_reminders_file(f'{PREAMBLE}## Sent\n\n')

        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertIn('Live', problems[0])

    def test_a_missing_sent_header_stops_anything_being_sent(self):
        """Injecting a reminder that cannot then be filed would re-send it every day."""
        self.given_reminders_file(
            f'{PREAMBLE}## Live\n\n- 2026-08-20 - 2026-07-01 - Chase the roofer\n')

        due, problems = self.due()

        self.assertEqual(due, [])
        self.assertIn('Sent', problems[0])


class TestRenderingReminders(ReminderTestCase):

    def test_due_reminders_render_as_checkboxes(self):
        self.given_reminders('- 2026-08-20 - 2026-07-01 - Chase the roofer\n'
                             '- 2026-08-21 - 2026-07-01 - Renew the passport\n')

        due, _ = self.due()

        self.assertEqual(reminders.section_for_todo_note(due),
                         '**Reminders**\n'
                         '- [ ] Chase the roofer\n'
                         '- [ ] Renew the passport\n'
                         '---\n')

    def test_nothing_due_renders_no_section(self):
        self.assertEqual(reminders.section_for_todo_note([]), '')

    def test_no_problems_renders_no_banner(self):
        self.assertEqual(reminders.banner_for_problems([]), '')

    def test_a_banner_quotes_the_problem_and_points_at_the_note(self):
        banner = reminders.banner_for_problems(['Unparseable reminder date "June 1st"'])

        self.assertTrue(banner.startswith('> [!error]'))
        self.assertIn('June 1st', banner)
        self.assertIn('GTD/Reminders.md', banner)


class TestFilingSentReminders(ReminderTestCase):

    def test_a_sent_reminder_moves_under_the_sent_header(self):
        self.given_reminders('- 2026-08-20 - 2026-07-01 - Chase the roofer\n')

        due, _ = self.due()
        reminders.move_to_sent(self.vault_path, due, TODAY)

        live, sent = self.live_and_sent()
        self.assertNotIn('Chase the roofer', live)
        self.assertIn('- 2026-08-20 - 2026-07-01 - Chase the roofer | sent: 2026-08-22', sent)

    def test_a_reminder_that_is_not_due_stays_live(self):
        self.given_reminders('- 2026-08-20 - 2026-07-01 - Chase the roofer\n'
                             '- 2026-09-15 - 2026-07-01 - Book the checkup\n')

        due, _ = self.due()
        reminders.move_to_sent(self.vault_path, due, TODAY)

        live, sent = self.live_and_sent()
        self.assertIn('Book the checkup', live)
        self.assertNotIn('Book the checkup', sent)

    def test_the_original_bullet_marker_is_kept(self):
        self.given_reminders('* 2026-08-20 - 2026-07-01 - Chase the roofer\n')

        due, _ = self.due()
        reminders.move_to_sent(self.vault_path, due, TODAY)

        self.assertIn('* 2026-08-20 - 2026-07-01 - Chase the roofer | sent: 2026-08-22',
                      self.live_and_sent()[1])

    def test_everything_else_in_the_note_is_left_exactly_as_it_was(self):
        """The note carries prose that Jack wrote, so lines are moved rather than a
        parsed model being re-rendered over the top of them."""
        self.given_reminders('Commentary that belongs to Jack, not to the script.\n'
                             '- 2026-08-20 - 2026-07-01 - Chase the roofer\n'
                             '- 2026-09-15 - 2026-07-01 - Book the checkup\n',
                             '- 2026-01-01 - 2025-12-01 - Older one | sent: 2026-01-01\n')

        due, _ = self.due()
        reminders.move_to_sent(self.vault_path, due, TODAY)

        self.assertEqual(self.file_contents(), reminders_file(
            'Commentary that belongs to Jack, not to the script.\n'
            '- 2026-09-15 - 2026-07-01 - Book the checkup\n',
            '- 2026-01-01 - 2025-12-01 - Older one | sent: 2026-01-01\n'
            '- 2026-08-20 - 2026-07-01 - Chase the roofer | sent: 2026-08-22\n'))

    def test_several_reminders_due_at_once_all_move_to_the_right_lines(self):
        """Line indices are recorded while reading and spent while filing, so removing
        lines one at a time would slide the later ones out from under their own indices.
        The not-yet-due line sits between two due ones, where such a slip would land."""
        self.given_reminders('- 2026-08-18 - 2026-07-01 - Renew the parking permit\n'
                             '- 2026-08-19 - 2026-07-01 - Chase the roofer\n'
                             '- 2026-09-15 - 2026-07-01 - Book the checkup\n'
                             '- 2026-08-20 - 2026-07-01 - Order more coffee\n')

        due, _ = self.due()
        reminders.move_to_sent(self.vault_path, due, TODAY)

        self.assertEqual(self.file_contents(), reminders_file(
            '- 2026-09-15 - 2026-07-01 - Book the checkup\n',
            '- 2026-08-18 - 2026-07-01 - Renew the parking permit | sent: 2026-08-22\n'
            '- 2026-08-19 - 2026-07-01 - Chase the roofer | sent: 2026-08-22\n'
            '- 2026-08-20 - 2026-07-01 - Order more coffee | sent: 2026-08-22\n'))

    def test_filing_nothing_leaves_the_note_untouched(self):
        self.given_reminders('- 2026-09-15 - 2026-07-01 - Book the checkup\n')
        before = self.file_contents()

        reminders.move_to_sent(self.vault_path, [], TODAY)

        self.assertEqual(self.file_contents(), before)
