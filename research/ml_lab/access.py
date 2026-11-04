"""Process-local evidence boundaries, not a security boundary against repository authors."""
from contextlib import contextmanager
import os
from pathlib import Path
import sys

from .artifacts import ROOT

_denied: tuple[Path, ...] = ()
_active = False


def _audit(event, args):
    if not _active:
        return
    if event == 'socket.connect':
        raise PermissionError('ML experiments are offline')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        forbidden = tuple(ROOT/'data'/name for name in ('raw','processed','external','prepared')) + _denied
        if any(path == p or path.is_relative_to(p) for p in forbidden):
            raise PermissionError(f'ML experiment access denied: {path.name}')


sys.addaudithook(_audit)


@contextmanager
def isolated(*denied: Path):
    global _active, _denied
    previous = _active, _denied
    _active, _denied = True, tuple(dict.fromkeys(_denied + tuple(p.resolve() for p in denied)))
    try:
        yield
    finally:
        _active, _denied = previous
