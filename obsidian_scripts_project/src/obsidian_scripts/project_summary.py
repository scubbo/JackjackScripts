from .obsidian_path import ObsidianPath

# TODO - order not technically deterministic. Does that matter?
# Not bothering with error-checking that each entry actually _has_ a Next Steps at this point -
# if that's not already obvious at the time of reading the output, the system itself needs improving!
def text_of_overview(
    path_to_root_of_projects: ObsidianPath,
    blocklisted_filenames=['Overview']):
  return '\n'.join([f'# {project_name}\n![[{project_name}#Next Steps]]\n'
   for project_name in list_active_projects(path_to_root_of_projects, blocklisted_filenames)])


def list_active_projects(
    path_to_root_of_projects: ObsidianPath,
    blocklisted_filenames=['Overview']):
  """
  blocklisted_filenames of the form `foo`, not `foo.md`
  """
  return list(
    map(
      lambda path: path.stem,
      filter(
        lambda path: not (path.is_dir() or path.stem in blocklisted_filenames),
        path_to_root_of_projects.system_path.iterdir())))
