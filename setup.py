from distutils.core import setup
import py2exe, sys

sys.argv.append('py2exe')

setup(
    windows=[{"script": "ui.py", "dest_base": "HeistRandomizer"}],
    options={"py2exe": {'bundle_files': 1, 'compressed': False}},
)
