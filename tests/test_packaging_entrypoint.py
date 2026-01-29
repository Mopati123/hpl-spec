import io
import unittest
from contextlib import redirect_stdout

from hpl import __version__
from hpl import cli


class PackagingEntrypointTests(unittest.TestCase):
    def test_cli_version_flag(self):
        buffer = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, redirect_stdout(buffer):
            cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        output = buffer.getvalue().strip()
        self.assertIn(__version__, output)
