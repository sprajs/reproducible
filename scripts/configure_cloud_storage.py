#!/usr/bin/env python3
"""Install scoped cloud secrets as an AWS profile without displaying their values."""
import configparser
import os
from pathlib import Path
import re


def configure(environ, home):
    key = environ.get('RESEARCH_AWS_ACCESS_KEY_ID', '')
    secret = environ.get('RESEARCH_AWS_SECRET_ACCESS_KEY', '')
    if not re.fullmatch(r'AKIA[A-Z0-9]{16}', key) or not re.fullmatch(r'[A-Za-z0-9/+=]{40}', secret):
        raise ValueError('Set both RESEARCH_AWS_ACCESS_KEY_ID and RESEARCH_AWS_SECRET_ACCESS_KEY as cloud secrets')
    folder = home / '.aws'
    if folder.is_symlink():
        raise ValueError('AWS configuration directory must not be a symlink')
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    folder.chmod(0o700)
    for name, section, values in [
        ('credentials', 'research', {'aws_access_key_id': key, 'aws_secret_access_key': secret}),
        ('config', 'profile research', {'region': 'eu-west-2', 'output': 'json'}),
    ]:
        path = folder / name
        if path.is_symlink():
            raise ValueError('AWS configuration files must not be symlinks')
        config = configparser.RawConfigParser()
        config.read(path)
        # Preserve other profiles, replace this dedicated research profile only.
        config[section] = values
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            config.write(stream)
        path.chmod(0o600)
    print('Configured restricted research AWS profile; secret values were not printed.')


if __name__ == '__main__':
    try:
        configure(os.environ, Path.home())
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
