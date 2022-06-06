import pathlib
import re

from setuptools import find_packages, setup


ROOT_DIR = pathlib.Path(__file__).parent
VERSION_PATH = ROOT_DIR / 'ts_cc_extractor' / '__init__.py'
README_PATH = ROOT_DIR / 'README.md'

long_description = README_PATH.read_text(encoding='utf-8')
long_description_content_type = 'text/markdown'

match = re.search(r'^__version__\s*=\s*[\'"](?P<version>.+?)[\'"]',
                  VERSION_PATH.read_text(encoding='utf-8'), re.M)
assert match
version = match.group('version')


if __name__ == '__main__':
    setup(
        name='ts-cc-extractor',
        version=version,
        description=('Extract EIA-608 captions from Video Transport Stream (*.ts) file'
                     'and convert them to SubRip (*.srt) or Video Text Tracks (*.vtt) subtitles'),
        long_description=long_description,
        long_description_content_type=long_description_content_type,
        author='Andy Trofimov',
        author_email='interlark@gmail.com',
        packages=find_packages(),
        python_requires='>=3.7',
        keywords='ts extract convert eia-608 srt vtt subtitles captions',
        url='https://github.com/interlark/ts-cc-extractor',
        install_requires=[
            'pycaption>=2.0.9',
        ],
        extras_require={
            'dev': [
                'wheel>=0.36.2,<0.38',
                'tox>=3.5,<4',
                'pytest>=6.2,<8',
                'typing-extensions>=4.0.0;python_version<"3.8"',
            ],
        },
        classifiers=[
            'Topic :: Internet',
            'Topic :: Utilities',
            'Topic :: Multimedia :: Video',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'License :: OSI Approved :: MIT License',
        ],
        license='MIT',
        entry_points={'console_scripts': ['ts-cc-extractor = ts_cc_extractor.__main__:main']},
    )
