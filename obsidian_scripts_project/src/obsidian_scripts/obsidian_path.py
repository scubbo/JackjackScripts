from dataclasses import dataclass
from os import sep
from pathlib import Path


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
        return self.system_path[:str(self.system_path).index(self.inner_path)]

    @staticmethod
    def build_from_system_path(path: Path) -> 'ObsidianPath':
        return ObsidianPath(path, sep.join(path.parts[1:])[:-len(path.suffix)])

    @staticmethod
    def build_from_obsidian_path(obs_path: str, vault_path: Path) -> 'ObsidianPath':
        return ObsidianPath(Path(f'{vault_path.parts[:-1]}{sep}{obs_path}.md'), obs_path)
