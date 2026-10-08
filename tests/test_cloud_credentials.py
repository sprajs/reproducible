import configparser
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from configure_cloud_storage import configure


class CloudCredentialsTests(unittest.TestCase):
    def test_missing_secrets_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                configure({}, Path(tmp))
            self.assertFalse((Path(tmp) / '.aws').exists())

    def test_scoped_profile_preserves_other_profiles_and_never_prints_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.aws').mkdir()
            credentials = root / '.aws' / 'credentials'
            credentials.write_text('[other]\ncustom = preserved\n')
            secrets = {'RESEARCH_AWS_ACCESS_KEY_ID':'AKIA' + 'X' * 16,
                       'RESEARCH_AWS_SECRET_ACCESS_KEY':'x' * 40}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                configure(secrets, root)
            parser = configparser.RawConfigParser()
            parser.read(credentials)
            self.assertEqual(parser['other']['custom'], 'preserved')
            self.assertEqual(parser['research']['aws_access_key_id'], secrets['RESEARCH_AWS_ACCESS_KEY_ID'])
            for value in secrets.values():
                self.assertNotIn(value, output.getvalue())
            self.assertEqual(credentials.stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / '.aws').stat().st_mode & 0o777, 0o700)

    def test_symlink_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.aws').symlink_to(root)
            with self.assertRaises(ValueError):
                configure({'RESEARCH_AWS_ACCESS_KEY_ID':'AKIA'+'X'*16,
                           'RESEARCH_AWS_SECRET_ACCESS_KEY':'x'*40}, root)


if __name__ == '__main__':
    unittest.main()
