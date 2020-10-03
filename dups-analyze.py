#!/usr/bin/env python
import os
import sys
import argparse
import yaml


def read_index(indexfile):
    with open(indexfile) as fin:
        return yaml.load(fin, Loader=yaml.CLoader)


def trim_index(content):
    oldlen = len(content)
    content = [row for row in content if os.path.exists(row['path'])]
    newlen = len(content)
    if newlen != oldlen:
        print(f'{oldlen-newlen}/{oldlen} files no more available, skipped')
    return content


def add_to_map(pairmap, path1, path2, size):
    dir1 = os.path.dirname(path1)
    dir2 = os.path.dirname(path2)
    if dir1 < dir2:
        ktuple = (dir1, dir2)
    else:
        ktuple = (dir2, dir1)
    if ktuple not in pairmap:
        pairmap[ktuple] = {'totalsize': 0, 'files': []}
    pairmap[ktuple]['totalsize'] += size
    pairmap[ktuple]['files'].append([size, path1, path2])


def analyze(content, header_lines, verbose=False):
    hash_map = dict()
    for row in content:
        if 'hash' not in row:
            continue
        if row['hash'] not in hash_map:
            print(len(hash_map), row['hash'], end='\r', flush=True, file=sys.stderr)
            hash_map[row['hash']] = {'hash': row['hash'], 'filesize': row['size'], 'paths': []}
        hash_map[row['hash']]['paths'].append(row['path'])

    for kt in hash_map:
        hash_map[kt]['totalsize'] = hash_map[kt]['filesize'] * len(hash_map[kt]['paths'])

    directory_pair_map = dict()

    for kt in sorted(hash_map, key=lambda y: -hash_map[y]['totalsize']):
        if len(hash_map[kt]['paths']) == 1:
            continue
        # print(f'Hash: {kt}, #paths {len(hash_map[kt]["paths"])}, total size {hash_map[kt]["totalsize"]}')
        paths = hash_map[kt]['paths']
        for pi in range(len(paths)):
            for qi in range(pi+1, len(paths)):
                add_to_map(directory_pair_map, paths[pi], paths[qi], hash_map[kt]['filesize'])
    count = 0
    for x in sorted(directory_pair_map, key=lambda y: -directory_pair_map[y]['totalsize']):
        if header_lines is not None and count > header_lines:
            break
        dpmentry = directory_pair_map[x]
        print(f'\t{count:6d}: "{x}" total size of matching files: ', dpmentry['totalsize'], ', #matching files: ', len(dpmentry['files']))
        if verbose:
            sr = 0
            for pathpair in dpmentry['files']:
                print('\t'.join([str(x) for x in [sr] + pathpair]))
            print('==========================================')
        count += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true', help='provide details of matching files')
    parser.add_argument('--head', metavar='number-of-directory-pairs', type=int,
                        help='number of pairs to print (all pairs printed by default)')
    parser.add_argument('--index', '-i', metavar='Index-yaml', default='index.yaml', help='index yaml file')
    args = parser.parse_args()

    os.system('time /t 1>&2')
    content = read_index(args.index)
    content = trim_index(content)
    os.system('time /t 1>&2')
    analyze(content, args.head, args.verbose)
    os.system('time /t 1>&2')


if __name__ == '__main__':
    exit(main())
