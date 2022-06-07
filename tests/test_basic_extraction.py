import pathlib

import pytest
from pycaption import SRTReader, WebVTTReader
from pycaption.base import BaseReader
from ts_cc_extractor import extract_subtitles


SAMPLE_DIR = pathlib.Path(__file__).parent / 'sample'
VIDEO_SAMPLE = SAMPLE_DIR / 'sample.ts'

testdata = [
    ['SRT', SAMPLE_DIR / 'sample.srt', SRTReader],
    ['VTT', SAMPLE_DIR / 'sample.vtt', WebVTTReader],
]


def check_subtitles(subs_content: str, sample_file: pathlib.Path, reader: BaseReader):
    with sample_file.open(encoding='utf-8') as f_subs:
        sample_subs = reader().read(f_subs.read(), lang='en')
        test_subs = reader().read(subs_content, lang='en')
        sample_captions = sample_subs.get_captions(lang='en')
        test_captions = test_subs.get_captions(lang='en')

        assert len(sample_captions) == len(test_captions)
        for cue_test, cue_sample in zip(test_captions, sample_captions):
            assert cue_test.start == cue_sample.start
            assert cue_test.end == cue_sample.end
            assert cue_test.style == cue_sample.style
            assert len(cue_test.nodes) == len(cue_sample.nodes)
            for node_test, node_sample in zip(cue_test.nodes, cue_sample.nodes):
                assert node_test.type_ == node_sample.type_
                assert node_test.content == node_sample.content
                assert node_test.layout_info == node_sample.layout_info


@pytest.mark.parametrize('fmt, sample_file, reader', testdata)
def test_basic_extraction(fmt, sample_file, reader):
    with open(VIDEO_SAMPLE, 'rb') as f:
        subs_content = extract_subtitles(f, fmt=fmt)
        check_subtitles(subs_content, sample_file, reader)
