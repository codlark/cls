'''This file is the brikwork command line app.'''

import sys
import os
import argparse
from brikWorkEngine import *

#???? Do I need argparse for this app?
commandParser = argparse.ArgumentParser(description='brikwork command line app', add_help=True)
commandParser.add_argument('file', metavar='FILE')
commandParser.add_argument('-e', '--early-exit', action='store_true', dest='early', help="don't prompt for input after generation")
# add a data override

args = commandParser.parse_args()
directory, filename = os.path.split(os.path.realpath(args.file))
os.chdir(directory)

def openFile(filename):

    if not os.path.isfile(filename):
        raise bWError("filename '{filename}' is not a file",
        origin='command line', filename=filename)
    try:
        with open(filename, encoding='utf-8') as file:
            layoutText = file.read()
        print(f'found {filename}')
    except OSError:
        raise bWError("Could not open layout '{filename}'",
        origin='command line', filename=filename)
    return layoutText

app = QApplication()

try:
    layoutText = openFile(filename)
    layout = buildLayout(layoutText, filename)
    painter = AssetPainter(layout)
    painter.paint()
    assetTotal = len(painter.images)
    painter.save()
    print(f'generated {assetTotal} assets in {layout.output}')
except bWError as e:
    print('an error occured while generating assets:')
    print(e.message)

if not args.early:
    x = input('press enter to exit ')