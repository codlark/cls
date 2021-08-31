'''brikWork command line setup script

'''

import sys
from cx_Freeze import executable, setup, Executable

build_options = dict(excludes=[
    'tkinter',
    'unittest',
    'email',
    'http',
    'xml',
    'pydoc',
    'pdb',

#], includes=[

], include_files=[
    ('res/logo.ico', 'res/logo.ico')
],

)

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name='brikWork',
    version='0.5',
    description='brikWork app',
    options = dict(build_exe=build_options),
    executables=[Executable("brikWork.py", icon="../logo.ico", base=base)]
    )