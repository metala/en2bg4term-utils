#!/usr/bin/env python3

import argparse
import re
import sys
from difflib import ndiff
from itertools import count
from string import ascii_uppercase

non_empty_line_re = re.compile(r'.+\n')
empty_line_re = re.compile(r'\s*\n')
word_extractor_re = re.compile(r'(\(?(an|a|to|on)\)?\s+)?(.+?)')
nonalphahyphen_re = re.compile(r'[^a-z-]')
ws_re = re.compile(r'\s+')
sections = ['1-9'] + list(ascii_uppercase)


def read_file_lines(filename):
    with open(filename) as f:
        return f.readlines()


def write_file_lines(filename, lines):
    with open(filename, 'w') as f:
        return f.writelines(lines)


def find_table_body(lines, start):
    table_start = next(n for n in count(start)
                       if non_empty_line_re.fullmatch(lines[n]))
    try:
        table_end = next(n for n in count(table_start)
                         if empty_line_re.fullmatch(lines[n]))
    except IndexError:
        table_end = len(lines)

    return (table_start, table_end)


def list_section_tables(lines):
    start = 0
    for section in sections:
        try:
            start = lines.index(f'### {section}\n', start)
        except ValueError:
            print(f'> Missing section "### {section}"', file=sys.stderr)
            continue

        t_start, tb_end = find_table_body(lines, start + 1)
        tb_start = t_start + 2
        yield (section, tb_start, tb_end)


def table_row_first_cell(row):
    phrase = row.split('|')[0].strip()
    m = word_extractor_re.fullmatch(phrase)
    if m is None:
        return ''

    key = m.group(3)
    key = key.replace(' ', '-')
    key = ws_re.sub('-', key)
    key = nonalphahyphen_re.sub('', key)
    return key


def main():
    parser = argparse.ArgumentParser(description='Sorts and verifies en2bg4term tables')
    parser.add_argument('filename', default='readme.md', help='The filename to process.')
    parser.add_argument('--fix', action='store_true',
                        help='Fix and save file.')

    args = parser.parse_args()
    lines = read_file_lines(args.filename)

    is_sorted = True
    for s, start, end in list_section_tables(lines):
        section_lines = lines[start:end]
        sorted_lines = sorted(section_lines, key=table_row_first_cell)
        if section_lines == sorted_lines:
            continue
        if args.fix:
            lines[start:end] = sorted_lines
            continue

        is_sorted = False
        print(f'> Section "### {s}" is not alphabetically ordered. '
              'Showing diff:', file=sys.stderr)
        print(''.join(ndiff(section_lines, sorted_lines)))

    if args.fix:
        write_file_lines(args.filename, lines)
        print('The document has been sorted successfully.')
    if not is_sorted:
        print('> The document is not properly sorted.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
