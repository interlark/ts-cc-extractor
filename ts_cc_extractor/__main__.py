import argparse

from . import __version__, extract_subtitles


def main():
    parser = argparse.ArgumentParser('ts-cc-extractor', add_help=False)
    required_group = parser.add_argument_group('required arguments')
    optional_group = parser.add_argument_group('optional arguments')
    required_group.add_argument('-i', dest='ts_path', metavar='PATH', required=True,
                                help='Path to *.ts file')
    required_group.add_argument('-o', dest='out_path', metavar='PATH', required=True,
                                help='Output subtitles file')
    optional_group.add_argument('-f', dest='format', choices=['SRT', 'VTT'], default='SRT',
                                help='Subtitles format (default: %(default)s)')
    optional_group.add_argument('-v', '--version', action='version',
                                version=f'%(prog)s {__version__}')
    optional_group.add_argument('-h', '--help', action='help',
                                help='show this help message and exit')

    args = parser.parse_args()

    with open(args.ts_path, 'rb') as f_ts:
        subs_text = extract_subtitles(f_ts, fmt=args.format)

        if subs_text is not None:
            if args.out_path == '-':
                print(subs_text)
            else:
                with open(args.out_path, 'w') as f_out:
                    print(subs_text, file=f_out)
