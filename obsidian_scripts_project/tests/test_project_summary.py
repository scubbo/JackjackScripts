import src.obsidian_scripts.project_summary as project_summary
from src.obsidian_scripts.path_utils import ObsidianPath
from unittest import TestCase

from pathlib import Path
VAULT_PATH = Path('.').parent.joinpath('testing-vault')
OBSIDIAN_PATH_TO_PROJECTS = ObsidianPath(VAULT_PATH.joinpath('GTD').joinpath('Projects'), 'GTD/Projects')

class TestProjectSummary(TestCase):
  def test_get_current_projects(self):
    actives = project_summary.list_active_projects(
      OBSIDIAN_PATH_TO_PROJECTS,
      ['inactive-project'])
    self.assertCountEqual(
      actives,
      ['abc', 'def']
    )

  def test_text_of_overview(self):
    overview_text = project_summary.text_of_overview(OBSIDIAN_PATH_TO_PROJECTS, ['inactive-project'])
    assert overview_text == '# abc\n![[abc#Next Steps]]\n\n# def\n![[def#Next Steps]]\n'
