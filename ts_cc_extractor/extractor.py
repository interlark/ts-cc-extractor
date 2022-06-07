from __future__ import annotations

import io
import logging
import sys
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from pycaption import CaptionReadError, SCCReader, SRTWriter, WebVTTWriter

from .media_tools.ts import handle_file

if TYPE_CHECKING:
    from typing import IO, Any, Callable, Generator, Optional

    if sys.version_info >= (3, 8):
        from typing import TypedDict  # noqa: FE261
    else:
        from typing_extensions import TypedDict

    SCCFile = TypedDict('SCCFile', {'content': str, 'channel': int, 'type': Optional[str]})


logger = logging.getLogger(__name__)


def set_options(options: dict[str, Any]) -> dict[str, Any]:
    default_options = {
        'video': False,  # If video data should be logged
        'audio': False,  # If audio data should be logged
        'text': False,  # If text data should be logged
        'verbose': 0,  # Verbose level
        'log_cc': False,  # CC logging
        'show_progress': True,  # Show progress in stderr
    }

    return {**default_options, **options}


@contextmanager
def show_progress(mininterval: float = 0.1) -> Generator[Callable[[int, int, bool], None], None, None]:
    show_time = time.time()

    def _show_progress(current: int, total: int, is_final: bool = False):
        nonlocal show_time
        current_time = time.time()
        if current_time - show_time > mininterval or is_final:
            show_time = current_time
            percent = current / total * 100
            print('Progress: %d%%' % percent, end='\n' if is_final else '\r', file=sys.stderr)
    try:
        yield _show_progress
    finally:
        _show_progress(1, 1, is_final=True)


def extract_scc(ts_file: bytes | IO[bytes], **options) -> list[SCCFile]:
    """Extracts CEA-608 `SCC` (Scenarist Closed Captions) from `TS`.

    Returns:
        List of files:
        [
            {
                'name': 'EMBEDDED' | 'SCTE' | 'ATSC',
                'channel': 0 | 1,
                'content': ...,
            },
        ]
    """
    cc_files: list[SCCFile] = []
    options = set_options(options)

    if isinstance(ts_file, bytes):
        ts_file = io.BytesIO(ts_file)

    if options['show_progress']:
        with show_progress() as progress_callback:
            handle_file(ts_file, progress_callback, cc_files, **options)
    else:
        handle_file(ts_file, cc_files=cc_files, **options)

    return cc_files


def extract_subtitles(ts_file: bytes | IO[bytes], fmt: str = 'SRT', **options) -> str | None:
    """Extract subtitles out of TS file.

    Args:
        ts_file: TS file
        format: Subtitles format: 'SRT' or 'VTT'
    """
    scc_files = extract_scc(ts_file, **options)
    if not scc_files:
        logger.error('No EIA captions found!')
        return None

    # TODO extract all files?
    for scc_file in scc_files:
        try:
            scc_captions = SCCReader().read(content=scc_file['content'])
            break
        except CaptionReadError:
            scc_captions = None

    if not scc_captions:
        logger.error('SCC caption read failed!')
        return None

    if fmt.upper() == 'SRT':
        return SRTWriter().write(scc_captions)

    return WebVTTWriter().write(scc_captions)
