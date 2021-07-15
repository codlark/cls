'''brikWork command line setup script

'''

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

])

setup(
    name='brikWork',
    version='0.2',
    description='brikWork command line app',
    options = dict(build_exe=build_options),
    executables=[Executable("brikWork.py", icon="../logo.ico")]
    )