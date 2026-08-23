from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .constants import TIME_FORMAT

REMINDERS_NOTE = 'GTD/Reminders.md'
LIVE_HEADER = '## Live'
SENT_HEADER = '## Sent'


@dataclass
class Reminder:
    """A live reminder, carrying the index of the line it was read from so that filing
    it away later can move that line itself."""
    line_index: int
    due: datetime
    text: str


def _reminders_path(vault_path: Path) -> Path:
    return vault_path.joinpath('GTD', 'Reminders.md')


def _header_index(lines: List[str], header: str) -> Optional[int]:
    for index, line in enumerate(lines):
        if line.strip() == header:
            return index
    return None


def _section_bounds(lines: List[str], header_index: int) -> Tuple[int, int]:
    """The half-open range of lines belonging to the section under `header_index`."""
    for index in range(header_index + 1, len(lines)):
        if lines[index].startswith('#'):
            return header_index + 1, index
    return header_index + 1, len(lines)


def reminders_due(vault_path: Path, today: datetime) -> Tuple[List[Reminder], List[str]]:
    """Live reminders dated on or before `today`, plus a description of every line that
    could not be read.

    Unreadable lines are reported rather than raised on, and are left where they are: a
    reminder that cannot be delivered has to survive to be retried, and one typo should
    cost a warning in the day's note rather than the whole day's setup.
    """
    path = _reminders_path(vault_path)
    if not path.exists():
        return [], []
    lines = path.read_text().splitlines()

    if _header_index(lines, LIVE_HEADER) is None:
        return [], [f'No "{LIVE_HEADER}" header found in {REMINDERS_NOTE}']
    if _header_index(lines, SENT_HEADER) is None:
        # Nothing may be sent that cannot then be filed, or it would send again every day
        return [], [f'No "{SENT_HEADER}" header found in {REMINDERS_NOTE}, '
                    f'so no reminder can be filed once it has been sent']

    due = []
    problems = []
    start, end = _section_bounds(lines, _header_index(lines, LIVE_HEADER))
    for index in range(start, end):
        entry = lines[index].strip()
        if not entry.startswith(('- ', '* ')):
            continue
        # Split from the left only twice, so the text itself may contain " - "
        fields = entry[2:].split(' - ', 2)
        if len(fields) < 3:
            problems.append(f'Expected "<reminder date> - <capture date> - <text>" '
                            f'but found "{entry}"')
            continue
        reminder_date, _, text = (field.strip() for field in fields)
        try:
            when = datetime.strptime(reminder_date, TIME_FORMAT)
        except ValueError:
            problems.append(f'Unparseable reminder date "{reminder_date}" in "{entry}"')
            continue
        if when.date() <= today.date():
            due.append(Reminder(index, when, text))
    return due, problems


def section_for_todo_note(reminders: List[Reminder]) -> str:
    if not reminders:
        return ''
    return ('**Reminders**\n'
            + '\n'.join(f'- [ ] {reminder.text}' for reminder in reminders)
            + '\n---\n')


def banner_for_problems(problems: List[str]) -> str:
    """A callout for the top of the day's TODO note. Reminders are only worth having if
    a failure to deliver one is impossible to miss."""
    if not problems:
        return ''
    return ('> [!error] Reminders could not be read\n'
            + '\n'.join(f'> - {problem}' for problem in problems)
            + f'\n> These lines are still live in {REMINDERS_NOTE}, '
              f'and will be retried on the next run.\n')


def move_to_sent(vault_path: Path, reminders: List[Reminder], today: datetime):
    """Moves each reminder from the Live section to the end of the Sent one, stamped
    with the day it was sent.

    Lines are moved verbatim rather than re-rendered from `reminders`, so the note's
    hand-written prose, its commentary, and each line's own bullet marker all survive.
    """
    if not reminders:
        return
    path = _reminders_path(vault_path)
    contents = path.read_text()
    lines = contents.splitlines()

    _, end_of_sent = _section_bounds(lines, _header_index(lines, SENT_HEADER))
    moved = {reminder.line_index for reminder in reminders}
    filed = [f'{lines[index]} | sent: {today.strftime(TIME_FORMAT)}' for index in sorted(moved)]

    # A single pass over the original snapshot, rather than a sequence of deletions, so
    # that every recorded index still addresses the line it was read from however many
    # reminders come due together
    rewritten = []
    for index, line in enumerate(lines):
        if index == end_of_sent:
            rewritten.extend(filed)
        if index not in moved:
            rewritten.append(line)
    if end_of_sent >= len(lines):
        rewritten.extend(filed)

    path.write_text('\n'.join(rewritten) + ('\n' if contents.endswith('\n') else ''))
