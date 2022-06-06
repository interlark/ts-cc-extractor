# TS-CC Extractor
[![Tests](https://github.com/interlark/ts-cc-extractor/actions/workflows/tests.yml/badge.svg)](https://github.com/interlark/ts-cc-extractor/actions/workflows/tests.yml)
[![PyPi version](https://badgen.net/pypi/v/ts-cc-extractor)](https://pypi.org/project/ts-cc-extractor)
[![Supported Python versions](https://badgen.net/pypi/python/ts-cc-extractor)](https://pypi.org/project/ts-cc-extractor)
[![PyPi license](https://badgen.net/pypi/license/ts-cc-extractor)](https://pypi.org/project/ts-cc-extractor)

With this pure-python utility you can extract __EIA-608 captions__ from __Video Transport Stream__ _(*.ts)_ file
and convert them to __SubRip__ _(*.srt)_ or __Video Text Tracks__ _(*.vtt)_ subtitles.


## Installation

```
pip install ts-cc-extractor
```


## Usage

```
usage: ts-cc-extractor -i PATH -o PATH [-f {SRT,VTT}] [-v] [-h]

required arguments:
  -i PATH        Path to *.ts file
  -o PATH        Output subtitles file

optional arguments:
  -f {SRT,VTT}   Subtitles format (default: SRT)
  -v, --version  show program's version number and exit
  -h, --help     show this help message and exit
```


## API example

```python

from ts_cc_extractor import extract_subtitles

with open('video1.ts') as f:
    subs_text = extract_subtitles(f, fmt='VTT')
    print(subs_text)
```
```
WEBVTT

00:01.705 --> 00:03.974 align:left position:10% line:5% size:80%
THAT'S JUST THE WAY IT GOES.
I DONE SEEN IT TOO MANY TIMES.

00:03.974 --> 00:05.609 align:left position:30% line:89% size:60%
HEY, Y'ALL READY?

...
```

## CLI example

```
$ ts-cc-extractor -i video2.ts -o subs.srt -f SRT
$ cat subs.srt
```
```
1
00:00:01,967 --> 00:00:05,633                       
>> HARRY AND MEGHAN WERE IN THE
MAJOR GENERAL'S OFFICE

2
00:00:05,633 --> 00:00:10,533       
OVERLOOKING THE PAGEANTLY OF THE
HORSE GUARDS PARADE AND THE

3
00:00:10,533 --> 00:00:10,800  
TROOPING.

...
```


## License

BSD