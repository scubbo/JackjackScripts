import logging
from dataclasses import dataclass
from os import sep
from pathlib import Path

LOGGER = logging.getLogger(__name__)

@dataclass
class ObsidianPath:
    # Filesystem path
    system_path: Path
    # Path relative to the vault-root, without extension
    inner_path: str

    def bare_note_name(self):
        path = self.system_path
        return path.name[:-len(path.suffix)]

    def vault_path(self):
        ret_val = str(self.system_path.absolute())[:str(self.system_path.absolute()).index(self.inner_path)]
        LOGGER.info(ret_val)
        return ret_val

    @staticmethod
    def build_from_system_path(path: Path) -> 'ObsidianPath':
        return ObsidianPath(path, sep.join(path.parts[1:])[:-len(path.suffix)])

    @staticmethod
    def build_from_obsidian_path(obs_path: str, vault_path: Path) -> 'ObsidianPath':
        # TODO - this could probably be done more neatly with `Path(...).join_path`, but I'm debugging
        return ObsidianPath(Path(f'{sep.join(vault_path.parts + (obs_path,))}.md'), obs_path)
