import src.obsidian_scripts.obsidian_commands as obsidian_commands
from src.obsidian_scripts.obsidian_path import ObsidianPath

from json import loads
from pathlib import Path
from unittest import TestCase

from vault_fixture import TemporaryVaultTestCase, VAULT_NAME

TODO_NOTE = 'GTD/Daily TODOs/Todo - 2025-06-11.md'


class TestAdvancedUri(TestCase):

    def uri_for(self, new_pane):
        note = ObsidianPath.build_from_system_path(Path(VAULT_NAME).joinpath(TODO_NOTE))
        return obsidian_commands._advanced_uri(VAULT_NAME, note, new_pane)

    def test_addresses_the_note_within_the_vault(self):
        uri = self.uri_for(new_pane=False)
        self.assertTrue(uri.startswith('obsidian://advanced-uri?'))
        self.assertIn(f'vault={VAULT_NAME}', uri)
        self.assertIn('filepath=GTD%2FDaily%20TODOs%2FTodo%20-%202025-06-11', uri)

    def test_asks_for_a_new_pane_only_when_one_is_wanted(self):
        self.assertNotIn('newpane', self.uri_for(new_pane=False))
        self.assertIn('newpane=true', self.uri_for(new_pane=True))


class TestBookmarking(TemporaryVaultTestCase):

    def setUp(self):
        super().setUp()
        self.note = ObsidianPath.build_from_system_path(Path(VAULT_NAME).joinpath(TODO_NOTE))

    def bookmarked_paths(self):
        bookmarks = loads(self.vault_path
                          .joinpath('.obsidian', 'bookmarks.json').read_text())
        return [item['path'] for item in bookmarks['items']]

    def test_bookmarking_records_the_note(self):
        obsidian_commands.bookmark_file(self.note)
        self.assertIn(TODO_NOTE, self.bookmarked_paths())

    def test_bookmarking_leaves_existing_bookmarks_alone(self):
        bookmarks_before = self.bookmarked_paths()
        obsidian_commands.bookmark_file(self.note)
        self.assertEqual(self.bookmarked_paths()[:len(bookmarks_before)], bookmarks_before)

    def test_bookmarking_twice_records_the_note_once(self):
        obsidian_commands.bookmark_file(self.note)

        with self.assertLogs(obsidian_commands.LOGGER, level='WARNING') as reported:
            obsidian_commands.bookmark_file(self.note)

        self.assertEqual(self.bookmarked_paths().count(TODO_NOTE), 1)
        self.assertIn('already bookmarked', reported.output[0])

    def test_unbookmarking_removes_the_note(self):
        obsidian_commands.bookmark_file(self.note)
        obsidian_commands.unbookmark_file(self.note)
        self.assertNotIn(TODO_NOTE, self.bookmarked_paths())

    def test_unbookmarking_a_note_that_was_never_bookmarked_is_reported(self):
        with self.assertLogs(obsidian_commands.LOGGER, level='WARNING') as reported:
            obsidian_commands.unbookmark_file(self.note)

        self.assertIn('Could not unbookmark', reported.output[0])
