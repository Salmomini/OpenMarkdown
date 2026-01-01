import sys
from typing import Iterable, Dict, List, Set


_PENDING_PREFIX = "\u2192"
_DONE_PREFIX = "\u2713"
_DIM = "\033[2m"
_RESET = "\033[0m"
_steps: List[str] = []
_step_index: Dict[str, int] = {}
_shown = False
_completed: Set[str] = set()


def set_steps(steps: Iterable[str]) -> None:
    global _steps, _step_index, _shown, _completed
    _steps = list(steps)
    _step_index = {message: idx for idx, message in enumerate(_steps)}
    _shown = False
    _completed = set()


def _show_pending() -> None:
    global _shown
    if _shown or not _steps:
        return
    for message in _steps:
        sys.stdout.write(f"{_PENDING_PREFIX} {message}\n")
    sys.stdout.flush()
    _shown = True


def _mark_done(message: str) -> None:
    idx = _step_index[message]
    total = len(_steps)
    lines_up = total - idx
    sys.stdout.write(f"\033[{lines_up}A\r")
    sys.stdout.write(f"{_DIM}{_DONE_PREFIX} {message}{_RESET}\033[K\n")
    if lines_up > 1:
        sys.stdout.write(f"\033[{lines_up - 1}B")
    sys.stdout.flush()


def log_step(message: str) -> None:
    _show_pending()
    if message not in _step_index:
        sys.stdout.write(f"{_PENDING_PREFIX} {message}\n")
        sys.stdout.flush()
        return
    if message in _completed:
        return
    _mark_done(message)
    _completed.add(message)
