#!/usr/bin/env python3

import os, pwd, sys

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zlib import decompress

IGNORED_DIRECTORY_NAMES = ['build', 'env', 'out', 'logs']

@dataclass
class CommitInfo:
  commit_date: datetime

def main(args):
  print(f'Scanning all Git repos under {args.workspace_path}')
  paths_to_search = [Path(args.workspace_path)]
  git_dirs = []

  while paths_to_search:
    path = paths_to_search.pop()
    try:
      candidates = list(path.iterdir())
      if '.git' in [candidate.stem for candidate in candidates]:
        # Found a git directory - do not traverse any further,
        # but add this to git_dirs for later processing
        git_dirs.append(path)
      else:
        paths_to_search += [candidate for candidate in candidates if candidate.is_dir() and candidate.stem not in IGNORED_DIRECTORY_NAMES]
    except PermissionError:
      print(f'PermissionError trying to scan {path}')
      next

  for p in git_dirs:
    branches = {branch_name: get_commit_info(p, branch_name) for branch_name in get_branch_names_in_repo(p)}
    print(f'Repo: {p}')
    for (branch_name, commit_info) in branches.items():
      print(f'\t{branch_name}')
      print(f'\t\tCommit date: {commit_info.commit_date}')
    print()
    # Just testing!
    # TODO next:
    # * List all branches older than given age, prompt to delete
    # * Optionally prompt to delete entire workspace - double-confirm, especially if unpushed commits and/or uncommited changes
    # import sys
    # sys.exit(1)

def get_branch_names_in_repo(repo_root: Path):
  # This can't just be `return p.joinpath('.git', 'refs', 'heads').iterdir(), because if a Git branch name has `/` in it,
  # the directory structure of `heads` will reflect that. Sigh.
  base_path = repo_root.joinpath('.git', 'refs', 'heads')
  return [str(p.relative_to(base_path)) for p in base_path.glob('**/*') if p.is_file()]

# I could have used GitPython for this, but what's the fun in that!? :P
# (More seriously - writing this dependency-free makes it more portable)
def get_commit_info(path, branch_name):
  commit_id = path.joinpath('.git', 'refs', 'heads', branch_name).read_text()[:-1] # Remove newline
  # Note - this assumes that all commits are stored in .git/objects indexed by first two characters, then the rest.
  # That's been true so far in my testing, but ¯\_(ツ)_/¯
  commit_info_path = path.joinpath('.git', 'objects', commit_id[:2], commit_id[2:])
  try:
    commit_info_raw = decompress(commit_info_path.read_bytes())
  except FileNotFoundError:
    packfile_id, offset_in_packfile = find_packfile_id_and_offset_for_commit(path, commit_id)
    commit_info_raw = extract_commit_info_from_packfile_as_offset(path, packfile_id, offset_in_packfile)
  # print('DEBUG - commit_info_raw is')
  # print(commit_info_raw)
  return parse_commit_info(commit_info_raw)

def parse_commit_info(commit_info):
  for line in commit_info.decode('utf-8').splitlines(): # This assumes decodable into utf-8, which...I think is true?
    if line.startswith('committer'):
      # Note - this ignores the Timezone. As above, in all my testing, timezone was always +0000 -
      # and, besides, we're only looking for a rough measure of "is this old?", so a few hours either way doesn't matter
      commit_date = datetime.fromtimestamp(int(line.split()[-2]))
  return CommitInfo(commit_date=commit_date)

def whoami():
  return pwd.getpwuid(os.getuid()).pw_name

def extract_commit_info_from_packfile_as_offset(repo_dir, packfile_id, offset):
  # TODO - this should probably be extracted!
  pack_path = repo_dir.joinpath('.git', 'objects', 'pack')
  pack_file_path = pack_path.joinpath(packfile_id + '.pack')
  if not pack_file_path:
    raise Exception(f'Could not find pack file path in {repo_dir}')

  with open(pack_file_path.absolute(), 'rb') as f:
    f.seek(offset)
    byte_as_bin = _hex_to_bin(f.read(1).hex())
    should_read_next_byte = byte_as_bin[0] == '1'
    obj_type = _get_obj_type(byte_as_bin[1:4])
    if obj_type != 'OBJ_COMMIT':
      raise Exception(f'Unhandlable object type: {obj_type}')

    accumulated_bin_string = byte_as_bin[4:]
    while should_read_next_byte:
      byte_as_bin = _hex_to_bin(f.read(1).hex())
      should_read_next_byte = byte_as_bin[0] == '1'
      accumulated_bin_string += byte_as_bin[1:]

    # object_length = int(accumulated_bin_string, 2)
    #
    # So, as it turns out, we don't actually _need_ the object length, because that only tells
    # us the size of the object when _de_-compressed. Rather, we rely on zlib's robustness,
    # since zlib streams start with a self-describing header that will tell it when to stop.
    #
    # But I kept it around as an instructional example :P
    #
    # TODO: might be more efficient to convert this to a stream, so that `f.read()` won't just
    # read the _whole_ file when we know we only want to consume a small section of it.
    return decompress(f.read())


def find_packfile_id_and_offset_for_commit(repo_dir, commit_sha):
  # https://codewords.recurse.com/issues/three/unpacking-git-packfiles
  
  pack_path = repo_dir.joinpath('.git', 'objects', 'pack')

  idx_path = [pc for pc in pack_path.iterdir() if pc.suffix == '.idx']
  if not idx_path:
    raise Exception(f'Could not find .idx file in {repo_dir}')

  # Particularly large repos might have multiple packfiles, and one index file per packfile
  idx_ids = [idx.stem for idx in idx_path]
  for idx_id in idx_ids: # TODO - extract the content of this for-loop to a method, to avoid the awkward breaks/continues

    idx_path = pack_path.joinpath(idx_id + '.idx')

    # Not read_bytes() because we can optimize (lol, as if that makes a difference!) by doing seeks
    with open(idx_path.absolute(), 'rb') as f:
      header = f.read(4)
      if header != b'\xfftOc':
        print('Header had unexpected format')

      # Not used, just a curiosity
      version_number = int(f.read(4).hex(), 16)

      # Moving into the fanout table, which starts with 256 4-byte entries.
      # First we seek to the fanout table entry that tells us how many objects _preced_ the given prefix...
      prefix_in_decimal = int(commit_sha[:2], 16)
      f.seek((prefix_in_decimal-1)*4, 1)
      num_preceding_objects = int(f.read(4).hex(), 16)
      # ...then, we infer how many objects there are _with_ the given prefix...
      num_prefix_objects = int(f.read(4).hex(), 16)-num_preceding_objects
      # ...and finally, seek to the end of this section to find out how many objects there are
      f.seek((255 - (prefix_in_decimal + 1))*4, 1)
      num_total_objects = int(f.read(4).hex(), 16)

      # Moving into the second layer of the fanout table, where 20-byte object names are
      # sequentially listed.
      # First we seek to the start of "the objects that begin with the same prefix as the target commit"...
      f.seek(num_preceding_objects*20, 1)
      # then, we pull object names one-by-one until we find the target one
      for i in range(num_prefix_objects):
        obj_name = f.read(20).hex()
        if obj_name == commit_sha:
          f.seek((num_total_objects-(num_preceding_objects+i+1))*20, 1)
          break
      else:
        # Did not find commit within expected number of objects - must be in another idx file
        continue # continues the `for idx_id in idx_ids` loop

      # Skip through the cyclic redundancy checks - assume Git has already done that for us
      f.seek(num_total_objects*4, 1)

      # Find the packfile offset for the object
      f.seek((num_preceding_objects + i)*4, 1)
      offset_as_bin_string = ''.join([_hex_to_bin(f.read(1).hex()) for _ in range(4)])
      if offset_as_bin_string[0] == '0':
        offset_as_dec = _bin_to_dec(offset_as_bin_string[1:])
        break # Break the `for idx_id in idx_ids`
      else:
        # Packfile size >= 2GB - value in layer 4 is the offset in layer 5 _in which_ to find the pack-offset
        offset_in_layer_5 = _bin_to_dec(offset_as_bin_string[1:])
        f.seek((num_total_objects - (num_preceding_objects + i + 1))*4, 1)
        f.seek(offset_in_layer_5*8, 1)
        offset_as_dec = int(f.read(8).hex(), 16)
        break # BReak the `for idx_id in idx_ids`
  else: # Have exhaused all the idx_ids and still not found the 
    raise Exception(f'Could not find info for {commit_sha} in any index file')

  return idx_id, offset_as_dec


def _hex_to_bin(h):
  return bin(int(h, 16)).lstrip('0b').rjust(8, '0')

def _bin_to_dec(b):
  return int(b, 2)

def _get_obj_type(bits):
  return {
    '001': 'OBJ_COMMIT',
    '010': 'OBJ_TREE',
    '011': 'OBJ_BLOB',
    '100': 'OBJ_TAG',
    # sic
    '110': 'OBJ_OFS_DELTA',
    '111': 'OBJ_REF_DELTA'
  }[bits]

if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('--workspace-path', default=f'/Users/{whoami()}/workplace')
  main(parser.parse_args())
