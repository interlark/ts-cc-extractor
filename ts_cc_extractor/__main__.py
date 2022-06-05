import argparse

from . import __version__, extract_subtitles


def main():
    parser = argparse.ArgumentParser('ts-cc-extractor')
    parser.add_argument('-i', dest='ts_path', metavar='PATH', required=True,
                        help='Path to *.ts file')
    parser.add_argument('-o', dest='out_path', metavar='PATH', required=True,
                        help='Output subtitles file')
    parser.add_argument('-f', dest='format', choices=['SRT', 'VTT'], default='SRT',
                        help='Subtitles format (default: %(default)s)')
    parser.add_argument('--no-merge', action='store_true',
                        help='Do not merge similar cues')
    parser.add_argument('--split-lines', action='store_true',
                        help='Split subtitles by lines')
    parser.add_argument('-v', '--version', action='version',
                        version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    with open(args.ts_path, 'rb') as f_ts:
        subs_text = extract_subtitles(f_ts, split_lines=args.split_lines,
                                      merge_similar=not args.no_merge, format=args.format)

        if subs_text is not None:
            if args.out_path == '-':
                print(subs_text)
            else:
                with open(args.out_path, 'w') as f_out:
                    print(subs_text, file=f_out)
