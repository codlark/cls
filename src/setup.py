'''cls command line setup script
note: to build, run `python setup.py build`
'''

import sys
from cx_Freeze import setup, Executable

build_options = dict(excludes=[
    'tkinter',
    'unittest',
    'email',
    'http',
    'xml',
    'pydoc',
    'pdb',

], include_files=[
    ('res/logo.ico', 'res/logo.ico')
], silent=True
)

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name='CLS Renderer',
    version='1.3',
    description='Renderer for Card Layout Script',
    author='Gia Bamrud',
    author_email='codlark@gmail.com',
    options = dict(build_exe=build_options),
    executables=[Executable("main.py", icon="res/logo.ico", base=base, target_name="CLS Renderer")]
    )