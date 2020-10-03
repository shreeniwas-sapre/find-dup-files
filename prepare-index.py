#!/usr/bin/env python
import os
import sys
import argparse
import yaml
import subprocess
import hashlib
import tqdm

is_os_win = os.name == 'nt'
is_os_linux = os.name == 'posix'

console_name = 'con' if is_os_win else '/dev/tty' if is_os_linux else None
file_tty = open(console_name, 'w') if console_name is not None else sys.stdout


def file_hash_external(fname):
    # Setup command
    oldcwd = None
    if is_os_win:
        oldcwd = os.getcwd()
        cmd = ['certutil', '-hashfile', os.path.basename(fname)]
        cwd = os.path.dirname(fname)
        os.chdir(cwd)
    elif is_os_linux:
        cmd = ['md5sum', fname]
    else:
        raise RuntimeError("should not be here")

    # Execute command
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    outs, errs = p.communicate()
    if p.returncode != 0:
        raise RuntimeError('Failed command %s\n%s' % (cmd, errs))

    # Extract output
    if is_os_win:
        os.chdir(oldcwd)
        outlines = [x.strip() for x in outs.split(b'\n')]
        return outlines[1].decode('ascii')
    elif is_os_linux:
        return outs.split(b'\n')[0].split(b' ')[0]
    else:
        raise RuntimeError("should not be here")


def file_hash_internal(fname):
    h = hashlib.md5()
    with open(fname, 'rb') as fin:
        h.update(fin.read())
    dig = h.hexdigest()
    return dig


def findfiles(dirs, ext, verbose):
    def _findfiles(_dir_name, _ext, _verbose, entries):
        dir_entries = []
        try:
            with os.scandir(_dir_name) as it:
                for entry in it:
                    if entry.name == '.' or entry.name == '..':
                        continue
                    file_path = os.path.join(_dir_name, entry.name).replace(os.sep, '/')
                    if entry.is_dir():
                        if _verbose:
                            print(f'{len(entries):6d}', end='\r', file=file_tty, flush=True)
                        dir_entries.append(file_path)
                        continue
                    if entry.is_file():
                        if _ext is not None:
                            if not file_path.endswith('.' + _ext):
                                continue
                        entries.append({
                            'path': file_path,
                            'size': entry.stat().st_size,
                            }
                        )
                        continue
                    raise Exception('unknown file kind', file_path)
        except PermissionError:
            print('error: permission denied to', _dir_name)
        for dir_name in sorted(dir_entries):
            _findfiles(dir_name, _ext, verbose, entries)

    allfiles = []
    for target_dir in dirs:
        _findfiles(target_dir, ext, verbose, allfiles)
    return allfiles


def write_index(indexfile, content):
    with open(indexfile + '_tmp', 'w') as fout:
        yaml.dump(content, fout, indent=4, Dumper=yaml.CDumper)
    os.replace(indexfile+'_tmp', indexfile)


def update_index(indexfile, initial_content=None):
    if initial_content is None:
        with open(indexfile) as fin:
            content = yaml.load(fin, Loader=yaml.CLoader)
    else:
        content = initial_content
    total_size = sum([row['size'] for row in content])
    files_with_same_size = dict()
    for row in content:
        try:
            files_with_same_size[row['size']] += 1
        except KeyError:
            files_with_same_size[row['size']] = 1
    num_files_skipped = 0
    num_files_hashed = 0

    with tqdm.tqdm(range(total_size), desc='Reading file info:') as pbar:
        for file_entry in sorted(content, key=lambda x: -x['size']):
            # TODO: (Document recipe to allow long paths)
            # if len(file_entry) > 256:
            #     print('WARNING', count, len(file_entry), file_entry)
            if files_with_same_size[file_entry['size']] == 1:
                num_files_skipped += 1
                continue
            num_files_hashed += 1
            if 'hash' not in file_entry or file_entry['hash'] is None:
                try:
                    file_entry['hash'] = file_hash_internal(file_entry['path'])
                except RuntimeError:
                    try:
                        file_entry['hash'] = file_hash_external(file_entry['path'])
                    except RuntimeError as e2:
                        print(e2, file_entry)
                        continue
            pbar.update(file_entry['size'])
    print(f'{num_files_skipped} files skipped (only 1 file with that size), {num_files_hashed} files hashed')
    return content


def prepare_main(args):
    target_dirs = [args.dir]
    output = args.index if args.index is not None else 'file-hashes.yaml'
    allfiles = findfiles(target_dirs, args.ext, args.verbose)
    with open(output, 'w') as fout:
        yaml.dump(allfiles, fout, indent=4, Dumper=yaml.CDumper)
    content = update_index(output, allfiles)
    write_index(output, content)


def update_main(args):
    content = update_index(args.index, None)
    write_index(args.index, content)


def read_index(indexfile):
    with open(indexfile) as fin:
        return yaml.load(fin, Loader=yaml.CLoader)


def clear_main(args):
    content = read_index(args.index)
    for row in content:
        if 'hash' in row:
            del row['hash']
    write_index(args.index, content)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='prepare index subcommands')
    prepare_subparser = subparsers.add_parser('prepare', help='prepare index')
    prepare_subparser.add_argument('--dir',     '-d', default='.',         metavar='Directory', help='directory')
    prepare_subparser.add_argument('--ext',     '-e', default=None,        metavar='Opt-Extension', help='extension without "."')
    prepare_subparser.add_argument('--index',   '-i', default='index.yaml', metavar='Index-yaml',        help='output YAML')
    prepare_subparser.add_argument('--verbose', '-v', action='store_true', help='verbose run')
    prepare_subparser.set_defaults(func=prepare_main)

    update_subparser = subparsers.add_parser('update', help='update index with hashes')
    update_subparser.add_argument('--index',   '-i', default='index.yaml',        metavar='Index-yaml', help='output YAML')
    update_subparser.set_defaults(func=update_main)

    clear_subparser = subparsers.add_parser('clear', help='clear index of hashes')
    clear_subparser.add_argument('--index',   '-i', default='index.yaml',        metavar='Index-yaml', help='output YAML')
    clear_subparser.set_defaults(func=clear_main)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == '__main__':
    exit(main())
