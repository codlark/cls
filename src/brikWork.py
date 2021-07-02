'''This file is the brikwork command line app.'''

import sys
import os
import argparse
from brikWorkEngine import *

#???? Do I need argparse for this app?
commandParser = argparse.ArgumentParser(description='brikwork command line app', add_help=True)
commandParser.add_argument('file', metavar='FILE')
# add a data override

args = commandParser.parse_args()
directory, filename = os.path.split(os.path.realpath(args.file))
os.chdir(directory)

if not os.path.isfile(filename):
    print(f'{filename} isn\'t a file')
    sys.exit(1)

with open(filename) as file:
    layoutText = file.read()
print(f'found {filename}')


app = QApplication()

try:
    layout = parseLayout(layoutText)
    painter = AssetPainter(layout)
    painter.paint()
    assetTotal = len(painter.images)
    painter.save()
except brikWorkError as e:
    print('an error occured while generating assets:')
    print(e.message)

print(f'generated {assetTotal} assets in {layout.output}')