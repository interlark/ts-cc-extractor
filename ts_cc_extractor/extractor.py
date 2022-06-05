from __future__ import annotations

import io
import logging
import sys
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pysrt
import pyvtt

from .media_tools.cea608towebvtt import WebVTTWriter
from .media_tools.scc import SccParser
from .media_tools.ts import handle_file

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import IO, Any, Generator, Callable, TypedDict, Optional

    ResultFile = TypedDict('ResultFile', {'content': str, 'channel': int, 'type': Optional[str]})


def set_options(options: dict[str, Any]) -> dict[str, Any]:
    default_options = {
        'video': False,  # If video data should be logged
        'audio': False,  # If audio data should be logged
        'text': False,  # If text data should be logged
        'verbose': 0,  # Verbose level
        'log_cc': False,  # CC logging
        'show_progress': True,  # Show progress in stderr'
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


def extract_scc(ts_file: bytes | IO[bytes], **options) -> list[ResultFile]:
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

    Note:
        ATSC - CEA-708
    """
    cc_files: list[ResultFile] = []
    options = set_options(options)

    if isinstance(ts_file, bytes):
        ts_file = io.BytesIO(ts_file)

    if options['show_progress']:
        with show_progress() as progress_callback:
            handle_file(ts_file, progress_callback, cc_files, **options)
    else:
        handle_file(ts_file, cc_files=cc_files, **options)

    return cc_files


def convert_scc_vtt(scc_file: str | IO[str],
                    split_lines: bool = False) -> list[ResultFile]:
    """Convert `SCC` to `VTT` subtitles:

    Args:
        scc_file: CEA-608 SCC file

    Returns:
        List of files:
        [
            {
                'channel': 0 | 1,
                'content': ...,
            },
        ]
    """
    if isinstance(scc_file, str):
        scc_file = io.StringIO(scc_file)

    vtt_ch0 = WebVTTWriter(combineConsecutiveRows=(not split_lines), channel=1)
    vtt_ch1 = WebVTTWriter(combineConsecutiveRows=(not split_lines), channel=2)
    SccParser(scc_file, vtt_ch0, vtt_ch1)

    vtt_files: list[ResultFile] = \
        [y for y in [x.get_vtt() for x in (vtt_ch0, vtt_ch1)] if y]

    return vtt_files


def extract_subtitles(ts_file: bytes | IO[bytes], fmt: str = 'SRT',
                      split_lines: bool = False,
                      merge_similar: bool = True,
                      **options) -> str | None:
    """Extract subtitles out of TS file.

    Args:
        ts_file: TS file
        format: 'SRT' or 'VTT'
    """
    if merge_similar and split_lines:
        merge_similar = False

    scc_files = extract_scc(ts_file, **options)
    if not scc_files:
        logger.error('No EIA captions found!')
        return None

    scc_file = scc_files[0]  # TODO extract all files?

    vtt_files = convert_scc_vtt(scc_file['content'], split_lines)
    if not vtt_files:
        logger.error('Failed to convert SCC captions!')
        return None

    vtt_file = vtt_files[0]  # TODO convert all files?

    subs = pyvtt.from_string(vtt_file['content'])

    for cue in subs:
        cue.text = cue.text.strip()

    if merge_similar:
        max_ms_between_cues = 250
        empty_cues = []
        for cue_idx, cue in enumerate(subs):
            if cue_idx < len(subs) - 1:
                next_cue = subs[cue_idx + 1]
                if next_cue.start - cue.end <= max_ms_between_cues \
                        and next_cue.text.startswith(cue.text):
                    next_cue.start = cue.start
                    empty_cues.append(cue_idx)

        for cue_idx in reversed(empty_cues):
            del subs[cue_idx]

    if fmt.upper() == 'SRT':
        srt_cues = []
        for cue_idx, cue in enumerate(subs, 1):
            srt_cues.append(
                pysrt.SubRipItem(
                    index=cue_idx, start=cue.start, end=cue.end, text=cue.text
                )
            )
        subs = pysrt.SubRipFile(items=srt_cues)

    with io.StringIO() as f:
        subs.write_into(f)
        return f.getvalue()
