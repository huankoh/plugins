#!/usr/bin/env python3
"""Bootstrap a private Codex ChatGPT auth cache from one environment secret."""

import argparse
import json
import os
from pathlib import Path
import secrets
import stat
import sys


SECRET_ENV = 'HSTACK_CODEX_AUTH_JSON'


class BootstrapError(Exception):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BootstrapError('the secret contains duplicate JSON fields')
        result[key] = value
    return result


def reject_constant(value):
    raise BootstrapError('the secret is not valid JSON')


def validate_seed(raw):
    if not raw:
        raise BootstrapError('the ChatGPT auth secret is missing')
    try:
        auth = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (ValueError, RecursionError):
        raise BootstrapError('the secret is not valid JSON') from None
    if not isinstance(auth, dict) or auth.get('auth_mode') != 'chatgpt':
        raise BootstrapError('the secret must use ChatGPT authentication')
    for key, value in auth.items():
        if key.lower().replace('_', '').replace('-', '') in {'apikey', 'openaiapikey'} and value is not None:
            raise BootstrapError('API key authentication is not supported')
    tokens = auth.get('tokens')
    if not isinstance(tokens, dict) or any(
        not isinstance(tokens.get(key), str) or not tokens[key].strip()
        for key in ('id_token', 'access_token', 'refresh_token')
    ):
        raise BootstrapError('the secret must include nonempty ChatGPT ID, access, and refresh tokens')
    return (json.dumps(auth, ensure_ascii=True, separators=(',', ':')) + '\n').encode('utf-8')


def reject_repository(directory_fd):
    try:
        os.stat('.git', dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise BootstrapError('the auth cache must be outside a Git checkout')


def open_auth_home(value):
    path = Path(value).expanduser()
    if not path.is_absolute() or '..' in path.parts or len(path.parts) < 2:
        raise BootstrapError('the auth cache requires an absolute path without parent traversal')
    user_home = Path.home()
    if path == user_home or path in user_home.parents:
        raise BootstrapError('the auth cache requires a dedicated directory')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open(path.anchor, flags)
    try:
        reject_repository(directory_fd)
        for component in path.parts[1:]:
            try:
                os.mkdir(component, mode=0o700, dir_fd=directory_fd)
            except FileExistsError:
                pass
            child_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
            reject_repository(directory_fd)
        if os.fstat(directory_fd).st_uid != os.getuid():
            raise BootstrapError('the auth cache directory must belong to the current user')
        os.fchmod(directory_fd, 0o700)
        return directory_fd
    except BaseException:
        os.close(directory_fd)
        raise


def existing_cache(directory_fd):
    try:
        cache_fd = os.open('auth.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    except FileNotFoundError:
        return False
    try:
        info = os.fstat(cache_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise BootstrapError('the existing auth cache must be a regular file owned by the current user')
        os.fchmod(cache_fd, 0o600)
    finally:
        os.close(cache_fd)
    return True


def restore_auth(auth_home):
    directory_fd = open_auth_home(auth_home)
    try:
        if existing_cache(directory_fd):
            return 'existing auth cache preserved'
        payload = validate_seed(os.environ.get(SECRET_ENV))
        temporary_name = '.auth-seed-' + secrets.token_hex(16)
        temporary_fd = os.open(
            temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=directory_fd,
        )
        try:
            with os.fdopen(temporary_fd, 'wb') as output:
                os.fchmod(output.fileno(), 0o600)
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(
                    temporary_name, 'auth.json', src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd, follow_symlinks=False,
                )
            except FileExistsError:
                if not existing_cache(directory_fd):
                    raise BootstrapError('the auth cache changed during bootstrap; retry') from None
                return 'existing auth cache preserved'
            os.fsync(directory_fd)
            return 'auth cache restored'
        finally:
            os.unlink(temporary_name, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Bootstrap a private Codex ChatGPT auth cache from HSTACK_CODEX_AUTH_JSON.',
        epilog=(
            'Existing auth.json is preserved, including refreshed credentials. '
            'This is a bootstrap only. It does not persist token rotation across VMs or '
            'coordinate concurrent refreshes. There is no API key fallback.'
        ),
    )
    parser.add_argument(
        '--auth-home', default=str(Path.home() / '.local/share/hstack-codex-auth'),
        help='Dedicated absolute cache directory outside Git checkouts. Symlink paths are refused.',
    )
    args = parser.parse_args(argv)
    try:
        status = restore_auth(args.auth_home)
    except BootstrapError as error:
        print('Codex auth bootstrap failed. ' + str(error) + '.', file=sys.stderr)
        return 1
    except (OSError, ValueError, RecursionError):
        print('Codex auth bootstrap failed. The cache path could not be safely used.', file=sys.stderr)
        return 1
    print('Codex ' + status + '.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
