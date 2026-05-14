import os
import sys

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if getattr(sys, "frozen", False):
    _here = os.path.dirname(sys.executable)
else:
    _here = os.path.dirname(os.path.abspath(__file__))

_cookies = os.path.join(_here, "cookies.txt")

args = sys.argv[1:]
if "--cookies-path" not in " ".join(args):
    args = ["--cookies-path", _cookies] + args
if "--no-config-file" not in args:
    args = ["--no-config-file"] + args

sys.argv = [sys.argv[0]] + args

from gamdl.cli.cli import main
main(standalone_mode=True)
